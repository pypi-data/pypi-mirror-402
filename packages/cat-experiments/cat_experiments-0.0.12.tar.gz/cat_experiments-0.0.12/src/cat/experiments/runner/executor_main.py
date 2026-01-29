"""Subprocess entry point for executor protocol.

This module implements the subprocess side of the executor protocol.
It reads JSON commands from stdin and writes JSON responses to stdout.

Usage:
    python -m cat.experiments.runner.executor_main <experiment.py>

Protocol:
    - One JSON object per line (JSON-lines format)
    - Commands: discover, init, run_task, run_eval, shutdown
    - See docs/executor-protocol.md for full specification
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, TextIO


async def main(experiment_path: str) -> int:
    """Main entry point for subprocess executor.

    Args:
        experiment_path: Path to experiment Python file

    Returns:
        Exit code (0 for success)
    """
    # Load experiment file to register @task/@evaluator
    try:
        load_experiment_file(Path(experiment_path))
    except Exception as e:
        error_response = {"error": f"Failed to load experiment: {e}"}
        sys.stdout.write(json.dumps(error_response) + "\n")
        sys.stdout.flush()
        return 1

    # Create executor (uses registry populated by loading experiment)
    from .executor import InProcessExecutor

    executor = InProcessExecutor()

    # Process commands from stdin
    try:
        await process_commands(executor, sys.stdin, sys.stdout)
    except Exception as e:
        error_response = {"error": f"Executor error: {e}"}
        sys.stdout.write(json.dumps(error_response) + "\n")
        sys.stdout.flush()
        return 1

    return 0


def load_experiment_file(path: Path) -> Any:
    """Load experiment file as a Python module.

    This executes the module, which triggers @task and @evaluator
    decorators to register functions in the global registry.
    """
    import importlib.util

    from ..sdk.decorators import clear_registry

    # Clear any previous registrations
    clear_registry()

    if not path.exists():
        raise FileNotFoundError(f"Experiment file not found: {path}")

    # Load the module
    spec = importlib.util.spec_from_file_location("experiment", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load experiment file: {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["experiment"] = module
    spec.loader.exec_module(module)

    return module


async def process_commands(
    executor: Any,
    stdin: TextIO,
    stdout: TextIO,
) -> None:
    """Process JSON commands from stdin, write responses to stdout.

    Args:
        executor: InProcessExecutor instance
        stdin: Input stream (JSON-lines)
        stdout: Output stream (JSON-lines)
    """
    from ..protocol import EvalInput, InitRequest, TaskInput

    for line in stdin:
        line = line.strip()
        if not line:
            continue

        try:
            msg = json.loads(line)
        except json.JSONDecodeError as e:
            write_response(stdout, {"error": f"Invalid JSON: {e}"})
            continue

        cmd = msg.get("cmd")

        try:
            if cmd == "discover":
                result = await executor.discover()
                write_response(stdout, result.to_dict())

            elif cmd == "init":
                request = InitRequest(
                    max_workers=msg.get("max_workers", 1),
                    params=msg.get("params", {}),
                )
                result = await executor.init(request)
                write_response(stdout, result.to_dict())

            elif cmd == "run_task":
                task_input = TaskInput.from_dict(msg["input"])
                result = await executor.run_task(task_input)
                write_response(stdout, result.to_dict())

            elif cmd == "run_eval":
                eval_input = EvalInput.from_dict(msg["input"])
                evaluator = msg.get("evaluator", "")
                result = await executor.run_eval(eval_input, evaluator)
                write_response(stdout, result.to_dict())

            elif cmd == "shutdown":
                result = await executor.shutdown()
                write_response(stdout, result.to_dict())
                break  # Exit loop after shutdown

            else:
                write_response(stdout, {"error": f"Unknown command: {cmd}"})

        except Exception as e:
            write_response(stdout, {"error": str(e)})


def write_response(stdout: TextIO, response: Any) -> None:
    """Write JSON response to stdout."""
    stdout.write(json.dumps(response) + "\n")
    stdout.flush()


def cli_main() -> None:
    """CLI entry point."""
    if len(sys.argv) < 2:
        print(
            "Usage: python -m cat.experiments.runner.executor_main <experiment.py>", file=sys.stderr
        )
        sys.exit(1)

    experiment_path = sys.argv[1]
    exit_code = asyncio.run(main(experiment_path))
    sys.exit(exit_code)


if __name__ == "__main__":
    cli_main()
