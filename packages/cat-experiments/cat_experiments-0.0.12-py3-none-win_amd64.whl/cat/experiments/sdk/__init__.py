"""Python SDK for writing cat-experiments experiment files.

This package provides the decorators and types for defining experiments:

    from cat.experiments.sdk import task, evaluator, TaskInput, TaskOutput, EvalInput, EvalOutput

    @task
    async def my_task(input: TaskInput) -> TaskOutput:
        ...

    @evaluator
    def my_evaluator(input: EvalInput) -> EvalOutput:
        ...

For convenience, these are also re-exported from the main cat.experiments package.
"""

from __future__ import annotations

# Re-export protocol types that users commonly need
from ..protocol import (
    EvalInput,
    EvalOutput,
    TaskInput,
    TaskOutput,
)

# Aggregate evaluator helpers
from .agg_ci import make_wilson_ci_aggregate

# Decorators
from .decorators import (
    clear_registry,
    evaluator,
    get_evaluator,
    get_task,
    list_evaluators,
    list_tasks,
    task,
)

# Tool call matching utilities
from .tools import (
    ToolCallMatch,
    ToolCallMatchingResult,
    match_tool_calls,
)

__all__ = [
    # Decorators
    "task",
    "evaluator",
    "get_task",
    "get_evaluator",
    "list_tasks",
    "list_evaluators",
    "clear_registry",
    # Protocol types
    "TaskInput",
    "TaskOutput",
    "EvalInput",
    "EvalOutput",
    # Tool call matching
    "match_tool_calls",
    "ToolCallMatch",
    "ToolCallMatchingResult",
    # Aggregate evaluators
    "make_wilson_ci_aggregate",
]
