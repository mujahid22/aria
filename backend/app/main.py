"""FastAPI surface for ARIA: submit a requirement, watch the agent pipeline live."""

from __future__ import annotations

import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.agents.orchestrator import split_requirements
from app.config import settings
from app.graph import aria_graph
from app.state import initial_state

app = FastAPI(title="ARIA")

allow_origins = ["http://localhost:3000", "http://localhost:3001"]
if settings.frontend_origin:
    allow_origins.append(settings.frontend_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Generous margin over observed split-call latency - any failure or timeout
# here just falls back to treating the whole submission as one requirement,
# so a flaky split call never loses the user's input.
SPLIT_TIMEOUT_SECONDS = 60


class RequirementRequest(BaseModel):
    requirement: str


async def _split_with_fallback(raw_requirement: str) -> list[str]:
    try:
        return await asyncio.wait_for(
            split_requirements(raw_requirement), timeout=SPLIT_TIMEOUT_SECONDS
        )
    except Exception:
        return [raw_requirement]


@app.post("/api/requirements")
async def submit_requirement(body: RequirementRequest) -> dict:
    """Non-streaming run - useful for smoke-testing the graph directly."""
    snippets = await _split_with_fallback(body.requirement)
    final_states = [await aria_graph.ainvoke(initial_state(snippet)) for snippet in snippets]
    return {"requirements": final_states}


@app.websocket("/ws/run")
async def run_requirement_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        raw_requirement = data["requirement"]

        snippets = await _split_with_fallback(raw_requirement)
        await websocket.send_json({"node": "_split", "update": {"count": len(snippets)}})

        for index, snippet in enumerate(snippets):
            await websocket.send_json(
                {
                    "node": "_requirement_start",
                    "update": {"index": index, "count": len(snippets), "raw_requirement": snippet},
                }
            )
            try:
                async for chunk in aria_graph.astream(initial_state(snippet), stream_mode="updates"):
                    for node_name, update in chunk.items():
                        await websocket.send_json(
                            {
                                "node": node_name,
                                "update": update,
                                "requirement_index": index,
                                "requirement_count": len(snippets),
                            }
                        )
            except Exception as exc:
                # Every node already has its own deadline/error handling, so this
                # is a last-resort net for this one requirement - it doesn't stop
                # the rest of the batch from being processed.
                await websocket.send_json(
                    {
                        "node": "_requirement_error",
                        "update": {"message": str(exc)},
                        "requirement_index": index,
                        "requirement_count": len(snippets),
                    }
                )

        await websocket.send_json({"node": "_done", "update": {}})
    except WebSocketDisconnect:
        pass
    finally:
        try:
            await websocket.close()
        except RuntimeError:
            pass
