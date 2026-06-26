"""Uploads the golden dataset to LangSmith (idempotent) and runs the
orchestrator-only evaluation, producing an Experiment visible in the
LangSmith UI under the `aria-golden-v1` dataset.

Usage (from backend/): uv run python -m evals.run_orchestrator_eval
"""

from __future__ import annotations

import asyncio

from dotenv import load_dotenv

load_dotenv()

from langsmith import Client  # noqa: E402
from langsmith.evaluation import aevaluate  # noqa: E402

from evals.evaluators import (  # noqa: E402
    entity_keyword_match,
    extraction_fidelity_judge,
    split_count_match,
    split_fidelity_judge,
    structured_output_success,
    target,
)
from evals.golden_dataset import GOLDEN_DATASET  # noqa: E402

DATASET_NAME = "aria-golden-v1"


def ensure_dataset(client: Client) -> str:
    """Creates the dataset on first run; on later runs, only adds examples
    whose golden_id isn't already present, so re-running this after editing
    golden_dataset.py doesn't duplicate existing examples."""
    if client.has_dataset(dataset_name=DATASET_NAME):
        dataset = client.read_dataset(dataset_name=DATASET_NAME)
        existing = list(client.list_examples(dataset_id=dataset.id))
        existing_ids = {e.metadata.get("golden_id") for e in existing if e.metadata}
        new_examples = [ex for ex in GOLDEN_DATASET if ex["id"] not in existing_ids]
    else:
        dataset = client.create_dataset(
            DATASET_NAME, description="ARIA orchestrator (split + extraction) golden dataset"
        )
        new_examples = GOLDEN_DATASET

    for ex in new_examples:
        client.create_example(
            inputs={"raw_text": ex["input"]},
            outputs={
                "expected_split_count": ex["expected_split_count"],
                "expected_requirements": ex["expected_requirements"],
            },
            metadata={"golden_id": ex["id"], "category": ex["category"], "notes": ex["notes"]},
            dataset_id=dataset.id,
        )
    print(f"Dataset '{DATASET_NAME}': {len(new_examples)} example(s) added this run.")
    return dataset.name


async def main() -> None:
    client = Client()
    dataset_name = ensure_dataset(client)

    results = await aevaluate(
        target,
        data=dataset_name,
        evaluators=[
            split_count_match,
            entity_keyword_match,
            structured_output_success,
            extraction_fidelity_judge,
            split_fidelity_judge,
        ],
        experiment_prefix="orchestrator-eval",
        # Production never runs more than one concurrent Mistral call (the
        # only true parallel fan-out, github+jira, splits across two
        # different providers) - higher eval concurrency here was stacking
        # enough simultaneous Mistral requests to trip the free-tier rate
        # limit even with the existing per-call throttle.
        max_concurrency=1,
    )
    print(f"\nExperiment: {results.experiment_name}")


if __name__ == "__main__":
    asyncio.run(main())
