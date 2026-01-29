"""Progress listener implementations for CLI.

Provides tqdm-based progress bars for experiment monitoring.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tqdm import tqdm

from ..progress import ProgressListener

if TYPE_CHECKING:
    from ...protocol import ExperimentResult, ExperimentSummary


class TqdmProgressListener:
    """Progress listener that displays tqdm progress bars.

    Creates separate progress bars for tasks and evaluations.
    """

    def __init__(self, desc: str = "Tasks") -> None:
        """Initialize the progress listener.

        Args:
            desc: Description for the task progress bar
        """
        self._desc = desc
        self._task_bar: tqdm | None = None
        self._eval_bar: tqdm | None = None

    def on_task_completed(
        self,
        index: int,
        total: int,
        result: "ExperimentResult",
    ) -> None:
        """Update task progress bar."""
        if self._task_bar is None:
            self._task_bar = tqdm(total=total, desc=self._desc)
        self._task_bar.update(1)

    def on_evaluation_completed(
        self,
        evaluator_name: str,
        index: int,
        total: int,
    ) -> None:
        """Update evaluation progress bar."""
        if self._eval_bar is None:
            self._eval_bar = tqdm(total=total, desc=f"Evaluating: {evaluator_name}")
        self._eval_bar.update(1)

    def on_experiment_completed(
        self,
        summary: "ExperimentSummary",
    ) -> None:
        """Close progress bars."""
        if self._task_bar is not None:
            self._task_bar.close()
        if self._eval_bar is not None:
            self._eval_bar.close()


# Verify protocol compliance
_listener: ProgressListener = TqdmProgressListener()  # type: ignore[assignment]

__all__ = ["TqdmProgressListener"]
