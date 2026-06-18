"""Shared LangGraph state threaded through every ARIA agent node."""

from __future__ import annotations

import operator
from typing import Annotated, Literal, TypedDict

AgentStatus = Literal["pending", "running", "success", "failed"]


class AgentEvent(TypedDict):
    agent: str
    status: AgentStatus
    message: str
    timestamp: str


class AriaState(TypedDict):
    # Captured by the orchestrator
    raw_requirement: str
    orchestrator_status: AgentStatus
    orchestrator_error: str | None
    requirement_title: str
    requirement_description: str
    acceptance_criteria: list[str]
    priority: str

    # Notion agent
    brd_content: str
    notion_status: AgentStatus
    notion_page_url: str | None
    notion_error: str | None

    # GitHub agent
    github_status: AgentStatus
    github_doc_url: str | None
    github_error: str | None

    # Jira agent
    jira_status: AgentStatus
    jira_issue_key: str | None
    jira_issue_url: str | None
    jira_error: str | None

    # Slack agent / overall outcome
    overall_status: Literal["success", "failed"]
    halt_reason: str | None
    slack_status: AgentStatus

    # Append-only log of status transitions, streamed to the UI.
    # github_agent and jira_agent run in parallel and both append here, so this
    # needs a concatenating reducer instead of last-write-wins overwrite semantics.
    agent_log: Annotated[list[AgentEvent], operator.add]


def initial_state(raw_requirement: str) -> AriaState:
    return AriaState(
        raw_requirement=raw_requirement,
        orchestrator_status="pending",
        orchestrator_error=None,
        requirement_title="",
        requirement_description="",
        acceptance_criteria=[],
        priority="medium",
        brd_content="",
        notion_status="pending",
        notion_page_url=None,
        notion_error=None,
        github_status="pending",
        github_doc_url=None,
        github_error=None,
        jira_status="pending",
        jira_issue_key=None,
        jira_issue_url=None,
        jira_error=None,
        overall_status="success",
        halt_reason=None,
        slack_status="pending",
        agent_log=[],
    )
