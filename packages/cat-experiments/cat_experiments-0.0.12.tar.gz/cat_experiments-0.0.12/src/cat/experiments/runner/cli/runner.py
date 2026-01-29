"""CLI entry point for running tasks and evaluators via stdin/stdout."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Any

from ...protocol import EvalInput, EvalOutput, TaskInput, TaskOutput
from ...sdk.decorators import get_evaluator, get_task, list_evaluators, list_tasks


def run(
    task_name: str | None = None,
    evaluator_name: str | None = None,
) -> None:
    """Entry point for CLI mode.

    Reads JSON from stdin, invokes the specified task or evaluator,
    and writes JSON to stdout.

    Usage:
        python -m my_module --task task_name
        python -m my_module --evaluator eval_name
    """
    args = _parse_args()

    # Override with explicit arguments if provided
    task_name = task_name or args.task
    evaluator_name = evaluator_name or args.evaluator

    if args.list:
        _list_registered()
        return

    if not task_name and not evaluator_name:
        print("Error: Must specify --task or --evaluator", file=sys.stderr)
        sys.exit(1)

    if task_name and evaluator_name:
        print("Error: Cannot specify both --task and --evaluator", file=sys.stderr)
        sys.exit(1)

    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        if task_name:
            result = _run_task(task_name, input_data)
        else:
            result = _run_evaluator(evaluator_name, input_data)  # type: ignore[arg-type]

        print(result.to_json())

    except Exception as e:
        error_response = {"error": str(e), "type": type(e).__name__}
        print(json.dumps(error_response), file=sys.stderr)
        sys.exit(1)


def _parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run a task or evaluator via stdin/stdout JSON protocol"
    )
    parser.add_argument(
        "--task",
        "-t",
        help="Name of the task to run",
    )
    parser.add_argument(
        "--evaluator",
        "-e",
        help="Name of the evaluator to run",
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List registered tasks and evaluators",
    )
    return parser.parse_args()


def _list_registered() -> None:
    """Print registered tasks and evaluators."""
    tasks = list_tasks()
    evaluators = list_evaluators()

    print("Registered tasks:")
    for name in tasks:
        print(f"  - {name}")
    if not tasks:
        print("  (none)")

    print("\nRegistered evaluators:")
    for name in evaluators:
        print(f"  - {name}")
    if not evaluators:
        print("  (none)")


def _run_task(name: str, input_data: dict[str, Any]) -> TaskOutput:
    """Execute a registered task."""
    fn = get_task(name)
    if fn is None:
        raise ValueError(f"Unknown task: {name}. Available: {list_tasks()}")

    task_input = TaskInput.from_dict(input_data)

    if getattr(fn, "_is_async", False):
        return asyncio.run(fn(task_input))
    return fn(task_input)


def _run_evaluator(name: str, input_data: dict[str, Any]) -> EvalOutput:
    """Execute a registered evaluator."""
    fn = get_evaluator(name)
    if fn is None:
        raise ValueError(f"Unknown evaluator: {name}. Available: {list_evaluators()}")

    eval_input = EvalInput.from_dict(input_data)

    if getattr(fn, "_is_async", False):
        return asyncio.run(fn(eval_input))
    return fn(eval_input)
