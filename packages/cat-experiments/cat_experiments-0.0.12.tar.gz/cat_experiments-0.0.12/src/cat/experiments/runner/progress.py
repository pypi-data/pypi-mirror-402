"""Progress listener protocol and implementations.

The ProgressListener provides callbacks for monitoring experiment progress.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from ..protocol import ExperimentResult, ExperimentSummary


@runtime_checkable
class ProgressListener(Protocol):
    """Protocol for receiving experiment progress updates.

    The Orchestrator calls these methods at various points during execution
    to report progress. Implementations can use these for progress bars,
    logging, or other monitoring.
    """

    def on_task_completed(
        self,
        index: int,
        total: int,
        result: "ExperimentResult",
    ) -> None:
        """Called when a task completes.

        Args:
            index: Zero-based index of the completed task
            total: Total number of tasks
            result: The task result
        """
        ...

    def on_evaluation_completed(
        self,
        evaluator_name: str,
        index: int,
        total: int,
    ) -> None:
        """Called when an evaluation completes.

        Args:
            evaluator_name: Name of the evaluator
            index: Zero-based index of the completed evaluation
            total: Total number of evaluations for this evaluator
        """
        ...

    def on_experiment_completed(
        self,
        summary: "ExperimentSummary",
    ) -> None:
        """Called when the experiment completes.

        Args:
            summary: Final experiment summary
        """
        ...


class NullProgressListener:
    """No-op progress listener that does nothing.

    Use this when progress reporting is not needed (e.g., in tests
    or when running in quiet mode).
    """

    def on_task_completed(
        self,
        index: int,
        total: int,
        result: "ExperimentResult",
    ) -> None:
        """Do nothing."""
        pass

    def on_evaluation_completed(
        self,
        evaluator_name: str,
        index: int,
        total: int,
    ) -> None:
        """Do nothing."""
        pass

    def on_experiment_completed(
        self,
        summary: "ExperimentSummary",
    ) -> None:
        """Do nothing."""
        pass


__all__ = ["ProgressListener", "NullProgressListener"]
