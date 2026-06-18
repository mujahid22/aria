# ARIA

ARIA (Automated Requirements Intelligence Agent) turns free-text product requirements
into a Notion BRD, a GitHub technical-doc PR, a Jira backlog issue, and a Slack
notification - automatically, via a LangGraph multi-agent pipeline.

## Structure

- `backend/` - FastAPI + LangGraph pipeline, orchestrating Notion/GitHub/Jira/Slack
  MCP servers. See `backend/README.md` for local setup.
- `frontend/` - Next.js UI that submits requirements and streams the pipeline's
  progress live over a WebSocket. See `frontend/README.md` for local setup.

## Running locally

```bash
# backend
cd backend
cp .env.example .env   # fill in API keys
uv run uvicorn app.main:app --reload

# frontend
cd frontend
npm install
npm run dev
```

## Deployment

Both services have Dockerfiles and are currently deployed on Fly.io:
- Backend: `flyctl deploy --app aria-backend-mujahid` (from `backend/`)
- Frontend: `flyctl deploy --app aria-frontend-mujahid --build-arg NEXT_PUBLIC_WS_URL=wss://aria-backend-mujahid.fly.dev/ws/run` (from `frontend/`)
