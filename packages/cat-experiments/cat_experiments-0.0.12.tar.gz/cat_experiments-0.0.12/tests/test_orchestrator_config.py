"""Tests for Orchestrator config validation."""

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
def mock_backend():
    """Create mock StorageBackend."""
    backend = Mock()
    backend.get_completed_runs.return_value = set()
    return backend


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
    return [DatasetExample(input={}, output={}, id="ex1")]


class TestOrchestratorConfigValidation:
    """Test config validation in orchestrator."""

    @pytest.mark.asyncio
    async def test_default_config_if_none_provided(
        self, mock_backend, mock_executor, mock_progress, sample_dataset
    ):
        """Uses default ExperimentConfig if not provided."""
        orchestrator = Orchestrator(
            backend=mock_backend,
            executor=mock_executor,
            progress=mock_progress,
        )

        summary = await orchestrator.run(
            dataset=sample_dataset,
            config=None,
        )

        # Should complete without error
        assert summary.config is not None
        assert summary.config.name is not None

    @pytest.mark.asyncio
    async def test_validates_max_workers_positive(
        self, mock_backend, mock_executor, mock_progress, sample_dataset
    ):
        """max_workers must be >= 1."""
        orchestrator = Orchestrator(
            backend=mock_backend,
            executor=mock_executor,
            progress=mock_progress,
        )

        with pytest.raises(ValueError, match="max_workers"):
            await orchestrator.run(
                dataset=sample_dataset,
                config=ExperimentConfig(name="test", max_workers=0),
            )

    @pytest.mark.asyncio
    async def test_validates_repetitions_positive(
        self, mock_backend, mock_executor, mock_progress, sample_dataset
    ):
        """repetitions must be >= 1."""
        orchestrator = Orchestrator(
            backend=mock_backend,
            executor=mock_executor,
            progress=mock_progress,
        )

        with pytest.raises(ValueError, match="repetitions"):
            await orchestrator.run(
                dataset=sample_dataset,
                config=ExperimentConfig(name="test", repetitions=0),
            )
