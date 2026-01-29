"""Decorators for registering task and evaluator functions.

These decorators are used in user experiment files to mark functions as
tasks or evaluators that can be discovered and run by the CLI.
"""

from __future__ import annotations

import inspect
from functools import wraps
from typing import Any, Callable, TypeVar

from ..protocol import EvalInput, EvalOutput, TaskInput, TaskOutput

F = TypeVar("F", bound=Callable[..., Any])

# Global registries
_tasks: dict[str, Callable[..., Any]] = {}
_evaluators: dict[str, Callable[..., Any]] = {}


def task(fn: F) -> F:
    """Register a function as a task.

    The decorated function receives a TaskInput and should return a TaskOutput
    (or a dict/string that can be converted to one).

    Example:
        @task
        async def my_task(input: TaskInput) -> TaskOutput:
            result = await call_llm(input.input["query"])
            return TaskOutput(output=result)
    """

    @wraps(fn)
    def wrapper(input_data: TaskInput) -> TaskOutput:
        result = fn(input_data)
        return _normalize_task_output(result)

    @wraps(fn)
    async def async_wrapper(input_data: TaskInput) -> TaskOutput:
        result = await fn(input_data)
        return _normalize_task_output(result)

    actual_wrapper = async_wrapper if inspect.iscoroutinefunction(fn) else wrapper
    _tasks[fn.__name__] = actual_wrapper
    # Preserve original function attributes
    actual_wrapper._original = fn  # type: ignore[attr-defined]
    actual_wrapper._is_async = inspect.iscoroutinefunction(fn)  # type: ignore[attr-defined]
    return actual_wrapper  # type: ignore[return-value]


def evaluator(fn: F) -> F:
    """Register a function as an evaluator.

    The decorated function receives an EvalInput and should return an EvalOutput
    (or a float/dict that can be converted to one).

    Example:
        @evaluator
        def accuracy(input: EvalInput) -> EvalOutput:
            expected = input.expected_output.get("answer")
            actual = input.actual_output
            score = 1.0 if expected == actual else 0.0
            return EvalOutput(score=score)
    """

    @wraps(fn)
    def wrapper(input_data: EvalInput) -> EvalOutput:
        result = fn(input_data)
        return _normalize_eval_output(result, fn.__name__)

    @wraps(fn)
    async def async_wrapper(input_data: EvalInput) -> EvalOutput:
        result = await fn(input_data)
        return _normalize_eval_output(result, fn.__name__)

    actual_wrapper = async_wrapper if inspect.iscoroutinefunction(fn) else wrapper
    _evaluators[fn.__name__] = actual_wrapper
    actual_wrapper._original = fn  # type: ignore[attr-defined]
    actual_wrapper._is_async = inspect.iscoroutinefunction(fn)  # type: ignore[attr-defined]
    return actual_wrapper  # type: ignore[return-value]


def get_task(name: str) -> Callable[..., Any] | None:
    """Get a registered task by name."""
    return _tasks.get(name)


def get_evaluator(name: str) -> Callable[..., Any] | None:
    """Get a registered evaluator by name."""
    return _evaluators.get(name)


def list_tasks() -> list[str]:
    """List all registered task names."""
    return list(_tasks.keys())


def list_evaluators() -> list[str]:
    """List all registered evaluator names."""
    return list(_evaluators.keys())


def clear_registry() -> None:
    """Clear all registered tasks and evaluators. Useful for testing."""
    _tasks.clear()
    _evaluators.clear()


def _normalize_task_output(result: Any) -> TaskOutput:
    """Normalize various return types to TaskOutput."""
    if isinstance(result, TaskOutput):
        return result
    if isinstance(result, dict):
        # Check if it looks like a TaskOutput dict
        if "output" in result:
            return TaskOutput.from_dict(result)
        # Otherwise treat the whole dict as the output
        return TaskOutput(output=result)
    if isinstance(result, (str, list)):
        return TaskOutput(output=result)
    # Fallback: convert to string
    return TaskOutput(output=str(result))


def _normalize_eval_output(result: Any, evaluator_name: str) -> EvalOutput:
    """Normalize various return types to EvalOutput."""
    if isinstance(result, EvalOutput):
        return result
    if isinstance(result, float):
        return EvalOutput(score=result)
    if isinstance(result, int):
        return EvalOutput(score=float(result))
    if isinstance(result, dict):
        if "score" in result:
            return EvalOutput.from_dict(result)
        # Assume it's metadata with an implicit score
        return EvalOutput(score=0.0, metadata=result)
    if isinstance(result, tuple) and len(result) >= 2:
        score, metadata = result[0], result[1]
        try:
            return EvalOutput(score=float(score), metadata=metadata)
        except (TypeError, ValueError):
            return EvalOutput(score=0.0, metadata=metadata)
    # Fallback: try to convert to float, default to 0.0 if that fails
    try:
        return EvalOutput(score=float(result))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return EvalOutput(
            score=0.0, metadata={"error": f"Could not convert result to score: {result}"}
        )


__all__ = [
    "task",
    "evaluator",
    "get_task",
    "get_evaluator",
    "list_tasks",
    "list_evaluators",
    "clear_registry",
]
