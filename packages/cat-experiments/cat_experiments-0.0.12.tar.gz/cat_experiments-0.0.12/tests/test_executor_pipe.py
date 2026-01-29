"""Tests for ThreadedPipeExecutor.

These tests verify that the pipe-based executor correctly simulates
the subprocess protocol, including JSON serialization round-trips.
"""

from __future__ import annotations

import pytest

from cat.experiments.protocol import (
    DatasetExample,
    EvalInput,
    ExperimentConfig,
    InitRequest,
    TaskInput,
)
from cat.experiments.runner.executor_pipe import ThreadedPipeExecutor


class TestThreadedPipeExecutorProtocol:
    """Test protocol methods via pipe communication."""

    @pytest.mark.asyncio
    async def test_discover_returns_task_and_evaluators(self):
        """discover() returns registered task and evaluators."""

        async def my_task(input: TaskInput) -> dict:
            return {"result": "done"}

        async def my_eval(input: EvalInput) -> float:
            return 1.0

        executor = ThreadedPipeExecutor(task_fn=my_task, evaluator_fns=[my_eval])
        await executor.start()

        try:
            result = await executor.discover()
            assert result.task == "my_task"
            assert "my_eval" in result.evaluators
        finally:
            await executor.stop()

    @pytest.mark.asyncio
    async def test_init_stores_config(self):
        """init() configures the executor."""

        async def my_task(input: TaskInput) -> dict:
            return {"result": "done"}

        executor = ThreadedPipeExecutor(task_fn=my_task)
        await executor.start()

        try:
            result = await executor.init(InitRequest(max_workers=4, params={"model": "gpt-4"}))
            assert result.ok is True
        finally:
            await executor.stop()

    @pytest.mark.asyncio
    async def test_run_task_executes_and_returns_result(self):
        """run_task() executes task and returns TaskResult."""

        async def my_task(input: TaskInput) -> dict:
            return {"answer": input.input.get("question", "") + " response"}

        executor = ThreadedPipeExecutor(task_fn=my_task)
        await executor.start()

        try:
            await executor.init(InitRequest(max_workers=1))

            task_input = TaskInput(
                id="test1",
                input={"question": "hello"},
                run_id="test1#1",
            )
            result = await executor.run_task(task_input)

            assert result.run_id == "test1#1"
            assert result.output == {"answer": "hello response"}
            assert result.error is None
            assert "execution_time_ms" in (result.metadata or {})
        finally:
            await executor.stop()

    @pytest.mark.asyncio
    async def test_run_task_handles_errors(self):
        """run_task() captures errors in result."""

        async def failing_task(input: TaskInput) -> dict:
            raise ValueError("Task failed intentionally")

        executor = ThreadedPipeExecutor(task_fn=failing_task)
        await executor.start()

        try:
            await executor.init(InitRequest(max_workers=1))

            task_input = TaskInput(id="test1", input={}, run_id="test1#1")
            result = await executor.run_task(task_input)

            assert result.run_id == "test1#1"
            assert result.error is not None
            assert "Task failed intentionally" in result.error
        finally:
            await executor.stop()

    @pytest.mark.asyncio
    async def test_run_eval_executes_single_evaluator(self):
        """run_eval() executes a single evaluator and returns result."""

        async def my_task(input: TaskInput) -> dict:
            return {"answer": "42"}

        async def accuracy_eval(input: EvalInput) -> float:
            expected = input.expected_output.get("answer") if input.expected_output else None
            actual = input.actual_output.get("answer") if input.actual_output else None
            return 1.0 if expected == actual else 0.0

        executor = ThreadedPipeExecutor(task_fn=my_task, evaluator_fns=[accuracy_eval])
        await executor.start()

        try:
            await executor.init(InitRequest(max_workers=1))

            eval_input = EvalInput(
                example={"id": "test1", "run_id": "test1#1", "input": {}, "output": {}},
                actual_output={"answer": "42"},
                expected_output={"answer": "42"},
            )
            result = await executor.run_eval(eval_input, "accuracy_eval")

            assert result.evaluator == "accuracy_eval"
            assert result.score == 1.0
            assert result.run_id == "test1#1"
        finally:
            await executor.stop()

    @pytest.mark.asyncio
    async def test_run_eval_returns_error_for_unknown_evaluator(self):
        """run_eval() returns error result for unknown evaluator."""

        async def my_task(input: TaskInput) -> dict:
            return {"answer": "42"}

        executor = ThreadedPipeExecutor(task_fn=my_task, evaluator_fns=[])
        await executor.start()

        try:
            await executor.init(InitRequest(max_workers=1))

            eval_input = EvalInput(
                example={"id": "test1", "run_id": "test1#1", "input": {}, "output": {}},
                actual_output={"answer": "42"},
                expected_output={"answer": "42"},
            )
            result = await executor.run_eval(eval_input, "unknown_eval")

            assert result.evaluator == "unknown_eval"
            assert result.score == 0.0
            assert result.error is not None
            assert "not found" in result.error
        finally:
            await executor.stop()

    @pytest.mark.asyncio
    async def test_shutdown_cleans_up(self):
        """shutdown() stops the worker thread."""

        async def my_task(input: TaskInput) -> dict:
            return {"result": "done"}

        executor = ThreadedPipeExecutor(task_fn=my_task)
        await executor.start()

        result = await executor.shutdown()
        assert result.ok is True

        # Worker thread should be stopped
        assert not executor._worker_thread.is_alive()


class TestThreadedPipeExecutorSerialization:
    """Test that data correctly round-trips through JSON."""

    @pytest.mark.asyncio
    async def test_complex_input_serializes_correctly(self):
        """Complex nested data survives JSON round-trip."""

        captured_input: list[TaskInput] = []

        async def capturing_task(input: TaskInput) -> dict:
            captured_input.append(input)
            return {"processed": True}

        executor = ThreadedPipeExecutor(task_fn=capturing_task)
        await executor.start()

        try:
            await executor.init(InitRequest(max_workers=1))

            task_input = TaskInput(
                id="test1",
                input={
                    "messages": [
                        {"role": "user", "content": "Hello"},
                        {"role": "assistant", "content": "Hi there!"},
                    ],
                    "metadata": {"nested": {"deeply": {"value": 123}}},
                },
                output={"expected": "value"},
                metadata={"tags": ["test", "example"]},
                run_id="test1#1",
                repetition_number=1,
                params={"temperature": 0.7, "model": "gpt-4"},
            )
            result = await executor.run_task(task_input)

            assert result.error is None
            assert len(captured_input) == 1

            # Verify data survived round-trip
            received = captured_input[0]
            assert received.id == "test1"
            assert received.input["messages"][0]["role"] == "user"
            assert received.input["metadata"]["nested"]["deeply"]["value"] == 123
            assert received.params["temperature"] == 0.7
        finally:
            await executor.stop()

    @pytest.mark.asyncio
    async def test_unicode_data_serializes_correctly(self):
        """Unicode strings survive JSON round-trip."""

        captured_input: list[TaskInput] = []

        async def capturing_task(input: TaskInput) -> dict:
            captured_input.append(input)
            return {"echo": input.input.get("text")}

        executor = ThreadedPipeExecutor(task_fn=capturing_task)
        await executor.start()

        try:
            await executor.init(InitRequest(max_workers=1))

            task_input = TaskInput(
                id="test1",
                input={"text": "Hello 世界! 🎉 Ñoño"},
                run_id="test1#1",
            )
            result = await executor.run_task(task_input)

            assert result.error is None
            assert result.output["echo"] == "Hello 世界! 🎉 Ñoño"
        finally:
            await executor.stop()


class TestThreadedPipeExecutorWithOrchestrator:
    """Test ThreadedPipeExecutor with the real Orchestrator."""

    @pytest.mark.asyncio
    async def test_full_experiment_via_pipe(self):
        """Run a complete experiment through pipe executor."""
        from unittest.mock import Mock

        from cat.experiments.runner.orchestrator import Orchestrator
        from cat.experiments.runner.progress import NullProgressListener

        async def my_task(input: TaskInput) -> dict:
            q = input.input.get("question", "")
            return {"answer": f"Answer to: {q}"}

        async def my_eval(input: EvalInput) -> float:
            return 1.0 if input.actual_output else 0.0

        executor = ThreadedPipeExecutor(task_fn=my_task, evaluator_fns=[my_eval])
        await executor.start()

        try:
            mock_backend = Mock()
            mock_backend.get_completed_runs.return_value = set()

            orchestrator = Orchestrator(
                backend=mock_backend,
                executor=executor,
                progress=NullProgressListener(),
            )

            dataset = [
                DatasetExample(input={"question": "Q1"}, output={}, id="ex1"),
                DatasetExample(input={"question": "Q2"}, output={}, id="ex2"),
            ]

            summary = await orchestrator.run(
                dataset=dataset,
                config=ExperimentConfig(name="pipe-test", max_workers=2),
            )

            assert summary.total_examples == 2
            assert summary.successful_examples == 2
            assert "my_eval" in summary.average_scores
            assert summary.average_scores["my_eval"] == 1.0
        finally:
            await executor.stop()
