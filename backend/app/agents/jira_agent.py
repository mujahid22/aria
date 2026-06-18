"""Jira agent: creates a backlog item from the captured requirement."""

from __future__ import annotations

from pydantic import BaseModel

from app.agents.common import log_event, run_specialist, select_tools
from app.config import settings
from app.mcp_client import tools_session
from app.state import AriaState

SYSTEM_PROMPT = """You are the Jira agent for ARIA. Given a structured product \
requirement, use the jira_create_issue tool to create a new backlog issue in \
the given project. Always pass issue_type="Task" exactly - do not use "Story", \
since this project's workflow does not have a Story issue type and the call \
will be rejected. Put the description and acceptance criteria in the issue \
description, and map priority via additional_fields (e.g. \
{"priority": {"name": "High"}}).

Once the issue is created (or creation fails), your FINAL reply must be ONLY a \
single JSON object, no other text, in exactly this shape:
{"status": "success" or "failed", "issue_key": "<created issue key or null>", \
"issue_url": "<created issue URL or null>", "error": "<explanation if failed, else null>"}"""


class JiraResult(BaseModel):
    status: str  # "success" | "failed"
    issue_key: str | None = None
    issue_url: str | None = None
    error: str | None = None


async def jira_agent_node(state: AriaState) -> dict:
    task = (
        f"Jira project key: {settings.jira_project_key}\n"
        f"Requirement title: {state['requirement_title']}\n"
        f"Description: {state['requirement_description']}\n"
        f"Acceptance criteria: {state['acceptance_criteria']}\n"
        f"Priority: {state['priority']}\n"
        "Create the backlog issue now."
    )
    try:
        async with tools_session("jira") as all_tools:
            tools = select_tools(all_tools, ["jira_create_issue"])
            result: JiraResult = await run_specialist(
                system_prompt=SYSTEM_PROMPT,
                task=task,
                tools=tools,
                response_schema=JiraResult,
                structured_output=False,
            )
    except Exception as exc:
        return {
            "jira_status": "failed",
            "jira_error": str(exc),
            "agent_log": log_event("jira", "failed", f"Jira agent crashed: {exc}"),
        }

    if result.status != "success" or not result.issue_key:
        error = result.error or "Unknown Jira failure"
        return {
            "jira_status": "failed",
            "jira_error": error,
            "agent_log": log_event("jira", "failed", error),
        }

    return {
        "jira_status": "success",
        "jira_issue_key": result.issue_key,
        "jira_issue_url": result.issue_url,
        "agent_log": log_event(
            "jira", "success", f"Backlog issue created: {result.issue_key}"
        ),
    }
