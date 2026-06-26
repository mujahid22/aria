"""Target function + evaluators for the orchestrator-only golden-dataset eval.

Scoped to the orchestrator (split + extraction) deliberately - see METRICS.md
on why this runs against the LLM-only path rather than the full side-effecting
pipeline: it's the part with no existing ground truth, needs to run repeatedly
and cheaply, and is where this project's own history shows real failure modes
(entity confusion between similarly-worded requirements about different
dashboards).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.agents.common import call_with_retry, get_llm
from app.agents.orchestrator import orchestrator_node, split_requirements
from app.state import initial_state


async def target(inputs: dict) -> dict:
    """Runs the same two LLM calls production uses (split, then per-item
    extraction) - no MCP/Notion/GitHub/Jira/Slack involved, so this is free
    of side effects and safe to run repeatedly."""
    raw_text = inputs["raw_text"]
    snippets = await split_requirements(raw_text)

    extractions = []
    for snippet in snippets:
        result = await orchestrator_node(initial_state(snippet))
        extractions.append(
            {
                "snippet": snippet,
                "status": result.get("orchestrator_status"),
                "title": result.get("requirement_title", ""),
                "description": result.get("requirement_description", ""),
                "acceptance_criteria": result.get("acceptance_criteria", []),
                "priority": result.get("priority", ""),
            }
        )

    return {"split_count": len(snippets), "snippets": snippets, "extractions": extractions}


# ---------------------------------------------------------------------------
# Deterministic evaluators
# ---------------------------------------------------------------------------


def split_count_match(run, example) -> dict:
    expected = example.outputs["expected_split_count"]
    actual = run.outputs.get("split_count", 0)
    return {
        "key": "split_count_match",
        "score": 1.0 if actual == expected else 0.0,
        "comment": f"expected {expected}, got {actual}",
    }


def entity_keyword_match(run, example) -> dict:
    """For each expected requirement, does at least one produced extraction
    contain one of its title_keywords (in title or description)? Greedy
    best-effort matching since split order isn't guaranteed to align with the
    reference order."""
    expected_reqs = example.outputs["expected_requirements"]
    extractions = run.outputs.get("extractions", [])
    haystacks = [
        (e.get("title", "") + " " + e.get("description", "")).lower() for e in extractions
    ]

    matched = 0
    details = []
    used = set()
    for req in expected_reqs:
        keywords = [k.lower() for k in req["title_keywords"]]
        hit_index = None
        for i, haystack in enumerate(haystacks):
            if i in used:
                continue
            if any(kw in haystack for kw in keywords):
                hit_index = i
                break
        if hit_index is not None:
            matched += 1
            used.add(hit_index)
            details.append(f"OK '{req['key_entity']}'")
        else:
            details.append(f"MISS '{req['key_entity']}' (keywords={req['title_keywords']})")

    score = matched / len(expected_reqs) if expected_reqs else 1.0
    return {"key": "entity_keyword_match", "score": score, "comment": "; ".join(details)}


def structured_output_success(run, example) -> dict:
    """Did every produced extraction actually succeed (no orchestrator node
    failure/fallback for any split item)?"""
    extractions = run.outputs.get("extractions", [])
    if not extractions:
        return {"key": "structured_output_success", "score": 0.0, "comment": "no extractions produced"}
    failures = [e for e in extractions if e.get("status") != "success"]
    score = 1.0 - (len(failures) / len(extractions))
    return {
        "key": "structured_output_success",
        "score": score,
        "comment": f"{len(failures)}/{len(extractions)} extraction(s) failed",
    }


# ---------------------------------------------------------------------------
# LLM-as-judge evaluators
# ---------------------------------------------------------------------------

_FIDELITY_PROMPT = """You are grading whether a structured extraction faithfully \
represents a source requirement, with no invented scope.

Source requirement snippet:
{snippet}

Extracted title: {title}
Extracted description: {description}
Extracted acceptance criteria: {criteria}

Grade on a 1-5 scale: 5 = fully faithful, captures the source with no invented \
scope; 3 = mostly faithful but adds or omits something non-trivial; 1 = \
significantly invents scope not in the source or misses the actual ask."""


class FidelityGrade(BaseModel):
    score: int = Field(description="1-5 faithfulness score")
    rationale: str = Field(description="One sentence explaining the score")


async def extraction_fidelity_judge(run, example) -> dict:
    extractions = run.outputs.get("extractions", [])
    if not extractions:
        return {"key": "extraction_fidelity", "score": 0.0, "comment": "no extractions produced"}

    judge = get_llm(temperature=0.0).with_structured_output(FidelityGrade)
    scores = []
    comments = []
    for e in extractions:
        prompt = _FIDELITY_PROMPT.format(
            snippet=e["snippet"],
            title=e["title"],
            description=e["description"],
            criteria="; ".join(e["acceptance_criteria"]),
        )
        grade: FidelityGrade = await call_with_retry(
            lambda p=prompt: judge.ainvoke(p), attempts=4, timeout=25.0
        )
        scores.append(grade.score)
        comments.append(f"{e['title']!r}: {grade.score}/5 - {grade.rationale}")

    avg = sum(scores) / len(scores) / 5.0  # normalize to 0-1
    return {"key": "extraction_fidelity", "score": avg, "comment": " | ".join(comments)}


_SPLIT_FIDELITY_PROMPT = """You are grading whether a set of split requirement \
snippets correctly and completely covers a set of expected distinct requirements, \
with no merging two requirements into one snippet and no inventing extra ones.

Original input:
{raw_text}

Expected distinct requirements (by subject):
{expected}

Produced split snippets:
{produced}

Grade on a 0-1 scale: 1.0 = every expected requirement is represented exactly \
once with no merging/contamination/invention; 0.5 = mostly right but one \
issue (a merge, a miss, or an invented extra item); 0.0 = split badly wrong."""


class SplitFidelityGrade(BaseModel):
    score: float = Field(description="0.0-1.0 split fidelity score")
    rationale: str = Field(description="One sentence explaining the score")


async def split_fidelity_judge(run, example) -> dict:
    raw_text = example.inputs["raw_text"]
    expected_reqs = example.outputs["expected_requirements"]
    snippets = run.outputs.get("snippets", [])

    judge = get_llm(temperature=0.0).with_structured_output(SplitFidelityGrade)
    prompt = _SPLIT_FIDELITY_PROMPT.format(
        raw_text=raw_text,
        expected="\n".join(f"- {r['key_entity']}" for r in expected_reqs),
        produced="\n".join(f"- {s}" for s in snippets) or "(none)",
    )
    grade: SplitFidelityGrade = await call_with_retry(
        lambda: judge.ainvoke(prompt), attempts=4, timeout=25.0
    )
    return {"key": "split_fidelity", "score": grade.score, "comment": grade.rationale}
