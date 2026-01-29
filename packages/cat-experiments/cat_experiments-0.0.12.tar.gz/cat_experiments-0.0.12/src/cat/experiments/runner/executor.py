"""Executor protocol and implementations for task/evaluator execution.

The Executor protocol defines how the orchestrator communicates with
task/evaluator execution backends. This enables:
- In-process execution (Python, for development/testing)
- Subprocess execution (any language via JSON-lines protocol)

Protocol Commands:
- discover() -> DiscoverResult: Get experiment metadata
- init(request) -> InitResult: Initialize with config
- run_task(input) -> TaskResult: Execute a single task
- run_eval(input, evaluators) -> list[EvalResult]: Execute evaluators on one input
- shutdown() -> ShutdownResult: Clean up resources

Flow Control:
The orchestrator uses windowed dispatch - it tracks in-flight tasks and
only sends new work when slots are available (in_flight < max_workers).
The executor just processes what it receives; backpressure is handled
by the orchestrator.
"""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable

from ..protocol import (
    DiscoverResult,
    EvalInput,
    EvalOutput,
    EvalResult,
    InitRequest,
    InitResult,
    ShutdownResult,
    TaskInput,
    TaskOutput,
    TaskResult,
)


@runtime_checkable
class Executor(Protocol):
    """Protocol for executing tasks and evaluators.

    The orchestrator sends single tasks/evals and manages parallelism via
    windowed dispatch. The executor processes what it receives.
    """

    async def discover(self) -> DiscoverResult:
        """Discover experiment metadata.

        Returns information about the registered task and evaluators,
        including names, default params, etc.
        """
        ...

    async def init(self, request: InitRequest) -> InitResult:
        """Initialize the executor.

        Args:
            request: Configuration including max_workers and params

        Returns:
            InitResult indicating success or failure
        """
        ...

    async def run_task(self, input: TaskInput) -> TaskResult:
        """Execute a single task.

        Args:
            input: The task input

        Returns:
            TaskResult with output, metadata, and optional error
        """
        ...

    async def run_eval(
        self,
        input: EvalInput,
        evaluator: str,
    ) -> EvalResult:
        """Execute a single evaluator on an input.

        Args:
            input: The eval input
            evaluator: Name of the evaluator to run.

        Returns:
            EvalResult for the evaluator
        """
        ...

    async def shutdown(self) -> ShutdownResult:
        """Shutdown the executor and clean up resources."""
        ...


class InProcessExecutor:
    """Executes tasks and evaluators in-process using asyncio.

    This executor:
    - Discovers registered @task and @evaluator functions
    - Handles sync/async function detection automatically
    - Processes single items (orchestrator handles parallelism)

    For subprocess-based execution, see SubprocessExecutor (future).
    """

    def __init__(
        self,
        task_fn: Callable[..., Any] | None = None,
        evaluator_fns: list[Callable[..., Any]] | None = None,
    ) -> None:
        """Initialize InProcessExecutor.

        Args:
            task_fn: Optional task function (if not using registry)
            evaluator_fns: Optional evaluator functions (if not using registry)
        """
        self._task_fn = task_fn
        self._evaluator_fns: dict[str, Callable[..., Any]] = {}
        if evaluator_fns:
            for fn in evaluator_fns:
                name = getattr(fn, "__name__", f"evaluator_{len(self._evaluator_fns)}")
                self._evaluator_fns[name] = fn
        self._max_workers = 1
        self._params: dict[str, Any] = {}
        self._initialized = False

    async def discover(self) -> DiscoverResult:
        """Discover registered task and evaluators."""
        from ..sdk.decorators import list_evaluators, list_tasks

        task_names = list_tasks()
        evaluator_names = list_evaluators()

        # Get task name
        task_name: str | None = None
        if self._task_fn:
            task_name = getattr(self._task_fn, "__name__", "task")
        elif task_names:
            task_name = task_names[0]

        # Get evaluator names
        eval_names: list[str] = []
        if self._evaluator_fns:
            eval_names = list(self._evaluator_fns.keys())
        else:
            eval_names = evaluator_names

        return DiscoverResult(
            protocol_version="1.0",
            task=task_name,
            evaluators=eval_names,
            params=self._params,
        )

    async def init(self, request: InitRequest) -> InitResult:
        """Initialize the executor with configuration."""
        self._max_workers = request.max_workers
        self._params = dict(request.params)
        self._initialized = True
        return InitResult(ok=True)

    async def run_task(self, input: TaskInput) -> TaskResult:
        """Execute a single task."""
        if not self._initialized:
            await self.init(InitRequest(max_workers=1))

        # Get task function
        task_fn = self._task_fn
        if task_fn is None:
            from ..sdk.decorators import get_task, list_tasks

            task_names = list_tasks()
            if not task_names:
                return TaskResult(
                    run_id=input.run_id or input.id,
                    error="No task registered",
                )
            task_fn = get_task(task_names[0])

        if task_fn is None:
            return TaskResult(
                run_id=input.run_id or input.id,
                error="Task function not found",
            )

        return await self._execute_single_task(task_fn, input)

    async def run_eval(
        self,
        input: EvalInput,
        evaluator: str,
    ) -> EvalResult:
        """Execute a single evaluator on an input."""
        if not self._initialized:
            await self.init(InitRequest(max_workers=1))

        # Get evaluator function
        eval_fn: Callable[..., Any] | None = None

        if self._evaluator_fns and evaluator in self._evaluator_fns:
            eval_fn = self._evaluator_fns[evaluator]
        else:
            from ..sdk.decorators import get_evaluator

            eval_fn = get_evaluator(evaluator)

        if not eval_fn:
            run_id = input.example.get("run_id") or input.example.get("id", "")
            return EvalResult(
                run_id=run_id,
                evaluator=evaluator,
                score=0.0,
                error=f"Evaluator '{evaluator}' not found",
            )

        # Get run_id from input
        run_id = input.example.get("run_id") or input.example.get("id", "")

        # Execute the evaluator
        return await self._execute_single_eval(run_id, evaluator, eval_fn, input)

    async def shutdown(self) -> ShutdownResult:
        """Shutdown the executor."""
        self._initialized = False
        return ShutdownResult(ok=True)

    # -------------------------------------------------------------------------
    # Internal execution helpers
    # -------------------------------------------------------------------------

    async def _execute_single_task(
        self,
        task_fn: Callable[..., Any],
        task_input: TaskInput,
    ) -> TaskResult:
        """Execute a single task, handling sync/async and timing."""
        run_id = task_input.run_id or task_input.id
        started_at = datetime.now(timezone.utc)

        try:
            if inspect.iscoroutinefunction(task_fn):
                result = await task_fn(task_input)
            else:
                result = await asyncio.to_thread(task_fn, task_input)

            completed_at = datetime.now(timezone.utc)
            execution_time_ms = (completed_at - started_at).total_seconds() * 1000

            # Handle TaskOutput returns
            if isinstance(result, TaskOutput):
                metadata = dict(result.metadata or {})
                metadata["started_at"] = started_at.isoformat()
                metadata["completed_at"] = completed_at.isoformat()
                metadata["execution_time_ms"] = execution_time_ms
                return TaskResult(
                    run_id=run_id,
                    output=result.output,
                    metadata=metadata,
                    error=result.error,
                )

            return TaskResult(
                run_id=run_id,
                output=result,
                metadata={
                    "started_at": started_at.isoformat(),
                    "completed_at": completed_at.isoformat(),
                    "execution_time_ms": execution_time_ms,
                },
            )

        except Exception as e:
            completed_at = datetime.now(timezone.utc)
            execution_time_ms = (completed_at - started_at).total_seconds() * 1000
            return TaskResult(
                run_id=run_id,
                metadata={
                    "started_at": started_at.isoformat(),
                    "completed_at": completed_at.isoformat(),
                    "execution_time_ms": execution_time_ms,
                },
                error=str(e),
            )

    async def _execute_single_eval(
        self,
        run_id: str,
        eval_name: str,
        eval_fn: Callable[..., Any],
        eval_input: EvalInput,
    ) -> EvalResult:
        """Execute a single evaluator, handling sync/async."""
        started_at = datetime.now(timezone.utc)

        try:
            if inspect.iscoroutinefunction(eval_fn):
                result = await eval_fn(eval_input)
            else:
                result = await asyncio.to_thread(eval_fn, eval_input)

            completed_at = datetime.now(timezone.utc)
            execution_time_ms = (completed_at - started_at).total_seconds() * 1000

            # Handle different return types
            if isinstance(result, EvalOutput):
                metadata = dict(result.metadata or {})
                metadata["started_at"] = started_at.isoformat()
                metadata["completed_at"] = completed_at.isoformat()
                metadata["execution_time_ms"] = execution_time_ms
                return EvalResult(
                    run_id=run_id,
                    evaluator=eval_name,
                    score=result.score,
                    label=result.label,
                    metadata=metadata,
                    explanation=result.explanation,
                )
            else:
                # Assume result is a score
                return EvalResult(
                    run_id=run_id,
                    evaluator=eval_name,
                    score=float(result),
                    metadata={
                        "started_at": started_at.isoformat(),
                        "completed_at": completed_at.isoformat(),
                        "execution_time_ms": execution_time_ms,
                    },
                )

        except Exception as e:
            completed_at = datetime.now(timezone.utc)
            execution_time_ms = (completed_at - started_at).total_seconds() * 1000
            return EvalResult(
                run_id=run_id,
                evaluator=eval_name,
                score=0.0,
                metadata={
                    "started_at": started_at.isoformat(),
                    "completed_at": completed_at.isoformat(),
                    "execution_time_ms": execution_time_ms,
                },
                error=str(e),
            )

    # -------------------------------------------------------------------------
    # Legacy API (for backward compatibility with existing orchestrator)
    # -------------------------------------------------------------------------

    async def execute_task(
        self,
        task_fn: Callable[..., Any],
        input: TaskInput,
    ) -> TaskOutput:
        """Execute a single task (legacy API).

        This method is kept for backward compatibility with the existing
        orchestrator. New code should use run_task() instead.
        """
        self._task_fn = task_fn
        result = await self._execute_single_task(task_fn, input)
        return TaskOutput(
            output=result.output,
            metadata=result.metadata,
            error=result.error,
        )

    async def execute_evaluator(
        self,
        eval_fn: Callable[..., Any],
        input: EvalInput,
    ) -> EvalOutput:
        """Execute a single evaluator (legacy API).

        This method is kept for backward compatibility with the existing
        orchestrator. New code should use run_eval() instead.
        """
        run_id = input.example.get("run_id") or input.example.get("id", "")
        eval_name = getattr(eval_fn, "__name__", "evaluator")
        result = await self._execute_single_eval(run_id, eval_name, eval_fn, input)

        # Include error in metadata for legacy API compatibility
        metadata = dict(result.metadata or {})
        if result.error:
            metadata["error"] = result.error

        return EvalOutput(
            score=result.score,
            label=result.label,
            metadata=metadata,
        )


__all__ = ["Executor", "InProcessExecutor"]
