"""Orchestrator for experiment execution.

The Orchestrator coordinates experiment execution:
- Dataset preparation (preview, repetitions, run_selection)
- Task execution with parallelism (via Executor)
- Evaluator execution (via Executor)
- Backend persistence (via StorageBackend)
- Progress reporting (via ProgressListener)
- Resume support

The Orchestrator uses the Executor protocol for task/evaluator execution.
It does not know about task/evaluator functions directly - the Executor
discovers and manages those (either via registry or subprocess protocol).
"""

from __future__ import annotations

import asyncio
import hashlib
import random
import time
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from ..protocol import (
    DatasetExample,
    EvalInput,
    ExperimentConfig,
    ExperimentResult,
    ExperimentSummary,
    InitRequest,
    TaskInput,
    TaskResult,
    TestCase,
)
from .executor import Executor, InProcessExecutor
from .progress import NullProgressListener, ProgressListener

if TYPE_CHECKING:
    from .adapters.protocol import StorageBackend


class Orchestrator:
    """Coordinates experiment execution with parallelism, persistence, and resume.

    The Orchestrator is the main entry point for running experiments. It:
    - Discovers available task/evaluators via the Executor
    - Prepares the dataset (preview selection, repetition expansion)
    - Executes tasks in parallel via the Executor
    - Persists results via the StorageBackend
    - Reports progress via the ProgressListener
    - Supports resuming previous experiments

    Example:
        # Executor discovers task/evaluators from registry or subprocess
        executor = InProcessExecutor(task_fn=my_task, evaluator_fns=[my_eval])
        orchestrator = Orchestrator(
            backend=LocalStorageBackend(),
            executor=executor,
            progress=TqdmProgressListener(),
        )
        summary = await orchestrator.run(
            dataset=examples,
            config=ExperimentConfig(name="my-experiment"),
        )
    """

    def __init__(
        self,
        backend: "StorageBackend | None" = None,
        executor: Executor | None = None,
        progress: ProgressListener | None = None,
    ) -> None:
        """Initialize the Orchestrator.

        Args:
            backend: Storage backend for persistence. If None, results are not persisted.
            executor: Executor for running tasks/evaluators. Defaults to InProcessExecutor.
            progress: Progress listener for monitoring. Defaults to NullProgressListener.
        """
        self._backend = backend
        self._executor: Executor = executor or InProcessExecutor()
        self._progress: ProgressListener = progress or NullProgressListener()

    async def run(
        self,
        dataset: list[DatasetExample],
        config: ExperimentConfig | None = None,
        experiment_id: str | None = None,
        run_selection: Mapping[str, Iterable[int]] | None = None,
        resume: str | None = None,
    ) -> ExperimentSummary:
        """Run an experiment.

        The task and evaluators are discovered from the Executor via the
        discover() protocol method. The Executor is responsible for knowing
        which task/evaluators to run (via registry, constructor args, or
        subprocess discovery).

        Args:
            dataset: List of dataset examples to process
            config: Experiment configuration
            experiment_id: Optional custom experiment ID
            run_selection: Optional mapping of example_id -> repetition numbers to run
            resume: Optional experiment ID to resume (skips completed runs)

        Returns:
            ExperimentSummary with results and statistics

        Raises:
            ValueError: If config validation fails or resume without backend
            RuntimeError: If all tasks fail
        """
        # Default config
        if config is None:
            config = ExperimentConfig(name="Experiment")

        # Validate config
        if config.max_workers < 1:
            raise ValueError("max_workers must be >= 1")
        if config.repetitions < 1:
            raise ValueError("repetitions must be >= 1")

        # Handle resume
        if resume is not None:
            if self._backend is None:
                raise ValueError("resume requires a storage backend")
            experiment_id = resume
            completed_runs = self._backend.get_completed_runs(resume)

            if completed_runs is None:
                # Experiment not found, start fresh
                completed_runs = set()
            else:
                # Load stored examples for stable IDs
                # Note: load_experiment is optional and only on LocalStorageBackend
                if hasattr(self._backend, "load_experiment"):
                    loaded = self._backend.load_experiment(resume)  # type: ignore[union-attr]
                    if loaded is not None:
                        _, stored_examples, _ = loaded
                        if stored_examples:
                            dataset = stored_examples

            # Build run_selection to skip completed runs
            if completed_runs and run_selection is None:
                run_selection = self._build_resume_selection(
                    dataset, completed_runs, config.repetitions
                )

        # Generate experiment ID if not provided
        if experiment_id is None:
            experiment_id = self._generate_experiment_id()

        # Prepare dataset (preview + repetitions)
        test_cases = self._prepare_test_cases(
            dataset=dataset,
            config=config,
            run_selection=run_selection,
        )

        # Early exit if no work to do
        if not test_cases:
            started_at = datetime.now(timezone.utc)
            return ExperimentSummary(
                total_examples=0,
                successful_examples=0,
                failed_examples=0,
                average_scores={},
                total_execution_time_ms=0.0,
                experiment_id=experiment_id,
                config=config,
                started_at=started_at,
                completed_at=started_at,
            )

        started_at = datetime.now(timezone.utc)
        results: list[ExperimentResult] = []

        try:
            # Initialize executor with config
            await self._executor.init(
                InitRequest(max_workers=config.max_workers, params=config.params)
            )

            # Start experiment in backend
            if self._backend is not None and resume is None:
                examples = [tc.example for tc in test_cases]
                # De-duplicate examples (repetitions share same example)
                seen_ids: set[str] = set()
                unique_examples: list[DatasetExample] = []
                for ex in examples:
                    if ex.id and ex.id not in seen_ids:
                        seen_ids.add(ex.id)
                        unique_examples.append(ex)
                self._backend.start_experiment(experiment_id, config, unique_examples)

            # Execute tasks with windowed dispatch
            results = await self._execute_tasks(
                test_cases=test_cases,
                config=config,
                experiment_id=experiment_id,
            )

            # Execute evaluators on successful results
            # The executor knows which evaluators to run
            await self._execute_evaluators(
                results=results,
                experiment_id=experiment_id,
                config=config,
            )

            # Aggregate scores placeholder (aggregate evaluators not yet in protocol)
            aggregate_scores: dict[str, float] = {}
            aggregate_metadata: dict[str, dict[str, Any]] = {}

            completed_at = datetime.now(timezone.utc)

            # Build summary
            summary = self._build_summary(
                results=results,
                config=config,
                experiment_id=experiment_id,
                started_at=started_at,
                completed_at=completed_at,
                aggregate_scores=aggregate_scores,
                aggregate_metadata=aggregate_metadata,
            )

            # Check for total failure
            if summary.total_examples > 0 and summary.successful_examples == 0:
                error_msg = next((r.error for r in results if r.error), "all tasks failed")
                if self._backend is not None:
                    self._backend.fail_experiment(experiment_id, error_msg)
                raise RuntimeError(f"Experiment failed: {error_msg}")

            # Complete experiment in backend
            if self._backend is not None:
                self._backend.complete_experiment(experiment_id, summary)

            # Report completion
            self._progress.on_experiment_completed(summary)

            return summary

        except RuntimeError:
            # RuntimeError from total failure check already called fail_experiment
            raise
        except Exception as e:
            # Fail experiment in backend for unexpected errors
            if self._backend is not None:
                self._backend.fail_experiment(experiment_id, str(e))
            raise

    async def _execute_tasks(
        self,
        test_cases: list[TestCase],
        config: ExperimentConfig,
        experiment_id: str,
    ) -> list[ExperimentResult]:
        """Execute tasks with windowed dispatch.

        Uses the executor protocol with backpressure:
        - Send up to max_workers tasks
        - Wait for results before sending more
        - This bounds memory and provides natural backpressure
        """
        total = len(test_cases)
        results: list[ExperimentResult] = []
        results_by_run_id: dict[str, ExperimentResult] = {}
        test_case_by_run_id: dict[str, tuple[int, TestCase]] = {}

        # Build all task inputs upfront
        pending_inputs: list[tuple[int, TestCase, TaskInput]] = []
        for index, test_case in enumerate(test_cases):
            task_input = TaskInput.from_dataset_example(
                test_case.example,
                experiment_id=experiment_id,
                run_id=test_case.run_id,
                repetition_number=test_case.repetition_number,
                params=config.params,
            )
            pending_inputs.append((index, test_case, task_input))
            test_case_by_run_id[test_case.run_id] = (index, test_case)

        # Track in-flight tasks
        in_flight: dict[str, asyncio.Task[TaskResult]] = {}
        pending_iter = iter(pending_inputs)
        completed_count = 0

        async def send_task(index: int, test_case: TestCase, task_input: TaskInput) -> TaskResult:
            """Execute a single task via the executor."""
            return await self._executor.run_task(task_input)

        # Fill initial window
        for _ in range(min(config.max_workers, len(pending_inputs))):
            try:
                index, test_case, task_input = next(pending_iter)
                coro = send_task(index, test_case, task_input)
                in_flight[test_case.run_id] = asyncio.create_task(coro)
            except StopIteration:
                break

        # Process results as they complete, refill window
        while in_flight:
            # Wait for any task to complete
            done, _ = await asyncio.wait(
                in_flight.values(),
                return_when=asyncio.FIRST_COMPLETED,
            )

            for completed_task in done:
                # Find which run_id completed
                completed_run_id: str | None = None
                for run_id, t in in_flight.items():
                    if t is completed_task:
                        completed_run_id = run_id
                        break

                if completed_run_id is None:
                    continue

                # Remove from in-flight
                del in_flight[completed_run_id]

                # Get result
                task_result = completed_task.result()
                index, test_case = test_case_by_run_id[completed_run_id]

                # Build ExperimentResult from TaskResult
                result = self._build_result_from_task_result(test_case, task_result, config)
                results_by_run_id[completed_run_id] = result

                # Persist
                if self._backend is not None:
                    self._backend.save_run(experiment_id, result)

                # Report progress
                completed_count += 1
                self._progress.on_task_completed(completed_count - 1, total, result)

                # Refill window
                try:
                    next_index, next_test_case, next_task_input = next(pending_iter)
                    coro = send_task(next_index, next_test_case, next_task_input)
                    in_flight[next_test_case.run_id] = asyncio.create_task(coro)
                except StopIteration:
                    pass  # No more tasks to send

        # Return results in original order
        for index, test_case, _ in pending_inputs:
            results.append(results_by_run_id[test_case.run_id])

        return results

    async def _execute_evaluators(
        self,
        results: list[ExperimentResult],
        experiment_id: str,
        config: ExperimentConfig,
    ) -> None:
        """Execute evaluators on all results with windowed dispatch.

        Uses the executor protocol with backpressure:
        - Send up to max_workers eval requests
        - Wait for results before sending more

        Each (result, evaluator) pair is sent as a separate job for proper
        tracing and parallelization.
        """
        # Filter out failed tasks
        successful_results = [r for r in results if not r.error]
        if not successful_results:
            return

        # Discover evaluators from executor
        discovery = await self._executor.discover()
        evaluators = discovery.evaluators
        if not evaluators:
            return

        # Build all eval jobs: one per (result, evaluator) pair
        # Each job is (ExperimentResult, EvalInput, evaluator_name)
        eval_jobs: list[tuple[ExperimentResult, EvalInput, str]] = []
        for result in successful_results:
            eval_input = EvalInput(
                example={
                    "id": result.example_id,
                    "run_id": result.run_id,
                    "input": result.input_data,
                    "output": result.output,
                },
                actual_output=result.actual_output,
                expected_output=result.output,
                task_metadata=result.metadata,
            )
            for evaluator in evaluators:
                eval_jobs.append((result, eval_input, evaluator))

        total_evals = len(eval_jobs)
        eval_index = 0

        # Track in-flight evals by unique key (run_id:evaluator)
        in_flight: dict[str, asyncio.Task[tuple[ExperimentResult, Any]]] = {}
        pending_iter = iter(eval_jobs)

        async def send_eval(
            result: ExperimentResult, eval_input: EvalInput, evaluator: str
        ) -> tuple[ExperimentResult, Any]:
            """Execute a single evaluator for a single result."""
            eval_result = await self._executor.run_eval(eval_input, evaluator)
            return (result, eval_result)

        def make_job_key(run_id: str, evaluator: str) -> str:
            """Create unique key for an eval job."""
            return f"{run_id}:{evaluator}"

        # Fill initial window
        for _ in range(min(config.max_workers, len(eval_jobs))):
            try:
                result, eval_input, evaluator = next(pending_iter)
                coro = send_eval(result, eval_input, evaluator)
                job_key = make_job_key(result.run_id, evaluator)
                in_flight[job_key] = asyncio.create_task(coro)
            except StopIteration:
                break

        # Process results as they complete, refill window
        while in_flight:
            # Wait for any eval to complete
            done, _ = await asyncio.wait(
                in_flight.values(),
                return_when=asyncio.FIRST_COMPLETED,
            )

            for completed_task in done:
                # Find which job_key completed
                completed_key: str | None = None
                for job_key, t in in_flight.items():
                    if t is completed_task:
                        completed_key = job_key
                        break

                if completed_key is None:
                    continue

                # Remove from in-flight
                del in_flight[completed_key]

                # Get result
                result, eval_result = completed_task.result()
                evaluator_name = eval_result.evaluator

                # Store in result
                result.evaluation_scores[evaluator_name] = eval_result.score
                if eval_result.label or eval_result.metadata:
                    meta: dict[str, Any] = dict(eval_result.metadata or {})
                    if eval_result.label:
                        meta["label"] = eval_result.label
                    result.evaluator_metadata[evaluator_name] = meta

                # Persist
                if self._backend is not None:
                    self._backend.save_evaluation(
                        experiment_id=experiment_id,
                        run_id=result.run_id,
                        evaluator_name=evaluator_name,
                        score=eval_result.score,
                        label=eval_result.label,
                        metadata=eval_result.metadata,
                    )

                # Report progress
                self._progress.on_evaluation_completed(evaluator_name, eval_index, total_evals)
                eval_index += 1

                # Refill window
                try:
                    next_result, next_eval_input, next_evaluator = next(pending_iter)
                    coro = send_eval(next_result, next_eval_input, next_evaluator)
                    job_key = make_job_key(next_result.run_id, next_evaluator)
                    in_flight[job_key] = asyncio.create_task(coro)
                except StopIteration:
                    pass  # No more evals to send

    def _prepare_test_cases(
        self,
        dataset: list[DatasetExample],
        config: ExperimentConfig,
        run_selection: Mapping[str, Iterable[int]] | None,
    ) -> list[TestCase]:
        """Prepare test cases from dataset with preview and repetitions."""
        examples = list(dataset)

        # Apply preview selection
        if config.preview_examples is not None and config.preview_examples < len(examples):
            rng = random.Random(config.preview_seed)
            examples = rng.sample(examples, config.preview_examples)

        # Build test cases with repetitions
        test_cases: list[TestCase] = []

        for example in examples:
            example_id = example.id or ""

            for rep in range(1, config.repetitions + 1):
                # Check run_selection filter
                if run_selection is not None:
                    if example_id not in run_selection:
                        continue
                    allowed_reps = list(run_selection[example_id])
                    if rep not in allowed_reps:
                        continue

                test_cases.append(
                    TestCase(
                        example=example,
                        repetition_number=rep,
                        params=config.params,
                    )
                )

        return test_cases

    def _build_result_from_task_result(
        self,
        test_case: TestCase,
        task_result: TaskResult,
        config: ExperimentConfig,
    ) -> ExperimentResult:
        """Build ExperimentResult from TaskResult (new protocol)."""
        metadata = dict(task_result.metadata or {})

        # Extract timing
        started_at = None
        completed_at = None
        execution_time_ms = None

        if "started_at" in metadata:
            started_at = datetime.fromisoformat(metadata["started_at"])
        if "completed_at" in metadata:
            completed_at = datetime.fromisoformat(metadata["completed_at"])
        if "execution_time_ms" in metadata:
            execution_time_ms = metadata["execution_time_ms"]

        return ExperimentResult(
            example_id=test_case.example_id,
            run_id=test_case.run_id,
            repetition_number=test_case.repetition_number,
            started_at=started_at,
            completed_at=completed_at,
            input_data=dict(test_case.example.input),
            output=dict(test_case.example.output),
            actual_output=task_result.output,
            evaluation_scores={},
            evaluator_metadata={},
            metadata=metadata,
            error=task_result.error,
            execution_time_ms=execution_time_ms,
        )

    def _build_summary(
        self,
        results: list[ExperimentResult],
        config: ExperimentConfig,
        experiment_id: str,
        started_at: datetime,
        completed_at: datetime,
        aggregate_scores: dict[str, float],
        aggregate_metadata: dict[str, dict[str, Any]],
    ) -> ExperimentSummary:
        """Build experiment summary from results."""
        total_examples = len(results)
        successful_examples = len([r for r in results if not r.error])
        failed_examples = total_examples - successful_examples

        # Calculate average scores
        average_scores: dict[str, float] = {}
        if results:
            all_metric_names: set[str] = set()
            for result in results:
                if not result.error:
                    all_metric_names.update(result.evaluation_scores.keys())

            for metric_name in all_metric_names:
                scores = [
                    r.evaluation_scores.get(metric_name, 0.0)
                    for r in results
                    if not r.error and metric_name in r.evaluation_scores
                ]
                if scores:
                    average_scores[metric_name] = sum(scores) / len(scores)

        # Calculate total execution time
        total_execution_time_ms = sum(r.execution_time_ms or 0.0 for r in results)

        return ExperimentSummary(
            total_examples=total_examples,
            successful_examples=successful_examples,
            failed_examples=failed_examples,
            average_scores=average_scores,
            aggregate_scores=aggregate_scores,
            aggregate_metadata=aggregate_metadata,
            total_execution_time_ms=total_execution_time_ms,
            experiment_id=experiment_id,
            config=config,
            started_at=started_at,
            completed_at=completed_at,
        )

    def _build_resume_selection(
        self,
        dataset: list[DatasetExample],
        completed_runs: set[str],
        repetitions: int,
    ) -> dict[str, list[int]]:
        """Build run_selection to skip completed runs."""
        selection: dict[str, list[int]] = {}

        for example in dataset:
            example_id = example.id or ""
            incomplete_reps: list[int] = []

            for rep in range(1, repetitions + 1):
                run_id = f"{example_id}#{rep}"
                if run_id not in completed_runs:
                    incomplete_reps.append(rep)

            if incomplete_reps:
                selection[example_id] = incomplete_reps

        return selection

    def _generate_experiment_id(self) -> str:
        """Generate a unique experiment ID."""
        timestamp = int(time.time())
        hash_input = f"{timestamp}-{random.random()}"
        hash_suffix = hashlib.md5(hash_input.encode()).hexdigest()[:12]
        return f"exp_{hash_suffix}_{timestamp}"


__all__ = ["Orchestrator"]
