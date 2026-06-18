"""Notion agent: drafts a BRD and publishes it as a Notion page.

The official Notion MCP server wraps Notion's raw REST API 1:1 (auto-generated
from its OpenAPI spec), so the agent must produce exact nested block JSON, not
Markdown. A worked example in the system prompt anchors the expected shape.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.agents.common import log_event, run_specialist, select_tools
from app.config import settings
from app.mcp_client import tools_session
from app.state import AriaState

SYSTEM_PROMPT = """You are the Notion agent for ARIA. Given a structured product \
requirement, write a clear Business Requirements Document and publish it as a \
new Notion page using the `API-post-page` tool.

Call API-post-page with exactly this shape:
{
  "parent": {"page_id": "<the parent page ID given to you>"},
  "properties": {"title": {"title": [{"text": {"content": "<requirement title>"}}]}},
  "children": [
    {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"text": {"content": "Overview"}}]}},
    {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": "<a paragraph>"}}]}},
    {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [{"text": {"content": "<a bullet>"}}]}}
  ]
}

Build a full "children" array covering Overview, Description, Acceptance \
Criteria (as bulleted_list_item blocks, one per criterion), and Priority - \
following the block shapes above exactly. `parent` must never be null or \
omitted.

Once the page is created (or creation fails), your FINAL reply must be ONLY a \
single JSON object, no other text, in exactly this shape:
{"status": "success" or "failed", "page_url": "<created page URL or null>", \
"brd_content": "<the BRD as plain Markdown text, for the GitHub agent to reuse>", \
"error": "<explanation if failed, else null>"}"""


class NotionResult(BaseModel):
    status: str  # "success" | "failed"
    page_url: str | None = None
    brd_content: str = ""
    error: str | None = None


async def notion_agent_node(state: AriaState) -> dict:
    task = (
        f"Parent Notion page ID: {settings.notion_parent_page_id}\n"
        f"Requirement title: {state['requirement_title']}\n"
        f"Description: {state['requirement_description']}\n"
        f"Acceptance criteria: {state['acceptance_criteria']}\n"
        f"Priority: {state['priority']}\n"
        "Write the BRD and create the Notion page now."
    )
    try:
        async with tools_session("notion") as all_tools:
            tools = select_tools(all_tools, ["API-post-page"])
            result: NotionResult = await run_specialist(
                system_prompt=SYSTEM_PROMPT,
                task=task,
                tools=tools,
                response_schema=NotionResult,
                structured_output=False,
            )
    except Exception as exc:
        return {
            "notion_status": "failed",
            "notion_error": str(exc),
            "agent_log": log_event("notion", "failed", f"Notion agent crashed: {exc}"),
        }

    if result.status != "success" or not result.page_url:
        error = result.error or "Unknown Notion failure"
        return {
            "notion_status": "failed",
            "notion_error": error,
            "agent_log": log_event("notion", "failed", error),
        }

    return {
        "notion_status": "success",
        "notion_page_url": result.page_url,
        "brd_content": result.brd_content,
        "agent_log": log_event(
            "notion", "success", f"BRD published to Notion: {result.page_url}"
        ),
    }
