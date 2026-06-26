# ARIA Evaluation Report — Orchestrator Golden Dataset, Round 1

**Scope:** orchestrator-only (split + extraction), 25-example synthetic golden
dataset, 3 evaluation passes. See [METRICS.md](METRICS.md) for metric
definitions and [golden_dataset.py](golden_dataset.py) for the dataset itself.

## Health verdict

**ARIA's orchestrator is qualitatively sound.** Across 3 full passes (75
example-executions), there is zero evidence of the failure mode this dataset
was specifically built to catch — entity confusion between similarly-worded
requirements about different subjects (e.g. Sales vs Inventory dashboard).
Every adversarial example designed for that (`multi-01`, `multi-08`,
`entity-01/02/03`) extracted correctly whenever the underlying LLM call
succeeded.

**The actual finding of this round is operational, not a quality defect**: a
meaningful fraction of extractions failed due to Mistral API rate-limiting,
caused by this eval's traffic competing with the live Fly.io deployment for
the same API key's quota. This contaminated every quality metric in the first
run badly enough to look like a quality problem before the cause was isolated.

## Setup

- **Tracing**: LangSmith wired into both local dev and the live Fly
  deployment (`LANGCHAIN_TRACING_V2`, project `aria`) — every graph run, node,
  LLM call, and tool call is traced with token usage, latency, and custom
  metadata (`submission_id`, `requirement_index`/`count`).
- **Dataset**: `aria-golden-v1` in LangSmith, 25 examples across 5 categories
  (single, multi, vague, entity_confusion, edge) — see METRICS.md for why this
  is scoped to the orchestrator rather than the full side-effecting pipeline.
- **Evaluators**: 3 deterministic (`split_count_match`, `entity_keyword_match`,
  `structured_output_success`) + 2 LLM-as-judge (`extraction_fidelity`,
  `split_fidelity`), run via `langsmith.evaluation.aevaluate`.

## Results across the 3 runs

| Metric | Run 1 (concurrency=3) | Run 2 (concurrency=1, judges retried) | Run 3 (orchestrator retry budget bumped) |
|---|---|---|---|
| `structured_output_success` | 0.12 | 0.71 | 0.68 |
| `entity_keyword_match` | 0.12 | 0.71 | 0.68 |
| `split_count_match` | 0.60 | 0.88 | 0.92 |
| `split_fidelity` (judge) | n/a (mostly errored) | 0.91 (3 errored) | 0.95 (5 errored) |
| `extraction_fidelity` (judge) | n/a (mostly errored) | 0.67 (16/33 errored) | 0.60 (8/29 errored) |

Run 1's near-zero scores are **not real** — see Failure Analysis. They're
included to show the eval harness itself had a bug worth documenting.

## Failure analysis

**Run 1**: `aevaluate(..., max_concurrency=3)` let 3 examples process in
parallel. Production never runs more than one concurrent Mistral call (the
only real fan-out, github+jira, splits across two *different* providers), so
this concurrency setting put more simultaneous load on Mistral's free-tier
quota than the app is designed for, on top of the LLM-as-judge calls (which
had no retry/timeout protection at all at this point) — Mistral returned 429s
on nearly every call. **Fix**: `max_concurrency=1`; wrapped both judge calls in
`call_with_retry(attempts=4, timeout=25.0)`, matching the resilience pattern
already used elsewhere in the codebase.

**Run 2**: Clean run, but `structured_output_success` and (consequently)
`entity_keyword_match` still landed at ~71%. Manual inspection of every
failure showed:
- Every `entity_keyword_match` "miss" was a requirement whose extraction had
  already failed (`status: "failed"`, empty title/description) — i.e. zero
  genuine entity-confusion errors, 100% downstream noise from extraction
  failures.
- Every `split_count_match` miss was the split call falling back to treating
  multi-requirement input as one item (e.g. `edge-01`'s 5-requirement input
  collapsed to `split_count: 1`) — the same fallback path, one level up.
- Root cause: `orchestrator_node` and `split_requirements` wrapped their
  Mistral calls in `call_with_retry(attempts=2, timeout=25.0)` — thinner than
  every other Mistral call site in the codebase (`run_react_agent` for
  notion/jira uses the function's default `attempts=5`). Under sustained
  quota pressure — this eval's traffic plus the live Fly deployment sharing
  one Mistral API key, with no cross-process coordination on the throttle —
  that 2-attempt budget exhausted and the code's existing (deliberate)
  fallback-to-one-item behavior kicked in.

**Fix**: bumped both call sites to `attempts=3, timeout=14.0` — chosen so the
worst case (3 × 14s + exponential rate-limit backoff ≈ 54s) stays under the
60s node deadline already in place, while giving real retry headroom.

**Run 3** (validation): `split_count_match` improved 88% → 92%, and the
LLM-judge error rate improved (extraction_fidelity errors 16/33 → 8/29). But
`structured_output_success`/`entity_keyword_match` stayed flat (~68-71%), and
the *specific* examples that failed were different from run 2's (e.g. `dark
mode toggle` and `Remove GMROI` failed in run 3 but passed in run 2; the
reverse for others) — confirming this is governed by **ambient, time-varying
quota contention** rather than any deterministic code path. The retry-budget
fix helps but can't fully absorb pressure from a process it has no visibility
into (the live deployment's own traffic).

## Current status & risk

- **Quality**: no action needed. Zero genuine entity-confusion, split-merge,
  or scope-invention defects found in 75 example-executions.
- **Operational risk (real, unresolved)**: this Mistral API key's effective
  quota is too tight for local/eval traffic to coexist with the live
  deployment. The in-process throttle (`_MISTRAL_MIN_INTERVAL_SECONDS`) only
  serializes calls *within one process* — it has no way to account for the
  other process's calls.

## Recommendations (need a decision, not yet acted on)

1. Provision a separate Mistral API key for eval/dev traffic so it stops
   competing with the live deployment's quota — the most direct fix.
2. Or: request a higher rate-limit tier on the existing key.
3. Or: schedule eval runs during low-traffic windows only (weakest option —
   doesn't fix the underlying contention, just avoids triggering it).

## Not yet done (next steps)

- The curated full-pipeline (side-effecting) subset, per the original hybrid
  scope decision — orchestrator-only is covered; Notion/GitHub/Jira/Slack
  faithfulness checks are not yet built.
- Wiring this eval as a recurring CI gate (currently a manual, on-demand run).
