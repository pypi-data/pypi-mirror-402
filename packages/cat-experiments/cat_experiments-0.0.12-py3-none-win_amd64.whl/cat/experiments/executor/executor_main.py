"""Subprocess entry point for executor protocol.

This module implements the subprocess side of the executor protocol.
It reads JSON commands from stdin and writes JSON responses to stdout.

Concurrent Execution:
    The executor processes run_task and run_eval commands concurrently.
    The Go CLI sends multiple commands without waiting for responses,
    and the Python executor processes them in parallel using asyncio.
    Responses include run_id to match with requests.

Usage:
    python -m cat.experiments.executor.executor_main <experiment.py>

Protocol:
    - One JSON object per line (JSON-lines format)
    - Commands: discover, init, run_task, run_eval, shutdown
    - All responses include "__cat__" key with protocol version
    - See docs/executor-protocol.md for full specification
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, TextIO

# Protocol version included in all responses to distinguish from user output
# Integer for simple comparison (e.g., if proto >= 2)
PROTOCOL_VERSION = 1


def _wrap_response(response: dict[str, Any] | list[Any]) -> dict[str, Any] | list[Any]:
    """Add protocol marker to response.

    For dict responses, adds __cat__ key with protocol version.
    For list responses (eval results), wraps in a dict with __cat__ and data keys.
    """
    if isinstance(response, list):
        return {"__cat__": PROTOCOL_VERSION, "data": response}
    else:
        return {"__cat__": PROTOCOL_VERSION, **response}


async def main(experiment_path: str) -> int:
    """Main entry point for subprocess executor.

    Args:
        experiment_path: Path to experiment Python file

    Returns:
        Exit code (0 for success)
    """
    # Set up tracing BEFORE loading experiment file
    # This ensures any instrumentors the user sets up will use our TracerProvider
    try:
        from ..sdk.tracing import setup_executor_tracing

        setup_executor_tracing()
    except ImportError:
        pass  # Tracing extra not installed, skip

    # Load experiment file to register @task/@evaluator
    try:
        load_experiment_file(Path(experiment_path))
    except Exception as e:
        error_response = _wrap_response({"error": f"Failed to load experiment: {e}"})
        sys.stdout.write(json.dumps(error_response) + "\n")
        sys.stdout.flush()
        return 1

    # Create executor (uses registry populated by loading experiment)
    from .executor import InProcessExecutor

    executor = InProcessExecutor()

    # Process commands from stdin with concurrent task execution
    try:
        await process_commands_concurrent(executor, sys.stdin, sys.stdout)
    except Exception as e:
        error_response = _wrap_response({"error": f"Executor error: {e}"})
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


async def process_commands_concurrent(
    executor: Any,
    stdin: TextIO,
    stdout: TextIO,
) -> None:
    """Process JSON commands with concurrent task/eval execution.

    Control commands (discover, init, shutdown) are processed synchronously.
    Task and eval commands are dispatched as concurrent asyncio tasks.
    Responses are written as tasks complete, with run_id for matching.

    Args:
        executor: InProcessExecutor instance
        stdin: Input stream (JSON-lines)
        stdout: Output stream (JSON-lines)
    """
    from ..protocol import EvalInput, InitRequest, TaskInput

    in_flight: set[asyncio.Task[None]] = set()
    write_lock = asyncio.Lock()
    shutdown_event = asyncio.Event()

    async def write_response_locked(response: Any) -> None:
        """Write response with lock to prevent interleaving.

        All responses are wrapped with __cat__ protocol version marker
        to distinguish from user stdout output.
        """
        async with write_lock:
            wrapped = _wrap_response(response)
            stdout.write(json.dumps(wrapped) + "\n")
            stdout.flush()

    async def handle_task(task_input: TaskInput) -> None:
        """Execute a task and write the response."""
        try:
            result = await executor.run_task(task_input)
            await write_response_locked(result.to_dict())
        except Exception as e:
            await write_response_locked(
                {
                    "run_id": task_input.run_id or task_input.id,
                    "error": str(e),
                }
            )

    async def handle_eval(eval_input: EvalInput, evaluator: str) -> None:
        """Execute a single evaluator and write the response."""
        try:
            result = await executor.run_eval(eval_input, evaluator)
            # Write single result
            await write_response_locked(result.to_dict())
        except Exception as e:
            run_id = eval_input.example.get("run_id", "")
            await write_response_locked(
                {
                    "run_id": run_id,
                    "evaluator": evaluator,
                    "score": 0.0,
                    "error": str(e),
                }
            )

    async def read_commands() -> None:
        """Read and dispatch commands from stdin."""
        loop = asyncio.get_event_loop()

        while not shutdown_event.is_set():
            # Read line in executor to not block the event loop
            line = await loop.run_in_executor(None, stdin.readline)
            if not line:
                break

            line = line.strip()
            if not line:
                continue

            try:
                msg = json.loads(line)
            except json.JSONDecodeError as e:
                await write_response_locked({"error": f"Invalid JSON: {e}"})
                continue

            cmd = msg.get("cmd")

            try:
                if cmd == "discover":
                    result = await executor.discover()
                    await write_response_locked(result.to_dict())

                elif cmd == "init":
                    request = InitRequest(
                        max_workers=msg.get("max_workers", 1),
                        params=msg.get("params", {}),
                    )
                    result = await executor.init(request)
                    await write_response_locked(result.to_dict())

                elif cmd == "run_task":
                    task_input = TaskInput.from_dict(msg["input"])
                    task = asyncio.create_task(handle_task(task_input))
                    in_flight.add(task)
                    task.add_done_callback(in_flight.discard)

                elif cmd == "run_eval":
                    eval_input = EvalInput.from_dict(msg["input"])
                    evaluator = msg.get("evaluator", "")
                    task = asyncio.create_task(handle_eval(eval_input, evaluator))
                    in_flight.add(task)
                    task.add_done_callback(in_flight.discard)

                elif cmd == "shutdown":
                    # Wait for all in-flight tasks
                    if in_flight:
                        await asyncio.gather(*in_flight, return_exceptions=True)
                    result = await executor.shutdown()
                    await write_response_locked(result.to_dict())
                    shutdown_event.set()
                    break

                else:
                    await write_response_locked({"error": f"Unknown command: {cmd}"})

            except Exception as e:
                await write_response_locked({"error": str(e)})

    await read_commands()

    # Ensure all tasks complete
    if in_flight:
        await asyncio.gather(*in_flight, return_exceptions=True)


def write_response(stdout: TextIO, response: Any) -> None:
    """Write JSON response to stdout."""
    stdout.write(json.dumps(response) + "\n")
    stdout.flush()


def cli_main() -> None:
    """CLI entry point."""
    if len(sys.argv) < 2:
        print(
            "Usage: python -m cat.experiments.executor.executor_main <experiment.py>",
            file=sys.stderr,
        )
        sys.exit(1)

    experiment_path = sys.argv[1]
    exit_code = asyncio.run(main(experiment_path))
    sys.exit(exit_code)


if __name__ == "__main__":
    cli_main()
