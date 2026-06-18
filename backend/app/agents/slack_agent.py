"""Slack agent: the final node - always runs, reports success or halt."""

from __future__ import annotations

from pydantic import BaseModel

from app.agents.common import log_event, run_specialist, select_tools
from app.config import settings
from app.mcp_client import tools_session
from app.state import AriaState

JSON_REPLY_INSTRUCTION = """

Once you've posted (or attempted to post) the message, your FINAL reply must \
be ONLY a single JSON object, no other text, in exactly this shape:
{"status": "success" or "failed", "error": "<explanation if failed, else null>"}"""

SUCCESS_PROMPT = (
    """You are the Slack agent for ARIA, the last step in the \
pipeline. Use the available Slack tools to post a message to the given channel \
confirming that a requirement was fully captured: the BRD is in Notion, the \
technical documentation PR is open on GitHub, and the backlog issue is in Jira. \
Include the links provided. Report whether the message was sent."""
    + JSON_REPLY_INSTRUCTION
)

FAILURE_PROMPT = (
    """You are the Slack agent for ARIA, the last step in the \
pipeline. A requirement failed partway through the pipeline. Use the available \
Slack tools to post a message to the given channel stating clearly that this \
requirement was NOT captured, naming which step failed and why, and that the \
overall flow was halted as a result. Report whether the message was sent."""
    + JSON_REPLY_INSTRUCTION
)


class SlackResult(BaseModel):
    status: str  # "success" | "failed"
    error: str | None = None


async def slack_agent_node(state: AriaState) -> dict:
    if state["overall_status"] == "success":
        task = (
            f"Channel ID: {settings.slack_channel_id}\n"
            f"Requirement title: {state['requirement_title']}\n"
            f"Notion BRD: {state['notion_page_url']}\n"
            f"GitHub tech doc PR: {state['github_doc_url']}\n"
            f"Jira issue: {state['jira_issue_key']} ({state['jira_issue_url']})\n"
            "Post the success confirmation now."
        )
        system_prompt = SUCCESS_PROMPT
    else:
        task = (
            f"Channel ID: {settings.slack_channel_id}\n"
            f"Requirement title: {state['requirement_title']}\n"
            f"Halt reason: {state['halt_reason']}\n"
            "Post the failure notification now."
        )
        system_prompt = FAILURE_PROMPT

    try:
        async with tools_session("slack") as all_tools:
            tools = select_tools(all_tools, ["slack_post_message"])
            result: SlackResult = await run_specialist(
                system_prompt=system_prompt,
                task=task,
                tools=tools,
                response_schema=SlackResult,
                structured_output=False,
            )
    except Exception as exc:
        return {
            "slack_status": "failed",
            "agent_log": log_event("slack", "failed", f"Slack agent crashed: {exc}"),
        }

    if result.status != "success":
        return {
            "slack_status": "failed",
            "agent_log": log_event(
                "slack", "failed", result.error or "Failed to post Slack message"
            ),
        }

    return {
        "slack_status": "success",
        "agent_log": log_event("slack", "success", "Notification sent to Slack"),
    }
