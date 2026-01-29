"""Tests for Orchestrator dataset preparation."""

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


class TestOrchestratorDatasetPreparation:
    """Test dataset preparation (preview, repetitions, run_selection)."""

    @pytest.mark.asyncio
    async def test_preview_examples_limits_dataset(
        self, mock_backend, mock_executor, mock_progress
    ):
        """config.preview_examples limits number of examples run."""
        dataset = [DatasetExample(input={"q": str(i)}, output={}, id=f"ex{i}") for i in range(10)]

        orchestrator = Orchestrator(
            backend=mock_backend,
            executor=mock_executor,
            progress=mock_progress,
        )

        await orchestrator.run(
            dataset=dataset,
            config=ExperimentConfig(name="test", preview_examples=3),
        )

        assert mock_executor.run_task.call_count == 3

    @pytest.mark.asyncio
    async def test_preview_seed_is_deterministic(self, mock_backend, mock_executor, mock_progress):
        """Same seed produces same preview selection."""
        dataset = [DatasetExample(input={"q": str(i)}, output={}, id=f"ex{i}") for i in range(10)]

        captured_ids_run1: list[str] = []
        captured_ids_run2: list[str] = []

        async def capture_run1(inp: TaskInput) -> TaskResult:
            captured_ids_run1.append(inp.id)
            return TaskResult(run_id=inp.run_id or inp.id, output={}, metadata={})

        async def capture_run2(inp: TaskInput) -> TaskResult:
            captured_ids_run2.append(inp.id)
            return TaskResult(run_id=inp.run_id or inp.id, output={}, metadata={})

        # Run 1
        mock_executor.run_task = AsyncMock(side_effect=capture_run1)
        orchestrator = Orchestrator(
            backend=mock_backend,
            executor=mock_executor,
            progress=mock_progress,
        )
        await orchestrator.run(
            dataset=dataset,
            config=ExperimentConfig(name="test", preview_examples=3, preview_seed=42),
        )

        # Run 2
        mock_executor.run_task = AsyncMock(side_effect=capture_run2)
        orchestrator = Orchestrator(
            backend=mock_backend,
            executor=mock_executor,
            progress=mock_progress,
        )
        await orchestrator.run(
            dataset=dataset,
            config=ExperimentConfig(name="test", preview_examples=3, preview_seed=42),
        )

        assert captured_ids_run1 == captured_ids_run2

    @pytest.mark.asyncio
    async def test_repetitions_expands_runs(self, mock_backend, mock_executor, mock_progress):
        """Each example runs config.repetitions times."""
        dataset = [
            DatasetExample(input={"q": "A"}, output={}, id="ex1"),
            DatasetExample(input={"q": "B"}, output={}, id="ex2"),
        ]

        orchestrator = Orchestrator(
            backend=mock_backend,
            executor=mock_executor,
            progress=mock_progress,
        )

        await orchestrator.run(
            dataset=dataset,
            config=ExperimentConfig(name="test", repetitions=3),
        )

        # 2 examples * 3 repetitions = 6 runs
        assert mock_executor.run_task.call_count == 6

    @pytest.mark.asyncio
    async def test_run_selection_filters_examples(self, mock_backend, mock_executor, mock_progress):
        """Only specified examples/repetitions are run."""
        dataset = [
            DatasetExample(input={"q": "A"}, output={}, id="ex1"),
            DatasetExample(input={"q": "B"}, output={}, id="ex2"),
            DatasetExample(input={"q": "C"}, output={}, id="ex3"),
        ]

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

        # Only run ex1 rep 1 and ex3 reps 1,2
        await orchestrator.run(
            dataset=dataset,
            config=ExperimentConfig(name="test", repetitions=3),
            run_selection={"ex1": [1], "ex3": [1, 2]},
        )

        assert len(captured_inputs) == 3
        ids = [inp.id for inp in captured_inputs]
        assert "ex1" in ids
        assert "ex3" in ids
        assert "ex2" not in ids
