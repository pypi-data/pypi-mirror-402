"""Tests for Orchestrator resume functionality."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest

from cat.experiments.protocol import (
    DatasetExample,
    DiscoverResult,
    ExperimentConfig,
    InitResult,
    ShutdownResult,
    TaskInput,
    TaskResult,
)
from cat.experiments.runner.orchestrator import Orchestrator


def _make_task_result(run_id: str = "test#1", output: dict | None = None) -> TaskResult:
    """Helper to create TaskResult with defaults."""
    return TaskResult(run_id=run_id, output=output or {"result": "done"}, metadata={})


@pytest.fixture
def mock_executor():
    """Create mock Executor with protocol methods."""
    executor = Mock()
    executor.discover = AsyncMock(return_value=DiscoverResult(task="test_task", evaluators=[]))
    executor.init = AsyncMock(return_value=InitResult(ok=True))
    executor.run_task = AsyncMock(side_effect=lambda inp: _make_task_result(inp.run_id))
    executor.run_eval = AsyncMock(return_value=[])
    executor.shutdown = AsyncMock(return_value=ShutdownResult(ok=True))
    return executor


@pytest.fixture
def mock_progress():
    """Create mock ProgressListener."""
    return Mock()


@pytest.fixture
def sample_dataset():
    """Create sample dataset examples."""
    return [
        DatasetExample(input={"q": "A"}, output={"a": "1"}, id="ex1"),
        DatasetExample(input={"q": "B"}, output={"a": "2"}, id="ex2"),
        DatasetExample(input={"q": "C"}, output={"a": "3"}, id="ex3"),
    ]


class TestOrchestratorResume:
    """Test resume functionality."""

    @pytest.mark.asyncio
    async def test_resume_skips_completed_runs(self, mock_executor, mock_progress, sample_dataset):
        """Runs returned by backend.get_completed_runs() are skipped."""
        mock_backend = Mock()
        mock_backend.get_completed_runs.return_value = {"ex1#1", "ex2#1"}
        mock_backend.load_experiment.return_value = (
            ExperimentConfig(name="test"),
            sample_dataset,
            [],
        )

        orchestrator = Orchestrator(
            backend=mock_backend,
            executor=mock_executor,
            progress=mock_progress,
        )

        await orchestrator.run(
            dataset=sample_dataset,
            config=ExperimentConfig(name="test"),
            resume="exp123",
        )

        # Only ex3 should be executed
        assert mock_executor.run_task.call_count == 1

    @pytest.mark.asyncio
    async def test_resume_uses_stored_examples(self, mock_executor, mock_progress):
        """Uses examples from backend.load_experiment() for stable IDs."""
        stored_examples = [
            DatasetExample(input={"q": "stored"}, output={}, id="stored1"),
        ]

        mock_backend = Mock()
        mock_backend.get_completed_runs.return_value = set()
        mock_backend.load_experiment.return_value = (
            ExperimentConfig(name="test"),
            stored_examples,
            [],
        )

        captured_inputs: list[TaskInput] = []

        async def capture(inp: TaskInput) -> TaskResult:
            captured_inputs.append(inp)
            return TaskResult(run_id=inp.run_id or inp.id, output={}, metadata={})

        mock_executor.run_task = AsyncMock(side_effect=capture)

        orchestrator = Orchestrator(
            backend=mock_backend,
            executor=mock_executor,
            progress=mock_progress,
        )

        # Pass different dataset - should be ignored in favor of stored
        await orchestrator.run(
            dataset=[DatasetExample(input={"q": "new"}, output={}, id="new1")],
            config=ExperimentConfig(name="test"),
            resume="exp123",
        )

        assert captured_inputs[0].input == {"q": "stored"}

    @pytest.mark.asyncio
    async def test_resume_nonexistent_experiment_starts_fresh(
        self, mock_executor, mock_progress, sample_dataset
    ):
        """If experiment not found, runs all tasks."""
        mock_backend = Mock()
        mock_backend.get_completed_runs.return_value = None
        mock_backend.load_experiment.return_value = None

        orchestrator = Orchestrator(
            backend=mock_backend,
            executor=mock_executor,
            progress=mock_progress,
        )

        await orchestrator.run(
            dataset=sample_dataset,
            config=ExperimentConfig(name="test"),
            resume="nonexistent",
        )

        assert mock_executor.run_task.call_count == 3

    @pytest.mark.asyncio
    async def test_resume_all_completed_runs_nothing(
        self, mock_executor, mock_progress, sample_dataset
    ):
        """If all runs completed, no tasks executed."""
        mock_backend = Mock()
        mock_backend.get_completed_runs.return_value = {"ex1#1", "ex2#1", "ex3#1"}
        mock_backend.load_experiment.return_value = (
            ExperimentConfig(name="test"),
            sample_dataset,
            [],
        )

        orchestrator = Orchestrator(
            backend=mock_backend,
            executor=mock_executor,
            progress=mock_progress,
        )

        summary = await orchestrator.run(
            dataset=sample_dataset,
            config=ExperimentConfig(name="test"),
            resume="exp123",
        )

        mock_executor.run_task.assert_not_called()
        assert summary.total_examples == 0

    @pytest.mark.asyncio
    async def test_resume_requires_backend(self, mock_executor, mock_progress):
        """ValueError if resume specified without backend."""
        orchestrator = Orchestrator(
            backend=None,
            executor=mock_executor,
            progress=mock_progress,
        )

        with pytest.raises(ValueError, match="resume requires a storage backend"):
            await orchestrator.run(
                dataset=[],
                resume="exp123",
            )
