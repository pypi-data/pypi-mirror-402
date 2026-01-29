"""Tests for Orchestrator backend lifecycle integration."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest

from cat.experiments.protocol import (
    DatasetExample,
    DiscoverResult,
    ExperimentConfig,
    InitResult,
    ShutdownResult,
    TaskResult,
)
from cat.experiments.runner.orchestrator import Orchestrator


def _make_task_result(run_id: str = "test#1", output: dict | None = None) -> TaskResult:
    """Helper to create TaskResult with defaults."""
    return TaskResult(run_id=run_id, output=output or {"done": True}, metadata={})


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
    return [DatasetExample(input={"q": "A"}, output={}, id="ex1")]


class TestOrchestratorBackendIntegration:
    """Test backend lifecycle calls."""

    @pytest.mark.asyncio
    async def test_calls_start_experiment_at_beginning(
        self, mock_executor, mock_progress, sample_dataset
    ):
        """backend.start_experiment() called before tasks."""
        mock_backend = Mock()
        mock_backend.get_completed_runs.return_value = set()

        orchestrator = Orchestrator(
            backend=mock_backend,
            executor=mock_executor,
            progress=mock_progress,
        )

        await orchestrator.run(
            dataset=sample_dataset,
            config=ExperimentConfig(name="test"),
        )

        mock_backend.start_experiment.assert_called_once()

    @pytest.mark.asyncio
    async def test_calls_complete_experiment_on_success(
        self, mock_executor, mock_progress, sample_dataset
    ):
        """backend.complete_experiment() called with summary on success."""
        mock_backend = Mock()
        mock_backend.get_completed_runs.return_value = set()

        orchestrator = Orchestrator(
            backend=mock_backend,
            executor=mock_executor,
            progress=mock_progress,
        )

        await orchestrator.run(
            dataset=sample_dataset,
            config=ExperimentConfig(name="test"),
        )

        mock_backend.complete_experiment.assert_called_once()
        # Verify summary is passed
        call_args = mock_backend.complete_experiment.call_args
        assert call_args[0][1].total_examples == 1  # summary arg

    @pytest.mark.asyncio
    async def test_calls_fail_experiment_on_error(
        self, mock_executor, mock_progress, sample_dataset
    ):
        """backend.fail_experiment() called if orchestrator fails."""
        mock_backend = Mock()
        mock_backend.get_completed_runs.return_value = set()

        # Make all tasks fail
        mock_executor.run_task = AsyncMock(
            side_effect=lambda inp: TaskResult(
                run_id=inp.run_id, output=None, error="Failed", metadata={}
            )
        )

        orchestrator = Orchestrator(
            backend=mock_backend,
            executor=mock_executor,
            progress=mock_progress,
        )

        with pytest.raises(RuntimeError):
            await orchestrator.run(
                dataset=sample_dataset,
                config=ExperimentConfig(name="test"),
            )

        mock_backend.fail_experiment.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_backend_runs_without_persistence(
        self, mock_executor, mock_progress, sample_dataset
    ):
        """If backend is None, runs tasks without persistence."""
        orchestrator = Orchestrator(
            backend=None,
            executor=mock_executor,
            progress=mock_progress,
        )

        summary = await orchestrator.run(
            dataset=sample_dataset,
            config=ExperimentConfig(name="test"),
        )

        # Should complete without error
        assert summary.total_examples == 1
