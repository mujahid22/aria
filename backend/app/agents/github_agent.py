"""GitHub agent: converts the BRD into technical documentation and pushes it."""

from __future__ import annotations

import re
import uuid

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from app.agents.common import call_with_retry, extract_json_object, get_github_llm, log_event, select_tools
from app.config import settings
from app.mcp_client import tools_session
from app.state import AriaState

SYSTEM_PROMPT = """You are the GitHub agent for ARIA. Given a finished BRD, convert \
it into a technical documentation Markdown file (add an "## Implementation Notes" \
section with open technical questions, but keep the original requirement intent \
intact).

Then call the GitHub tools in EXACTLY this order, passing ONLY the parameters \
listed below for each call - do not add any other parameter (not "draft", not \
"maintainer_can_modify", not anything else not listed here), even if the tool's \
schema offers it as optional. Every parameter you DO pass must be exactly the \
type shown - never wrap a boolean in quotes:

1. create_branch(owner=<owner>, repo=<repo>, branch=<branch_name>)
2. create_or_update_file(owner=<owner>, repo=<repo>, branch=<branch_name>, \
path=<file_path>, content=<the markdown doc>, message=<a short commit message>)
3. create_pull_request(owner=<owner>, repo=<repo>, head=<branch_name>, \
base=<default_branch>, title=<a short PR title>, body=<a short PR description>)

`head` in step 3 MUST be exactly the same string as <branch_name> used in step 1 \
- never leave it blank. If a call fails because of an unexpected parameter type \
or an extra parameter you added, retry that SAME call with ONLY the parameters \
listed above for that step, omitting whatever you added. If create_branch \
reports the branch already exists, treat step 1 as already done and continue \
to step 2 - do not treat that as a failure."""

# Forgiving about a trailing quote/brace/paren so we don't swallow JSON syntax
# that follows the URL in the raw tool result text.
_PR_URL_RE = re.compile(r"https://github\.com/[^\s\"'}\]]+/pull/\d+")

MAX_STEPS = 6


def _slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or "requirement"


class GithubResult(BaseModel):
    status: str  # "success" | "failed"
    doc_url: str | None = None
    error: str | None = None


def _fallback_tool_calls(content: str) -> list[dict] | None:
    """NVIDIA NIM occasionally writes a tool call as plain-text JSON in the
    message content instead of using the structured tool_calls field (e.g.
    {"type": "function", "name": "create_or_update_file", "parameters": {...}}
    or the OpenAI-style {"name": ..., "arguments": {...}}). Recognize that and
    convert it into a real tool call instead of treating it as a give-up."""
    parsed = extract_json_object(content)
    if parsed is None:
        return None
    name = parsed.get("name")
    args = parsed.get("parameters") or parsed.get("arguments")
    if not name or not isinstance(args, dict):
        return None
    return [{"name": name, "args": args, "id": f"fallback-{uuid.uuid4().hex[:8]}"}]


async def _run_until_pr_opened(
    *, system_prompt: str, task: str, tools: list[BaseTool]
) -> GithubResult:
    """Drive the tool-calling loop by hand instead of via create_react_agent's
    generic loop, so we can stop the instant create_pull_request succeeds.

    create_react_agent always makes one extra LLM call after the last tool
    result to produce a final text answer - but by the time create_pull_request
    succeeds, its own JSON result already contains the PR URL, so that summary
    call is pure overhead. Skipping it cuts this agent's round trips from 4 to 3."""
    model = get_github_llm().bind_tools(tools, parallel_tool_calls=False)
    tools_by_name = {t.name: t for t in tools}
    messages: list[BaseMessage] = [SystemMessage(content=system_prompt), HumanMessage(content=task)]

    for _ in range(MAX_STEPS):
        ai_message: AIMessage = await call_with_retry(lambda: model.ainvoke(messages))
        messages.append(ai_message)
        tool_calls = ai_message.tool_calls or _fallback_tool_calls(ai_message.content) or []
        if not tool_calls:
            return GithubResult(
                status="failed", error=f"Agent stopped without opening a PR: {ai_message.content}"
            )

        for tool_call in tool_calls:
            tool = tools_by_name.get(tool_call["name"])
            tool_result_text = (
                str(await tool.ainvoke(tool_call["args"]))
                if tool is not None
                else f"Unknown tool: {tool_call['name']}"
            )
            messages.append(ToolMessage(content=tool_result_text, tool_call_id=tool_call["id"]))

            if tool_call["name"] == "create_pull_request":
                match = _PR_URL_RE.search(tool_result_text)
                if match:
                    return GithubResult(status="success", doc_url=match.group(0))
                # No URL found (e.g. a validation error) - let the loop continue
                # so the model can see the error and retry.

    return GithubResult(status="failed", error=f"Exceeded {MAX_STEPS} steps without opening a PR")


async def github_agent_node(state: AriaState) -> dict:
    slug = _slugify(state["requirement_title"])
    # Suffixed to avoid colliding with a branch from a prior run on the same title.
    branch_name = f"feature/tech-doc-{slug}-{uuid.uuid4().hex[:6]}"
    file_path = f"docs/tech/{slug}.md"
    task = (
        f"owner: {settings.github_owner}\n"
        f"repo: {settings.github_repo}\n"
        f"default_branch: main\n"
        f"branch_name: {branch_name}\n"
        f"file_path: {file_path}\n"
        f"Requirement title: {state['requirement_title']}\n"
        f"BRD content:\n{state['brd_content']}\n"
        "Convert this into a technical doc and push it following the exact steps "
        "in your instructions, using the owner/repo/default_branch/branch_name/"
        "file_path values given above verbatim."
    )
    try:
        async with tools_session("github") as all_tools:
            tools = select_tools(
                all_tools, ["create_branch", "create_or_update_file", "create_pull_request"]
            )
            result = await _run_until_pr_opened(system_prompt=SYSTEM_PROMPT, task=task, tools=tools)
    except Exception as exc:
        return {
            "github_status": "failed",
            "github_error": str(exc),
            "agent_log": log_event("github", "failed", f"GitHub agent crashed: {exc}"),
        }

    if result.status != "success" or not result.doc_url:
        error = result.error or "Unknown GitHub failure"
        return {
            "github_status": "failed",
            "github_error": error,
            "agent_log": log_event("github", "failed", error),
        }

    return {
        "github_status": "success",
        "github_doc_url": result.doc_url,
        "agent_log": log_event(
            "github", "success", f"Tech doc PR opened: {result.doc_url}"
        ),
    }
