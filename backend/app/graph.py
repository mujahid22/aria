"""LangGraph wiring: Orchestrator -> Notion -> (GitHub || Jira) -> Join -> Slack.

Failure handling is a routing decision, not an exception: a failed Notion step
skips the parallel stage entirely, and the join node downgrades overall_status to
"failed" if either parallel agent failed, which the Slack node turns into a halt
notification instead of a success confirmation.
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agents.github_agent import github_agent_node
from app.agents.jira_agent import jira_agent_node
from app.agents.notion_agent import notion_agent_node
from app.agents.orchestrator import orchestrator_node
from app.agents.slack_agent import slack_agent_node
from app.agents.common import log_event, with_node_deadline
from app.state import AriaState


def join_node(state: AriaState) -> dict:
    failed_agents = [
        name
        for name, status in (
            ("orchestrator", state["orchestrator_status"]),
            ("notion", state["notion_status"]),
            ("github", state["github_status"]),
            ("jira", state["jira_status"]),
        )
        if status == "failed"
    ]
    if failed_agents:
        halt_reason = f"Halted - failed step(s): {', '.join(failed_agents)}."
        return {
            "overall_status": "failed",
            "halt_reason": halt_reason,
            "agent_log": log_event("join", "failed", halt_reason),
        }
    return {
        "overall_status": "success",
        "halt_reason": None,
        "agent_log": log_event("join", "success", "All upstream agents succeeded"),
    }


def route_after_orchestrator(state: AriaState) -> str:
    if state["orchestrator_status"] == "success":
        return "notion_agent"
    return "join"


def route_after_notion(state: AriaState) -> list[str] | str:
    if state["notion_status"] == "success":
        return ["github_agent", "jira_agent"]
    return "join"


def build_graph():
    workflow = StateGraph(AriaState)

    # Per-node deadlines, given generous margin over observed worst-case timing
    # so ordinary free-tier latency variance doesn't surface as a visible
    # failure - the pipeline trades speed for not erroring out.
    workflow.add_node(
        "orchestrator",
        with_node_deadline(
            orchestrator_node, agent="orchestrator", status_key="orchestrator_status", error_key="orchestrator_error", seconds=60
        ),
    )
    workflow.add_node(
        "notion_agent",
        with_node_deadline(notion_agent_node, agent="notion", status_key="notion_status", error_key="notion_error", seconds=100),
    )
    workflow.add_node(
        "github_agent",
        with_node_deadline(github_agent_node, agent="github", status_key="github_status", error_key="github_error", seconds=270),
    )
    workflow.add_node(
        "jira_agent",
        with_node_deadline(jira_agent_node, agent="jira", status_key="jira_status", error_key="jira_error", seconds=100),
    )
    workflow.add_node("join", join_node)
    workflow.add_node(
        "slack_agent",
        with_node_deadline(slack_agent_node, agent="slack", status_key="slack_status", seconds=45),
    )

    workflow.add_edge(START, "orchestrator")
    workflow.add_conditional_edges(
        "orchestrator",
        route_after_orchestrator,
        ["notion_agent", "join"],
    )
    workflow.add_conditional_edges(
        "notion_agent",
        route_after_notion,
        ["github_agent", "jira_agent", "join"],
    )
    workflow.add_edge("github_agent", "join")
    workflow.add_edge("jira_agent", "join")
    workflow.add_edge("join", "slack_agent")
    workflow.add_edge("slack_agent", END)

    return workflow.compile()


aria_graph = build_graph()
