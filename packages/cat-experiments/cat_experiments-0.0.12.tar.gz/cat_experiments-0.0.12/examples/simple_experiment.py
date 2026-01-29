"""
Simple experiment example demonstrating how to set up a task and evaluator.

Run with:
    cat-experiments run examples/simple_experiment.py --dataset examples/sample_data.jsonl
"""

from __future__ import annotations

from cat.experiments.protocol import EvalInput, EvalOutput, TaskInput, TaskOutput
from cat.experiments.sdk import evaluator, task


@task
async def my_task(input: TaskInput) -> TaskOutput:
    """
    The system under test.

    This is where you would call your LLM, agent, or any other system.
    For this example, we just uppercase the question.
    """
    question = input.input.get("question", "")
    return TaskOutput(output={"answer": question.upper()})


@evaluator
async def exact_match(input: EvalInput) -> EvalOutput:
    """
    Check if the actual output matches the expected output exactly.
    """
    expected = input.expected_output.get("answer", "") if input.expected_output else ""
    actual_output = input.actual_output
    actual = (
        actual_output.get("answer", "") if isinstance(actual_output, dict) else str(actual_output)
    )

    score = 1.0 if expected == actual else 0.0
    return EvalOutput(
        score=score,
        label="match" if score == 1.0 else "mismatch",
        metadata={"expected": expected, "actual": actual},
    )


@evaluator
async def contains_keyword(input: EvalInput) -> EvalOutput:
    """
    Check if the response contains a specific keyword from the example metadata.
    """
    metadata = input.example.get("metadata") or {}
    keyword = metadata.get("keyword", "")
    actual_output = input.actual_output
    actual = (
        actual_output.get("answer", "") if isinstance(actual_output, dict) else str(actual_output)
    )

    found = keyword.lower() in actual.lower() if keyword else True
    score = 1.0 if found else 0.0

    return EvalOutput(
        score=score,
        label="found" if found else "missing",
        metadata={"keyword": keyword, "found": found},
    )


if __name__ == "__main__":
    # Run with: cat-experiments run examples/simple_experiment.py --dataset <data.jsonl>
    pass
