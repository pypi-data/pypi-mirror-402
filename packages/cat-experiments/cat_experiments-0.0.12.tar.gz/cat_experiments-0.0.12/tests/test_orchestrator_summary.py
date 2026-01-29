"""Tests for Orchestrator summary building."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest

from cat.experiments.protocol import (
    DatasetExample,
    DiscoverResult,
    EvalResult,
    ExperimentConfig,
    InitResult,
    ShutdownResult,
    TaskInput,
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
def mock_progress():
    """Create mock ProgressListener."""
    return Mock()


class TestOrchestratorSummary:
    """Test ExperimentSummary building."""

    @pytest.mark.asyncio
    async def test_summary_counts_total_examples(self, mock_backend, mock_progress):
        """summary.total_examples matches number of runs."""
        mock_executor = Mock()
        mock_executor.discover = AsyncMock(
            return_value=DiscoverResult(task="test_task", evaluators=[])
        )
        mock_executor.init = AsyncMock(return_value=InitResult(ok=True))
        mock_executor.run_task = AsyncMock(side_effect=lambda inp: _make_task_result(inp.run_id))
        mock_executor.run_eval = AsyncMock(return_value=[])
        mock_executor.shutdown = AsyncMock(return_value=ShutdownResult(ok=True))

        dataset = [DatasetExample(input={}, output={}, id=f"ex{i}") for i in range(5)]

        orchestrator = Orchestrator(
            backend=mock_backend,
            executor=mock_executor,
            progress=mock_progress,
        )

        summary = await orchestrator.run(
            dataset=dataset,
            config=ExperimentConfig(name="test"),
        )

        assert summary.total_examples == 5

    @pytest.mark.asyncio
    async def test_summary_counts_successful_and_failed(self, mock_backend, mock_progress):
        """summary.successful_examples and failed_examples are correct."""
        call_count = 0

        async def mixed_results(inp: TaskInput) -> TaskResult:
            nonlocal call_count
            call_count += 1
            run_id = inp.run_id or inp.id
            if call_count <= 2:
                return TaskResult(run_id=run_id, output=None, error="Failed", metadata={})
            return TaskResult(run_id=run_id, output={"done": True}, metadata={})

        mock_executor = Mock()
        mock_executor.discover = AsyncMock(
            return_value=DiscoverResult(task="test_task", evaluators=[])
        )
        mock_executor.init = AsyncMock(return_value=InitResult(ok=True))
        mock_executor.run_task = AsyncMock(side_effect=mixed_results)
        mock_executor.run_eval = AsyncMock(return_value=[])
        mock_executor.shutdown = AsyncMock(return_value=ShutdownResult(ok=True))

        dataset = [DatasetExample(input={}, output={}, id=f"ex{i}") for i in range(5)]

        orchestrator = Orchestrator(
            backend=mock_backend,
            executor=mock_executor,
            progress=mock_progress,
        )

        summary = await orchestrator.run(
            dataset=dataset,
            config=ExperimentConfig(name="test"),
        )

        assert summary.failed_examples == 2
        assert summary.successful_examples == 3

    @pytest.mark.asyncio
    async def test_summary_calculates_average_scores(self, mock_backend, mock_progress):
        """summary.average_scores averages across successful runs."""
        mock_executor = Mock()
        mock_executor.discover = AsyncMock(
            return_value=DiscoverResult(task="test_task", evaluators=["accuracy"])
        )
        mock_executor.init = AsyncMock(return_value=InitResult(ok=True))
        mock_executor.run_task = AsyncMock(side_effect=lambda inp: _make_task_result(inp.run_id))
        mock_executor.shutdown = AsyncMock(return_value=ShutdownResult(ok=True))

        scores = [0.8, 0.9, 1.0]
        call_count = 0

        async def return_scores(inp, evaluator: str) -> EvalResult:
            nonlocal call_count
            score = scores[call_count % len(scores)]
            call_count += 1
            run_id = inp.example.get("run_id", "")
            return EvalResult(run_id=run_id, evaluator=evaluator, score=score)

        mock_executor.run_eval = AsyncMock(side_effect=return_scores)

        dataset = [DatasetExample(input={}, output={}, id=f"ex{i}") for i in range(3)]

        orchestrator = Orchestrator(
            backend=mock_backend,
            executor=mock_executor,
            progress=mock_progress,
        )

        summary = await orchestrator.run(
            dataset=dataset,
            config=ExperimentConfig(name="test"),
        )

        assert summary.average_scores["accuracy"] == pytest.approx(0.9)

    @pytest.mark.asyncio
    async def test_summary_includes_timing(self, mock_backend, mock_progress):
        """summary.started_at, completed_at, total_execution_time_ms set."""
        mock_executor = Mock()
        mock_executor.discover = AsyncMock(
            return_value=DiscoverResult(task="test_task", evaluators=[])
        )
        mock_executor.init = AsyncMock(return_value=InitResult(ok=True))
        mock_executor.run_task = AsyncMock(
            side_effect=lambda inp: TaskResult(
                run_id=inp.run_id or inp.id,
                output={"done": True},
                metadata={"execution_time_ms": 100},
            )
        )
        mock_executor.run_eval = AsyncMock(return_value=[])
        mock_executor.shutdown = AsyncMock(return_value=ShutdownResult(ok=True))

        dataset = [DatasetExample(input={}, output={}, id="ex1")]

        orchestrator = Orchestrator(
            backend=mock_backend,
            executor=mock_executor,
            progress=mock_progress,
        )

        summary = await orchestrator.run(
            dataset=dataset,
            config=ExperimentConfig(name="test"),
        )

        assert summary.started_at is not None
        assert summary.completed_at is not None
        assert summary.total_execution_time_ms >= 0
