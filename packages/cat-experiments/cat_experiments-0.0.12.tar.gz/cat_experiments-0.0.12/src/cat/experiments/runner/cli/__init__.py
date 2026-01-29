"""CLI protocol types and decorators for subprocess-based task/evaluator invocation."""

from __future__ import annotations

from ...protocol import EvalInput, EvalOutput, TaskInput, TaskOutput
from ...sdk.decorators import evaluator, task
from .runner import run

__all__ = [
    # Protocol types for type hints
    "TaskInput",
    "TaskOutput",
    "EvalInput",
    "EvalOutput",
    # Decorators for experiment files
    "task",
    "evaluator",
    # Entry point for experiment files
    "run",
]
