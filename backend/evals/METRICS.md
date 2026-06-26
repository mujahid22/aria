# ARIA Evaluation Metrics

Two families of metrics: **operational** (is the system reliable and fast?) and
**quality** (is the output actually correct?). Operational metrics come straight
from LangSmith trace data; quality metrics need the golden dataset and a grader
(deterministic check or LLM-as-judge), since "correct" here means a generative
output faithfully represents free-text input.

## 1. Operational Metrics

| Metric | Definition | Source |
|---|---|---|
| End-to-end success rate | % of runs with `overall_status == "success"` | `agent_log` / final state |
| Per-node failure rate | % of runs where each node (`orchestrator`, `notion`, `github`, `jira`, `slack`) reports `status == "failed"`, broken out per node | final state per node |
| Per-node latency | p50/p90/p99 duration, per node | LangSmith run duration, grouped by `langgraph_node` metadata |
| End-to-end latency | p50/p90/p99 duration, per requirement | LangSmith root run duration |
| Timeout rate | % of failures whose error message matches `"timed out after"` | `*_error` fields |
| Retry rate | % of LLM/tool calls where `call_with_retry` needed more than one attempt | inferred from multiple sibling LLM-call runs under the same parent step in LangSmith |
| Token cost per run | total tokens, split by provider (Mistral vs NVIDIA NIM) since they have separate cost/rate-limit profiles | LangSmith `usage_metadata` on `llm`-type runs |

**Current known baseline going in**: per-node deadlines were already tuned from
real failures earlier (orchestrator 60s, notion 100s, jira 100s, github 270s,
slack 45s) - so the operational metrics above are partly a regression check
against that prior tuning, not a cold start.

## 2. Quality Metrics

| Metric | Definition | Grading method |
|---|---|---|
| Split correctness | For multi-requirement input, does the split produce exactly the expected count, with each item mapping 1:1 to a distinct source requirement (no merges, no invented items)? | Deterministic: split count == reference count. LLM-as-judge: each split snippet maps to exactly one reference requirement with no cross-contamination. |
| Extraction fidelity | Does `requirement_title`/`requirement_description`/`acceptance_criteria`/`priority` accurately represent the input, without inventing scope the input didn't ask for? | LLM-as-judge, 1-5 scale, graded against the source text (not a fixed reference answer, since phrasing legitimately varies) |
| Entity correctness | Does the extraction reference the correct subject (e.g. "Sales Dashboard" vs "Inventory Dashboard")? This is a real, previously-observed failure mode - this project's own test history includes a case where Net Sales formatting and GMROI removal (two different dashboards) were live test inputs precisely because of that risk. | Deterministic substring/keyword check against reference entities per golden example |
| BRD / tech doc / Jira faithfulness | Does the downstream artifact (Notion BRD content, GitHub tech doc, Jira issue body) stay faithful to the orchestrator's structured extraction - no further drift or invention at the second hop? | LLM-as-judge, graded against `requirement_description` + `acceptance_criteria`, not the raw input (isolates whether each agent introduces its own drift) |
| Structured-output success rate | Did `with_structured_output` parsing succeed without exhausting `call_with_retry`'s attempts? | Deterministic: orchestrator/split node status, since a parse failure surfaces as a node failure by construction |

## 3. What's Out of Scope (for now)

- Grading the actual *business* correctness of a requirement (e.g. "should this
  feature exist at all") - ARIA's job is faithful capture and routing, not
  product judgment.
- Notion/GitHub/Jira/Slack API correctness beyond "did the call succeed and
  return the artifact" - their own platforms are trusted once ARIA hands off.

## 4. Reporting Cadence

For this round: one full evaluation pass (golden dataset → run → grade →
analyze failures → fix → re-run → report). Not yet wired as a recurring CI gate
- that's a reasonable next step once this baseline exists.
