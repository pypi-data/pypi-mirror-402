"""Integration tests for Orchestrator with real executor."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from cat.experiments.protocol import (
    DatasetExample,
    EvalInput,
    EvalOutput,
    ExperimentConfig,
    TaskInput,
)
from cat.experiments.runner.executor import InProcessExecutor
from cat.experiments.runner.orchestrator import Orchestrator
from cat.experiments.runner.progress import NullProgressListener


@pytest.fixture
def sample_dataset():
    """Create sample dataset examples."""
    return [
        DatasetExample(input={"question": "What is 2+2?"}, output={"answer": "4"}, id="ex1"),
        DatasetExample(input={"question": "What is 3+3?"}, output={"answer": "6"}, id="ex2"),
    ]


class TestOrchestratorEndToEnd:
    """Integration tests with real executor and mock backend."""

    @pytest.mark.asyncio
    async def test_full_experiment_flow(self, sample_dataset):
        """Run complete experiment: tasks -> evaluators -> summary."""
        mock_backend = Mock()
        mock_backend.get_completed_runs.return_value = set()

        async def task(input: TaskInput) -> dict:
            return {"answer": input.output.get("answer", "") if input.output else ""}

        async def evaluator(input: EvalInput) -> EvalOutput:
            expected = input.expected_output.get("answer", "") if input.expected_output else ""
            actual = input.actual_output.get("answer", "") if input.actual_output else ""
            score = 1.0 if expected == actual else 0.0
            return EvalOutput(score=score)

        # Pass task and evaluators to InProcessExecutor
        orchestrator = Orchestrator(
            backend=mock_backend,
            executor=InProcessExecutor(task_fn=task, evaluator_fns=[evaluator]),
            progress=NullProgressListener(),
        )

        summary = await orchestrator.run(
            dataset=sample_dataset,
            config=ExperimentConfig(name="integration-test"),
        )

        assert summary.total_examples == 2
        assert summary.successful_examples == 2
        assert summary.average_scores.get("evaluator", 0) == 1.0
        mock_backend.start_experiment.assert_called_once()
        mock_backend.complete_experiment.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_and_async_mixed(self, sample_dataset):
        """Experiment with sync task and async evaluators works."""
        mock_backend = Mock()
        mock_backend.get_completed_runs.return_value = set()

        def sync_task(input: TaskInput) -> dict:
            return {"answer": input.output.get("answer", "") if input.output else ""}

        async def async_evaluator(input: EvalInput) -> EvalOutput:
            return EvalOutput(score=1.0)

        # Pass task and evaluators to InProcessExecutor
        orchestrator = Orchestrator(
            backend=mock_backend,
            executor=InProcessExecutor(task_fn=sync_task, evaluator_fns=[async_evaluator]),
            progress=NullProgressListener(),
        )

        summary = await orchestrator.run(
            dataset=sample_dataset,
            config=ExperimentConfig(name="mixed-test"),
        )

        assert summary.total_examples == 2
        assert summary.successful_examples == 2

    @pytest.mark.asyncio
    async def test_full_experiment_with_resume(self, sample_dataset):
        """Run experiment with partial completion, resume, verify completion."""
        mock_backend = Mock()

        # First run - one succeeds, one fails
        mock_backend.get_completed_runs.return_value = set()

        run_count = 0

        async def task_with_partial_failure(input: TaskInput) -> dict:
            nonlocal run_count
            run_count += 1
            if run_count > 1:
                raise RuntimeError("Simulated failure")
            return {"answer": "done"}

        # Pass task to InProcessExecutor
        orchestrator = Orchestrator(
            backend=mock_backend,
            executor=InProcessExecutor(task_fn=task_with_partial_failure),
            progress=NullProgressListener(),
        )

        # First run completes with partial failure (1 success, 1 fail)
        summary = await orchestrator.run(
            dataset=sample_dataset,
            config=ExperimentConfig(name="resume-test"),
        )
        assert summary.successful_examples == 1
        assert summary.failed_examples == 1

        # Resume - backend reports first run completed
        mock_backend.get_completed_runs.return_value = {"ex1#1"}
        mock_backend.load_experiment.return_value = (
            ExperimentConfig(name="resume-test"),
            sample_dataset,
            [],
        )

        async def task_completes(input: TaskInput) -> dict:
            return {"answer": "done"}

        # Create new executor with new task for resume
        orchestrator = Orchestrator(
            backend=mock_backend,
            executor=InProcessExecutor(task_fn=task_completes),
            progress=NullProgressListener(),
        )

        summary = await orchestrator.run(
            dataset=sample_dataset,
            config=ExperimentConfig(name="resume-test"),
            resume="exp123",
        )

        # Only second example should have been run
        assert summary.total_examples == 1
