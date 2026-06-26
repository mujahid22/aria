"""Orchestrator: turns a raw, free-text requirement into a structured spec."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.agents.common import call_with_retry, get_llm, log_event
from app.state import AriaState

SYSTEM_PROMPT = """You are the orchestration agent for ARIA, a system that turns a \
product manager's free-text requirement into a structured spec for downstream \
agents (Notion BRD writer, GitHub tech-doc writer, Jira backlog creator). \
Extract a concise title, a clear description, a short list of testable acceptance \
criteria, and a priority level. Do not invent scope the user didn't ask for."""


class RequirementExtraction(BaseModel):
    title: str = Field(description="Short, specific requirement title (under 80 chars)")
    description: str = Field(description="1-3 sentence description of the requirement")
    acceptance_criteria: list[str] = Field(description="3-6 testable acceptance criteria")
    priority: Literal["low", "medium", "high", "critical"]


SPLIT_SYSTEM_PROMPT = """You are the orchestration agent for ARIA. The input you \
receive may be a single product requirement, or it may be raw notes from a \
meeting or discussion that bundles together several separate, independent \
requirements or feature requests (e.g. a numbered list, bullet points, or a \
few sentences each describing a different ask).

Identify every distinct, independent requirement or feature request in the \
input. For each one, write a short self-contained snippet of text that fully \
captures that one requirement on its own - a downstream agent will read only \
that snippet, with no other context. Do not split a single requirement into \
multiple pieces, and do not invent requirements that aren't actually there. \
If the input only describes one requirement, return exactly one item \
containing that requirement."""


class SplitResult(BaseModel):
    requirements: list[str] = Field(
        description=(
            "Each distinct, independent requirement found in the input, as a "
            "self-contained snippet. Exactly one item if the input only "
            "describes a single requirement."
        )
    )


async def split_requirements(raw_text: str, *, config: dict | None = None) -> list[str]:
    """Detect and separate distinct requirements bundled in free text (e.g.
    meeting notes listing several asks at once). Runs once per submission,
    before the per-requirement pipeline. Any failure here just falls back to
    treating the whole input as one requirement, so a flaky split call never
    loses the user's input."""
    llm = get_llm(temperature=0.1).with_structured_output(SplitResult)
    try:
        result: SplitResult = await call_with_retry(
            lambda: llm.ainvoke(
                [
                    ("system", SPLIT_SYSTEM_PROMPT),
                    ("user", raw_text),
                ],
                config=config,
            ),
            # 3 attempts at 14s (worst case ~54s incl. rate-limit backoff)
            # stays under the 60s split budget in main.py while giving real
            # retry headroom under sustained quota pressure - eval runs
            # surfaced this falling back to "treat as one requirement" under
            # contention from concurrent production + eval traffic sharing
            # the same Mistral quota, exhausting the old attempts=2 budget.
            attempts=3,
            timeout=14.0,
        )
    except Exception:
        return [raw_text]

    cleaned = [r.strip() for r in result.requirements if r and r.strip()]
    return cleaned or [raw_text]


async def orchestrator_node(state: AriaState) -> dict:
    llm = get_llm(temperature=0.1).with_structured_output(RequirementExtraction)
    try:
        extraction: RequirementExtraction = await call_with_retry(
            lambda: llm.ainvoke(
                [
                    ("system", SYSTEM_PROMPT),
                    ("user", state["raw_requirement"]),
                ]
            ),
            # See split_requirements above for why attempts=3/timeout=14.0 -
            # same rate-limit-exhaustion finding from the golden-dataset eval,
            # still within the node's 60s deadline (graph.py) with margin.
            attempts=3,
            timeout=14.0,
        )
    except Exception as exc:
        return {
            "orchestrator_status": "failed",
            "orchestrator_error": str(exc),
            "agent_log": log_event("orchestrator", "failed", f"Orchestrator failed: {exc}"),
        }

    return {
        "orchestrator_status": "success",
        "requirement_title": extraction.title,
        "requirement_description": extraction.description,
        "acceptance_criteria": extraction.acceptance_criteria,
        "priority": extraction.priority,
        "agent_log": log_event(
            "orchestrator", "success", f"Captured requirement: {extraction.title}"
        ),
    }
