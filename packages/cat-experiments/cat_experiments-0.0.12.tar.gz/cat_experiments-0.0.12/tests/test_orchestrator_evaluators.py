"""Tests for Orchestrator evaluator execution."""

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
    TaskResult,
)
from cat.experiments.runner.orchestrator import Orchestrator


def _make_task_result(run_id: str = "test#1", output: dict | None = None) -> TaskResult:
    """Helper to create TaskResult with defaults."""
    return TaskResult(run_id=run_id, output=output or {"result": "done"}, metadata={})


def _make_eval_result(
    run_id: str, evaluator: str, score: float = 0.9, label: str | None = "good"
) -> EvalResult:
    """Helper to create EvalResult with defaults."""
    return EvalResult(run_id=run_id, evaluator=evaluator, score=score, label=label, metadata={})


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
    # Discover returns task and evaluators
    executor.discover = AsyncMock(
        return_value=DiscoverResult(task="test_task", evaluators=["eval1", "eval2"])
    )
    executor.init = AsyncMock(return_value=InitResult(ok=True))
    executor.run_task = AsyncMock(side_effect=lambda inp: _make_task_result(inp.run_id))
    # run_eval takes (input, evaluator) and returns single EvalResult
    executor.run_eval = AsyncMock(
        side_effect=lambda inp, evaluator: _make_eval_result(
            inp.example.get("run_id", ""), evaluator
        )
    )
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
    ]


class TestOrchestratorEvaluatorExecution:
    """Test evaluator execution flow."""

    @pytest.mark.asyncio
    async def test_executes_all_evaluators_on_each_result(
        self, mock_backend, mock_executor, mock_progress, sample_dataset
    ):
        """run_eval called once per (result, evaluator) pair."""
        orchestrator = Orchestrator(
            backend=mock_backend,
            executor=mock_executor,
            progress=mock_progress,
        )

        await orchestrator.run(
            dataset=sample_dataset,
            config=ExperimentConfig(name="test"),
        )

        # run_eval called once per (result, evaluator): 2 examples * 2 evaluators = 4
        assert mock_executor.run_eval.call_count == 4

    @pytest.mark.asyncio
    async def test_saves_evaluation_after_each(
        self, mock_backend, mock_executor, mock_progress, sample_dataset
    ):
        """backend.save_evaluation() called for each evaluator result."""
        orchestrator = Orchestrator(
            backend=mock_backend,
            executor=mock_executor,
            progress=mock_progress,
        )

        await orchestrator.run(
            dataset=sample_dataset,
            config=ExperimentConfig(name="test"),
        )

        # 2 examples * 2 evaluators = 4 evaluation saves
        assert mock_backend.save_evaluation.call_count == 4

    @pytest.mark.asyncio
    async def test_reports_progress_on_evaluation_completion(
        self, mock_backend, mock_executor, mock_progress, sample_dataset
    ):
        """progress.on_evaluation_completed() called for each evaluator result."""
        orchestrator = Orchestrator(
            backend=mock_backend,
            executor=mock_executor,
            progress=mock_progress,
        )

        await orchestrator.run(
            dataset=sample_dataset,
            config=ExperimentConfig(name="test"),
        )

        # 2 examples * 2 evaluators = 4 progress calls
        assert mock_progress.on_evaluation_completed.call_count == 4

    @pytest.mark.asyncio
    async def test_continues_on_evaluator_error(
        self, mock_backend, mock_executor, mock_progress, sample_dataset
    ):
        """If evaluator fails, continues with remaining evaluators."""
        call_count = 0

        async def sometimes_fails(inp, evaluator: str) -> EvalResult:
            nonlocal call_count
            call_count += 1
            run_id = inp.example.get("run_id", "")
            if call_count == 1:
                return EvalResult(run_id=run_id, evaluator=evaluator, score=0.0, error="Failed")
            return EvalResult(run_id=run_id, evaluator=evaluator, score=1.0)

        mock_executor.run_eval = AsyncMock(side_effect=sometimes_fails)

        orchestrator = Orchestrator(
            backend=mock_backend,
            executor=mock_executor,
            progress=mock_progress,
        )

        await orchestrator.run(
            dataset=sample_dataset,
            config=ExperimentConfig(name="test"),
        )

        # All evaluations attempted: 2 examples * 2 evaluators = 4 calls
        assert mock_executor.run_eval.call_count == 4

    @pytest.mark.asyncio
    async def test_no_evaluators_returns_empty_results(
        self, mock_backend, mock_executor, mock_progress, sample_dataset
    ):
        """If discover returns no evaluators, no evaluations are saved."""
        # Override discover to return no evaluators
        mock_executor.discover = AsyncMock(
            return_value=DiscoverResult(task="test_task", evaluators=[])
        )

        orchestrator = Orchestrator(
            backend=mock_backend,
            executor=mock_executor,
            progress=mock_progress,
        )

        await orchestrator.run(
            dataset=sample_dataset,
            config=ExperimentConfig(name="test"),
        )

        # run_eval not called since no evaluators discovered
        mock_executor.run_eval.assert_not_called()
        mock_backend.save_evaluation.assert_not_called()
