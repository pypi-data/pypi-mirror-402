"""Tests for Orchestrator task execution."""

from __future__ import annotations

import asyncio
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


@pytest.fixture
def mock_backend():
    """Create mock StorageBackend."""
    backend = Mock()
    backend.get_completed_runs.return_value = set()
    return backend


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


class TestOrchestratorTaskExecution:
    """Test task execution flow."""

    @pytest.mark.asyncio
    async def test_executes_all_tasks(
        self, mock_backend, mock_executor, mock_progress, sample_dataset
    ):
        """All dataset examples are executed via executor."""
        orchestrator = Orchestrator(
            backend=mock_backend,
            executor=mock_executor,
            progress=mock_progress,
        )

        await orchestrator.run(
            dataset=sample_dataset,
            config=ExperimentConfig(name="test"),
        )

        assert mock_executor.run_task.call_count == 3

    @pytest.mark.asyncio
    async def test_respects_max_workers(
        self, mock_backend, mock_executor, mock_progress, sample_dataset
    ):
        """Parallelism is limited to config.max_workers."""
        concurrent_count = 0
        max_concurrent = 0

        async def track_concurrency(inp: TaskInput) -> TaskResult:
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.01)
            concurrent_count -= 1
            return TaskResult(run_id=inp.run_id or inp.id, output={"done": True}, metadata={})

        mock_executor.run_task = AsyncMock(side_effect=track_concurrency)

        orchestrator = Orchestrator(
            backend=mock_backend,
            executor=mock_executor,
            progress=mock_progress,
        )

        await orchestrator.run(
            dataset=sample_dataset,
            config=ExperimentConfig(name="test", max_workers=2),
        )

        assert max_concurrent <= 2

    @pytest.mark.asyncio
    async def test_saves_run_after_each_task(
        self, mock_backend, mock_executor, mock_progress, sample_dataset
    ):
        """backend.save_run() called after each task completes."""
        orchestrator = Orchestrator(
            backend=mock_backend,
            executor=mock_executor,
            progress=mock_progress,
        )

        await orchestrator.run(
            dataset=sample_dataset,
            config=ExperimentConfig(name="test"),
        )

        assert mock_backend.save_run.call_count == 3

    @pytest.mark.asyncio
    async def test_reports_progress_on_task_completion(
        self, mock_backend, mock_executor, mock_progress, sample_dataset
    ):
        """progress.on_task_completed() called after each task."""
        orchestrator = Orchestrator(
            backend=mock_backend,
            executor=mock_executor,
            progress=mock_progress,
        )

        await orchestrator.run(
            dataset=sample_dataset,
            config=ExperimentConfig(name="test"),
        )

        assert mock_progress.on_task_completed.call_count == 3

    @pytest.mark.asyncio
    async def test_continues_on_task_error(
        self, mock_backend, mock_executor, mock_progress, sample_dataset
    ):
        """If task fails, continues with remaining tasks."""
        call_count = 0

        async def sometimes_fails(inp: TaskInput) -> TaskResult:
            nonlocal call_count
            call_count += 1
            run_id = inp.run_id or inp.id
            if call_count == 1:
                return TaskResult(run_id=run_id, output=None, error="Failed", metadata={})
            return TaskResult(run_id=run_id, output={"done": True}, metadata={})

        mock_executor.run_task = AsyncMock(side_effect=sometimes_fails)

        orchestrator = Orchestrator(
            backend=mock_backend,
            executor=mock_executor,
            progress=mock_progress,
        )

        summary = await orchestrator.run(
            dataset=sample_dataset,
            config=ExperimentConfig(name="test"),
        )

        assert mock_executor.run_task.call_count == 3
        assert summary.failed_examples == 1
        assert summary.successful_examples == 2

    @pytest.mark.asyncio
    async def test_passes_params_to_task(self, mock_backend, mock_executor, mock_progress):
        """config.params included in TaskInput."""
        captured_inputs: list[TaskInput] = []

        async def capture_input(inp: TaskInput) -> TaskResult:
            captured_inputs.append(inp)
            return TaskResult(run_id=inp.run_id or inp.id, output={"done": True}, metadata={})

        mock_executor.run_task = AsyncMock(side_effect=capture_input)

        orchestrator = Orchestrator(
            backend=mock_backend,
            executor=mock_executor,
            progress=mock_progress,
        )

        dataset = [DatasetExample(input={"q": "test"}, output={}, id="ex1")]

        await orchestrator.run(
            dataset=dataset,
            config=ExperimentConfig(name="test", params={"model": "gpt-4"}),
        )

        assert captured_inputs[0].params == {"model": "gpt-4"}
