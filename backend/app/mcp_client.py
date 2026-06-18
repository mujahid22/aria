"""MCP server connection definitions and per-agent tool loading."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

from app.config import settings


def build_mcp_client() -> MultiServerMCPClient:
    """Each server runs as a local stdio subprocess - no OAuth redirect handling
    needed, which keeps the backend fully non-interactive for an automated pipeline.
    """
    return MultiServerMCPClient(
        {
            "notion": {
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "@notionhq/notion-mcp-server"],
                "env": {
                    "NOTION_TOKEN": settings.notion_api_key,
                },
            },
            # Locally this shells out to `docker run` for the official image. Most
            # PaaS hosts (Fly.io included) don't support Docker-in-Docker for a
            # running container, so the deploy image instead bakes in the same
            # binary the image wraps (extracted at build time) and runs it
            # directly - see backend/Dockerfile.
            "github": (
                {
                    "transport": "stdio",
                    "command": "docker",
                    "args": [
                        "run",
                        "-i",
                        "--rm",
                        "-e",
                        "GITHUB_PERSONAL_ACCESS_TOKEN",
                        "ghcr.io/github/github-mcp-server",
                    ],
                    "env": {
                        "GITHUB_PERSONAL_ACCESS_TOKEN": settings.github_token,
                    },
                }
                if settings.github_mcp_use_docker
                else {
                    "transport": "stdio",
                    "command": "github-mcp-server",
                    "args": ["stdio"],
                    "env": {
                        "GITHUB_PERSONAL_ACCESS_TOKEN": settings.github_token,
                    },
                }
            ),
            "jira": {
                "transport": "stdio",
                "command": "uvx",
                "args": ["mcp-atlassian"],
                "env": {
                    "JIRA_URL": settings.jira_url,
                    "JIRA_USERNAME": settings.jira_username,
                    "JIRA_API_TOKEN": settings.jira_api_token,
                },
            },
            "slack": {
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-slack"],
                "env": {
                    "SLACK_BOT_TOKEN": settings.slack_bot_token,
                    "SLACK_TEAM_ID": settings.slack_team_id,
                },
            },
        }
    )


_client: MultiServerMCPClient | None = None


def get_mcp_client() -> MultiServerMCPClient:
    global _client
    if _client is None:
        _client = build_mcp_client()
    return _client


async def get_tools(server_name: str) -> list[BaseTool]:
    return await get_mcp_client().get_tools(server_name=server_name)


@asynccontextmanager
async def tools_session(server_name: str) -> AsyncIterator[list[BaseTool]]:
    """Like get_tools(), but keeps one MCP subprocess session open for the
    whole `async with` block instead of opening a new one per tool call.

    langchain_mcp_adapters' default get_tools() passes session=None down to
    each tool, so every single tool invocation - not just the initial listing -
    spins up a brand-new subprocess (`uvx`/`npx`/`docker run`) from scratch.
    That's the dominant source of this app's latency variance: an agent that
    makes 2-4 tool calls was launching 2-4 separate subprocesses, each with its
    own random startup cost, instead of 1."""
    async with get_mcp_client().session(server_name) as session:
        tools = await load_mcp_tools(session, server_name=server_name)
        yield tools
