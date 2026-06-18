"""Environment-driven settings for ARIA's LLM and MCP server connections."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.environ.get(name, "")
    return value


class Settings:
    # LLM - NVIDIA NIM (Llama 3.3 70B Instruct), used only by the GitHub agent:
    # its 3-step flow shares a separate rate-limit pool from the other agents'
    # Mistral quota, so it isn't starved by them.
    nvidia_api_key: str = _require("NVIDIA_API_KEY")
    nvidia_model: str = os.environ.get("NVIDIA_MODEL", "meta/llama-3.3-70b-instruct")

    # LLM - Mistral, used by orchestrator/notion/jira/slack
    mistral_api_key: str = _require("MISTRAL_API_KEY")
    mistral_model: str = os.environ.get("MISTRAL_MODEL", "mistral-large-latest")

    # Notion (official local MCP server, internal integration token)
    notion_api_key: str = _require("NOTION_API_KEY")
    notion_parent_page_id: str = _require("NOTION_PARENT_PAGE_ID")

    # GitHub (official github-mcp-server). Locally run via Docker; the deploy
    # image instead runs the extracted binary directly (no Docker-in-Docker).
    github_token: str = _require("GITHUB_PERSONAL_ACCESS_TOKEN")
    github_owner: str = _require("GITHUB_OWNER")
    github_repo: str = _require("GITHUB_REPO")
    github_mcp_use_docker: bool = os.environ.get("GITHUB_MCP_USE_DOCKER", "true").lower() == "true"

    # Jira (mcp-atlassian, API token auth)
    jira_url: str = _require("JIRA_URL")
    jira_username: str = _require("JIRA_USERNAME")
    jira_api_token: str = _require("JIRA_API_TOKEN")
    jira_project_key: str = _require("JIRA_PROJECT_KEY")

    # Slack (official reference MCP server, bot token auth)
    slack_bot_token: str = _require("SLACK_BOT_TOKEN")
    slack_team_id: str = _require("SLACK_TEAM_ID")
    slack_channel_id: str = _require("SLACK_CHANNEL_ID")

    # Deployed frontend origin, added to CORS allow-list alongside localhost.
    frontend_origin: str = os.environ.get("FRONTEND_ORIGIN", "")


settings = Settings()
