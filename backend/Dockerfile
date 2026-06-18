FROM ghcr.io/github/github-mcp-server:latest AS github-mcp

FROM python:3.13-slim

# Node.js for the npx-based MCP servers (Notion, Slack); uv for the app
# itself and the uvx-based Jira MCP server.
RUN apt-get update && apt-get install -y --no-install-recommends \
        nodejs npm ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Pre-install the npm-based MCP servers so `npx -y <pkg>` resolves from the
# global install instead of hitting the registry on every cold start.
RUN npm install -g @notionhq/notion-mcp-server @modelcontextprotocol/server-slack

# No Docker-in-Docker on most PaaS hosts, so the GitHub MCP server's binary
# is extracted from its official image and run directly instead - see
# GITHUB_MCP_USE_DOCKER in app/mcp_client.py.
COPY --from=github-mcp /server/github-mcp-server /usr/local/bin/github-mcp-server

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app ./app

# Pre-warm uv's cache for the Jira MCP server so the first real run doesn't
# pay a registry round-trip on top of its node deadline.
RUN uvx mcp-atlassian --help > /dev/null 2>&1 || true

ENV GITHUB_MCP_USE_DOCKER=false
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
