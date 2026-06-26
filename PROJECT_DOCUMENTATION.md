# ARIA — Project Documentation

**ARIA (Automated Requirements Intelligence Agent)** converts a free-text product
requirement (or a bundle of several, e.g. raw meeting notes) into a Notion BRD, a
GitHub technical-doc PR, a Jira backlog issue, and a Slack notification —
automatically, via a multi-agent pipeline.

## 1. Tech Stack

| Layer | Choice |
|---|---|
| Backend language/runtime | Python 3.13, managed with `uv` |
| Backend framework | FastAPI (HTTP + WebSocket) |
| Agent orchestration | LangGraph (`StateGraph`) |
| LLM abstraction | LangChain |
| Tool integration | MCP (Model Context Protocol) |
| Frontend framework | Next.js 16 (App Router, Turbopack, standalone output) |
| UI | React 19, TypeScript, Tailwind CSS v4, Framer Motion |
| Containerization | Docker (multi-stage builds) |
| Hosting | Fly.io (both services) |
| Source control | GitHub (`mujahid22/aria`) |

## 2. Model Selection

| Agent(s) | Model | Why |
|---|---|---|
| Orchestrator, Notion, Jira, Slack | Mistral `mistral-large-latest` | Single fast, cheap model for straightforward structuring/tool-calling tasks |
| GitHub | NVIDIA NIM — Llama 3.3 70B Instruct | Deliberately on a **separate** provider/rate-limit pool. GitHub's 3-step flow (branch → file → PR) issues more LLM calls per run than the others; sharing Mistral's free-tier quota across all five agents was starving GitHub specifically. Splitting providers isolates that quota pressure. |

Both are free/low-cost tiers — a deliberate constraint of this build, which is why
much of the engineering effort (next section) went into absorbing their latency
and rate-limit variance rather than assuming a premium, low-latency model.

## 3. Framework / Architectural Choices

- **LangGraph over a freeform agent loop**: the pipeline is modeled as an explicit
  state machine with conditional edges (skip downstream steps on failure) and a
  real parallel fan-out (GitHub + Jira run concurrently after Notion succeeds,
  rejoining at a `join` node). This makes failure handling a routing decision,
  not an exception, and keeps the whole flow inspectable/debuggable.
- **MCP over hand-rolled API clients**: Notion, GitHub, Jira, and Slack already
  ship official MCP servers. Using them via `langchain-mcp-adapters` means each
  agent gets real tool-calling against the live product instead of bespoke REST
  wrappers per integration.
- **WebSocket streaming over polling**: the frontend gets live per-node progress
  events (`/ws/run`) so the UI can animate each agent as it works, instead of
  polling for a final result.
- **Orchestrator-owned requirement splitting over a separate splitter agent or
  LangGraph's `Send` map-reduce API**: when a submission bundles multiple
  requirements (e.g. meeting notes), splitting was added as a second focused LLM
  call inside the existing orchestrator, and the FastAPI layer loops the
  *unmodified* graph once per split item. This was chosen over `Send`-based
  fan-out to avoid multiplying concurrent LLM pressure across already-fragile
  free-tier rate limits, and to avoid restructuring the flat pipeline state or
  the frontend's single-pipeline visualization.

## 4. Pipeline Flow

```
        ┌──────────────┐
        │ Orchestrator │  splits + structures the raw requirement(s)
        └──────┬───────┘
               ▼
        ┌──────────────┐
        │    Notion    │  writes the BRD
        └──────┬───────┘
               ▼
       ┌───────┴────────┐
       ▼                ▼
 ┌──────────┐      ┌──────────┐
 │  GitHub  │      │   Jira   │   run in parallel
 │ (tech doc│      │ (backlog │
 │  PR)     │      │  issue)  │
 └────┬─────┘      └────┬─────┘
      └────────┬────────┘
               ▼
          ┌─────────┐
          │  Join   │  aggregates status; any failure ⇒ overall "failed"
          └────┬────┘
               ▼
          ┌─────────┐
          │  Slack  │  posts success or failure notification
          └─────────┘
```

For a multi-requirement submission, this entire graph runs once per split
requirement, sequentially, with progress streamed per-requirement to the UI.

## 5. Reliability Engineering

Free-tier LLM APIs are the main source of fragility in this system, so a
disproportionate amount of effort went into absorbing that rather than assuming
reliable, low-latency calls:

- **Per-node deadlines**, tuned from observed real failures rather than guessed
  up front: Orchestrator 60s, Notion 100s, Jira 100s, GitHub 270s, Slack 45s.
  GitHub's is largest because its 3-step flow needs the most LLM round-trips.
- **Retry wrapper** (`call_with_retry`) with rate-limit-aware exponential backoff
  for `429`s and a short fixed delay for other transient errors (e.g. an MCP
  stdio subprocess hiccup).
- **A documented dead end, kept as institutional knowledge**: adding a
  per-attempt timeout *inside* the GitHub agent's tool-calling loop (to recover
  from a silently-hung LLM call) was tried and reverted — cancelling a call
  nested inside an open MCP session destabilized the session's internal task
  group, producing a worse failure than a plain timeout. The fix instead relies
  solely on the outer node deadline as the cancellation boundary.

## 6. Deployment

- Both services are Dockerized and deployed to **Fly.io**.
- The GitHub MCP server normally runs via `docker run` locally; the deploy image
  instead extracts and runs its binary directly (`GITHUB_MCP_USE_DOCKER=false`),
  since most PaaS hosts don't support Docker-in-Docker for a running container.
- Frontend is a standalone Next.js build; `NEXT_PUBLIC_WS_URL` is baked in at
  Docker build time (Next.js inlines `NEXT_PUBLIC_*` vars at build, not runtime).
- Backend CORS allow-list and the frontend's WebSocket target are both
  environment-driven (`FRONTEND_ORIGIN`, `NEXT_PUBLIC_WS_URL`) so the same images
  work across environments without code changes.
- **Google Cloud Run was evaluated** as a genuinely free alternative but paused:
  it requires an active billing account linked to the project even for free-tier
  usage, which conflicted with the goal of having nothing card-linked running.

## 7. Frontend Highlights

- Apple-inspired visual design with a custom avatar per agent, live pipeline
  visualization, and a CSS-grid "futuristic" background.
- Container-query-based responsive layout (not viewport-based) since panel width
  depends on grid position, not screen size.
- `useRef`-based state pattern in the run hook to avoid React Strict Mode
  double-invocation bugs that surfaced as duplicate UI entries during testing.
