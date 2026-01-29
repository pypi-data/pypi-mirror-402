"""Protocol definitions for backend adapters.

This module defines the interfaces that backend adapters implement.
These protocols are designed for CLI orchestration and are portable
to Go/Rust implementations.

Architecture Overview:

    CLI Orchestrator
    ├── StorageBackend
    │   ├── load_dataset()
    │   ├── start_experiment()
    │   ├── save_run()           # after task completes
    │   ├── save_evaluation()    # after each evaluator completes
    │   ├── complete_experiment()
    │   └── get_completed_runs()  # for resume
    │
    └── Executor (for task/evaluator execution)
        ├── TaskInput -> task() -> TaskOutput
        └── EvalInput -> evaluator() -> EvalOutput

The StorageBackend protocol is the interface the CLI orchestrator uses
to interact with storage systems (local files, Phoenix, Cat Cafe).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ...protocol import (
    DatasetExample,
    ExperimentConfig,
    ExperimentResult,
    ExperimentSummary,
)


@runtime_checkable
class StorageBackend(Protocol):
    """Protocol for storage backends used by the CLI orchestrator.

    A StorageBackend handles all persistence operations:
    - Loading datasets
    - Streaming experiment results as they complete
    - Supporting resume by tracking completed runs

    This is the interface that would be implemented in Go/Rust
    for the native CLI, or in Python for the prototype.

    Implementations:
    - LocalStorageBackend: File-based storage
    - PhoenixStorageBackend: Phoenix API
    - CatCafeStorageBackend: Cat Cafe API
    """

    # -------------------------------------------------------------------------
    # Dataset loading
    # -------------------------------------------------------------------------

    def load_dataset(
        self,
        *,
        name: str | None = None,
        path: str | None = None,
        version: str | None = None,
    ) -> list[DatasetExample]:
        """Load a dataset from the backend.

        Args:
            name: Dataset name (for remote backends)
            path: File path (for local backend)
            version: Optional version identifier

        Returns:
            List of dataset examples

        Raises:
            FileNotFoundError: If dataset doesn't exist
            ValueError: If neither name nor path provided
        """
        ...

    # -------------------------------------------------------------------------
    # Experiment lifecycle - streaming API
    # -------------------------------------------------------------------------

    def start_experiment(
        self,
        experiment_id: str,
        config: ExperimentConfig,
        examples: list[DatasetExample],
    ) -> None:
        """Called when an experiment starts.

        Initialize storage for this experiment. Called before any
        tasks are executed.

        Args:
            experiment_id: Unique identifier for this experiment
            config: Experiment configuration
            examples: Dataset examples that will be processed
        """
        ...

    def save_run(
        self,
        experiment_id: str,
        result: ExperimentResult,
    ) -> None:
        """Save a run result after task execution completes.

        Called after each task completes, before evaluators run.
        The result contains actual_output but evaluation_scores
        will be empty at this point.

        Args:
            experiment_id: Unique identifier for this experiment
            result: The task result (without evaluation scores)
        """
        ...

    def save_evaluation(
        self,
        experiment_id: str,
        run_id: str,
        evaluator_name: str,
        score: float,
        label: str | None,
        metadata: dict[str, object] | None,
    ) -> None:
        """Save a single evaluation result for a run.

        Called after each evaluator completes for a run. This enables
        streaming evaluation results as they complete.

        Phoenix API: POST v1/experiment_evaluations
        Cat Cafe API: append_evaluation(experiment_id, run_id, payload)

        Args:
            experiment_id: Unique identifier for this experiment
            run_id: The run this evaluation belongs to
            evaluator_name: Name of the evaluator
            score: Evaluation score
            label: Optional categorical label
            metadata: Optional evaluation metadata
        """
        ...

    def complete_experiment(
        self,
        experiment_id: str,
        summary: ExperimentSummary,
    ) -> None:
        """Called when an experiment completes successfully.

        Finalize the experiment - write summary, clean up, etc.

        Args:
            experiment_id: Unique identifier for this experiment
            summary: Final summary statistics
        """
        ...

    def fail_experiment(
        self,
        experiment_id: str,
        error: str,
    ) -> None:
        """Called when an experiment fails.

        Record the failure for debugging/retry.

        Args:
            experiment_id: Unique identifier for this experiment
            error: Error message describing the failure
        """
        ...

    # -------------------------------------------------------------------------
    # Resume support
    # -------------------------------------------------------------------------

    def get_completed_runs(
        self,
        experiment_id: str,
    ) -> set[str] | None:
        """Get the set of completed run_ids for resume.

        Returns None if the experiment doesn't exist (first run).
        Returns empty set if experiment exists but has no completed runs.
        Returns set of run_ids that completed successfully.

        Args:
            experiment_id: Unique identifier for the experiment

        Returns:
            Set of completed run_ids, or None if experiment doesn't exist
        """
        ...


@runtime_checkable
class AsyncStorageBackend(Protocol):
    """Async variant of StorageBackend.

    Same interface but with async methods for backends that benefit
    from async I/O (e.g., HTTP-based backends).
    """

    async def load_dataset(
        self,
        *,
        name: str | None = None,
        path: str | None = None,
        version: str | None = None,
    ) -> list[DatasetExample]: ...

    async def start_experiment(
        self,
        experiment_id: str,
        config: ExperimentConfig,
        examples: list[DatasetExample],
    ) -> None: ...

    async def save_run(
        self,
        experiment_id: str,
        result: ExperimentResult,
    ) -> None: ...

    async def save_evaluation(
        self,
        experiment_id: str,
        run_id: str,
        evaluator_name: str,
        score: float,
        label: str | None,
        metadata: dict[str, object] | None,
    ) -> None: ...

    async def complete_experiment(
        self,
        experiment_id: str,
        summary: ExperimentSummary,
    ) -> None: ...

    async def fail_experiment(
        self,
        experiment_id: str,
        error: str,
    ) -> None: ...

    async def get_completed_runs(
        self,
        experiment_id: str,
    ) -> set[str] | None: ...


__all__ = [
    "StorageBackend",
    "AsyncStorageBackend",
]
