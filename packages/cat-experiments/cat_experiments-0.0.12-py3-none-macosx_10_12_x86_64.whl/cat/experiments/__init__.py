"""
cat-experiments: Standalone evaluation engine for LLM applications.

Usage:
    1. Write an experiment file with @task and @evaluator decorators
    2. Run with: `cat-experiments run <experiment_file.py> --dataset <data.jsonl>`

Example experiment:
    from cat.experiments import task, evaluator, TaskInput, EvalInput

    @task
    async def my_task(input: TaskInput) -> dict:
        # Your LLM task logic here
        return {"response": "..."}

    @evaluator
    async def my_evaluator(input: EvalInput) -> float:
        # Score the task output
        return 1.0 if input.actual_output == input.expected_output else 0.0
"""

from __future__ import annotations

# Protocol types (for type hints in task/evaluator functions)
from .protocol import (
    DatasetExample,
    EvalInput,
    EvalOutput,
    TaskInput,
    TaskOutput,
)

# SDK decorators
from .sdk import (
    evaluator,
    task,
)

# Tool call matching utilities
from .sdk.tools import (
    ToolCallMatch,
    ToolCallMatchingResult,
    match_tool_calls,
)

# Tracing utilities
from .sdk.tracing import (
    capture_trace,
    extract_tool_calls,
)

__all__ = [
    # Decorators (primary API)
    "task",
    "evaluator",
    # Protocol types
    "TaskInput",
    "TaskOutput",
    "EvalInput",
    "EvalOutput",
    "DatasetExample",
    # Tool call matching
    "match_tool_calls",
    "ToolCallMatch",
    "ToolCallMatchingResult",
    # Tracing
    "capture_trace",
    "extract_tool_calls",
]
