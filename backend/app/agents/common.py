"""Shared helpers for building tool-calling specialist agents."""

from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime, timezone
from typing import Awaitable, Callable, TypeVar

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_mistralai import ChatMistralAI
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel

from app.config import settings
from app.state import AgentEvent, AgentStatus, AriaState

T = TypeVar("T", bound=BaseModel)
R = TypeVar("R")

# Ceiling per node (one deadline for the whole node, not per internal call) so a
# hung LLM/API call can never block the pipeline indefinitely - worst case across
# the critical path (orchestrator -> notion -> slowest of github/jira -> slack)
# is bounded to 4 * NODE_TIMEOUT_SECONDS.
NODE_TIMEOUT_SECONDS = 15

NodeFn = Callable[[AriaState], Awaitable[dict]]


def with_node_deadline(
    node_fn: NodeFn,
    *,
    agent: str,
    status_key: str,
    error_key: str | None = None,
    seconds: int = NODE_TIMEOUT_SECONDS,
) -> NodeFn:
    """Wrap a node so it always produces a terminal status within `seconds`,
    instead of letting a hung call (or an unhandled exception) silently stall
    the whole graph with no event ever reaching the UI."""

    async def wrapped(state: AriaState) -> dict:
        try:
            return await asyncio.wait_for(node_fn(state), timeout=seconds)
        except asyncio.TimeoutError:
            message = f"Timed out after {seconds}s"
            update: dict = {
                status_key: "failed",
                "agent_log": log_event(agent, "failed", f"{agent} {message.lower()}"),
            }
            if error_key:
                update[error_key] = message
            return update
        except Exception as exc:  # last-resort safety net for any bug in node_fn
            update = {
                status_key: "failed",
                "agent_log": log_event(agent, "failed", f"{agent} crashed: {exc}"),
            }
            if error_key:
                update[error_key] = str(exc)
            return update

    return wrapped


# Mistral's free tier rate-limits requests per second, not just concurrency:
# github and jira run in parallel and together make ~6 sequential model calls,
# so plain mutual exclusion (a semaphore with no gap) still let calls fire back
# to back fast enough to get HTTP 429s. Enforcing a minimum gap between any two
# call *starts*, process-wide, keeps every Mistral request under that rate.
_MISTRAL_LOCK = asyncio.Lock()
_MISTRAL_MIN_INTERVAL_SECONDS = 2.5
_mistral_last_call_at = 0.0


def get_llm(temperature: float = 0.2) -> ChatMistralAI:
    llm = ChatMistralAI(
        model=settings.mistral_model,
        api_key=settings.mistral_api_key,
        temperature=temperature,
    )
    original_agenerate = llm._agenerate

    async def throttled_agenerate(*args, **kwargs):
        global _mistral_last_call_at
        # Held for the whole call (not just until it starts) so two calls can
        # never overlap in flight, with a minimum gap enforced afterwards too.
        async with _MISTRAL_LOCK:
            now = asyncio.get_event_loop().time()
            wait = _MISTRAL_MIN_INTERVAL_SECONDS - (now - _mistral_last_call_at)
            if wait > 0:
                await asyncio.sleep(wait)
            result = await original_agenerate(*args, **kwargs)
            _mistral_last_call_at = asyncio.get_event_loop().time()
            return result

    llm._agenerate = throttled_agenerate
    return llm


def get_github_llm(temperature: float = 0.2) -> ChatNVIDIA:
    """The GitHub agent uses a separate provider (NVIDIA NIM) so its 3-step
    flow draws from its own rate-limit pool instead of competing with the
    other agents' shared Mistral quota."""
    return ChatNVIDIA(
        model=settings.nvidia_model,
        api_key=settings.nvidia_api_key,
        temperature=temperature,
    )


async def call_with_retry(
    fn: Callable[[], Awaitable[R]],
    *,
    attempts: int = 5,
    base_delay: float = 4.0,
    timeout: float | None = None,
) -> R:
    """Retry on any failure - both confirmed rate-limit errors (e.g. github+jira's
    parallel fan-out hitting Mistral's free-tier limit at the same moment) and
    other transient one-offs (e.g. an MCP stdio subprocess hiccup) - since both
    have shown up in practice and a retry reliably clears them. Rate-limit
    errors get a longer exponential backoff; anything else gets a short fixed
    delay, since it isn't waiting out a quota window.

    timeout bounds each individual attempt. Without it, a call that hangs
    instead of raising (observed with the GitHub agent's NVIDIA calls) never
    gives this function a chance to retry - it just sits there until the
    node's outer deadline eventually kills the whole node. A per-attempt
    timeout turns that hang into the same retryable failure as any other."""
    for attempt in range(attempts):
        try:
            return await (asyncio.wait_for(fn(), timeout=timeout) if timeout else fn())
        except Exception as exc:
            if attempt == attempts - 1:
                raise
            is_rate_limited = "429" in str(exc) or "rate_limit" in str(exc).lower()
            await asyncio.sleep(base_delay * (2**attempt) if is_rate_limited else 2.0)
    raise RuntimeError("unreachable")


def select_tools(tools: list[BaseTool], names: list[str]) -> list[BaseTool]:
    """Narrow an MCP server's full tool list to just what one agent needs.

    An MCP server's full tool list (e.g. 43 GitHub tools, 49 Jira tools) adds a
    lot of irrelevant schema to the prompt and burns through token-per-minute
    quotas, even though any single agent here only ever calls 1-3 of them."""
    by_name = {t.name: t for t in tools}
    selected = [by_name[n] for n in names if n in by_name]
    missing = [n for n in names if n not in by_name]
    if missing:
        raise RuntimeError(f"Tool(s) not found on MCP server: {missing}")
    return selected


def log_event(agent: str, status: AgentStatus, message: str) -> list[AgentEvent]:
    """Build a single-element log list - the agent_log reducer concatenates these."""
    return [
        AgentEvent(
            agent=agent,
            status=status,
            message=message,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    ]


async def run_specialist(
    *,
    system_prompt: str,
    task: str,
    tools: list[BaseTool],
    response_schema: type[T],
    structured_output: bool = True,
    parallel_tool_calls: bool = True,
    llm: BaseChatModel | None = None,
) -> T:
    """Run a ReAct tool-calling agent and coerce its final answer into response_schema.

    structured_output=False skips LangGraph's extra structured-extraction call
    (which appends a fresh request on top of the finished message history) and
    instead parses a JSON object out of the agent's own final text reply -
    Mistral's API rejects that extra call's message ordering, so its agents
    must be told (in their system prompt) to answer with a raw JSON object.

    parallel_tool_calls=False forces one tool call at a time - needed whenever
    later calls depend on an earlier call's result (e.g. GitHub's branch must
    exist before a file commit or PR can target it); otherwise the model fires
    all calls in the same turn and the dependent ones fail."""
    model = llm or get_llm()
    if not parallel_tool_calls:
        model = model.bind_tools(tools, parallel_tool_calls=False)
    agent = create_react_agent(
        model,
        tools,
        prompt=system_prompt,
        response_format=response_schema if structured_output else None,
    )
    result = await call_with_retry(lambda: agent.ainvoke({"messages": [("user", task)]}))
    if structured_output:
        return result["structured_response"]
    final_text = result["messages"][-1].content
    parsed = extract_json_object(final_text)
    if parsed is None:
        raise RuntimeError(f"No JSON object found in final answer: {final_text!r}")
    return response_schema(**parsed)


def extract_json_object(text: str) -> dict | None:
    """Find and parse the first {...} JSON object in free-form model text.

    Models occasionally emit a literal backslash inside a string value (e.g. a
    path, or an escaped apostrophe like \\') that isn't a valid JSON escape -
    repair that and retry once before giving up."""
    if not isinstance(text, str):
        return None
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    raw_json = match.group(0)
    try:
        return json.loads(raw_json)
    except json.JSONDecodeError:
        repaired = re.sub(r'\\(?!["\\/bfnrtu])', r"\\\\", raw_json)
        try:
            return json.loads(repaired)
        except json.JSONDecodeError:
            return None
