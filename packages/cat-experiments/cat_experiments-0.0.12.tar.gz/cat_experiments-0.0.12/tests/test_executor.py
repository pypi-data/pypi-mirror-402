"""Tests for Executor protocol and InProcessExecutor."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from cat.experiments.protocol import (
    EvalInput,
    EvalOutput,
    InitRequest,
    TaskInput,
    TaskOutput,
)
from cat.experiments.runner.executor import Executor, InProcessExecutor


class TestInProcessExecutorTaskExecution:
    """Test task execution in InProcessExecutor."""

    @pytest.mark.asyncio
    async def test_execute_async_task(self):
        """Executor awaits async task and returns TaskOutput."""
        executor = InProcessExecutor()

        async def async_task(input: TaskInput) -> dict:
            return {"result": input.id}

        task_input = TaskInput(id="ex1", input={"q": "test"})
        output = await executor.execute_task(async_task, task_input)

        assert isinstance(output, TaskOutput)
        assert output.output == {"result": "ex1"}
        assert output.error is None

    @pytest.mark.asyncio
    async def test_execute_sync_task(self):
        """Executor runs sync task via to_thread and returns TaskOutput."""
        executor = InProcessExecutor()

        def sync_task(input: TaskInput) -> dict:
            return {"result": input.id}

        task_input = TaskInput(id="ex1", input={"q": "test"})
        output = await executor.execute_task(sync_task, task_input)

        assert output.output == {"result": "ex1"}
        assert output.error is None

    @pytest.mark.asyncio
    async def test_execute_sync_task_uses_to_thread(self):
        """Verify sync task execution goes through to_thread."""
        executor = InProcessExecutor()

        def sync_task(input: TaskInput) -> dict:
            return {"result": "done"}

        task_input = TaskInput(id="ex1", input={"q": "test"})

        patch_target = "cat.experiments.runner.executor.asyncio.to_thread"
        with patch(patch_target, new_callable=AsyncMock) as mock:
            mock.return_value = {"result": "done"}
            await executor.execute_task(sync_task, task_input)

        mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_task_captures_timing(self):
        """TaskOutput includes started_at, completed_at, execution_time_ms in metadata."""
        executor = InProcessExecutor()

        async def async_task(input: TaskInput) -> dict:
            await asyncio.sleep(0.01)  # Small delay to measure
            return {"result": "done"}

        task_input = TaskInput(id="ex1", input={})
        output = await executor.execute_task(async_task, task_input)

        assert output.metadata is not None
        assert "started_at" in output.metadata
        assert "completed_at" in output.metadata
        assert "execution_time_ms" in output.metadata
        assert output.metadata["execution_time_ms"] >= 10  # At least 10ms

    @pytest.mark.asyncio
    async def test_execute_task_handles_exception(self):
        """On task exception, returns TaskOutput with error field, not raise."""
        executor = InProcessExecutor()

        async def failing_task(input: TaskInput) -> dict:
            raise ValueError("Task failed")

        task_input = TaskInput(id="ex1", input={})
        output = await executor.execute_task(failing_task, task_input)

        assert output.error == "Task failed"
        assert output.output is None

    @pytest.mark.asyncio
    async def test_execute_task_passes_input_correctly(self):
        """Task receives TaskInput with all fields populated."""
        executor = InProcessExecutor()
        received_input = None

        async def capturing_task(input: TaskInput) -> dict:
            nonlocal received_input
            received_input = input
            return {"done": True}

        task_input = TaskInput(
            id="ex1",
            input={"question": "test"},
            output={"answer": "expected"},
            metadata={"tag": "test"},
            experiment_id="exp123",
            run_id="ex1#1",
            repetition_number=1,
            params={"model": "gpt-4"},
        )
        await executor.execute_task(capturing_task, task_input)

        assert received_input == task_input


class TestInProcessExecutorEvaluatorExecution:
    """Test evaluator execution in InProcessExecutor."""

    @pytest.mark.asyncio
    async def test_execute_async_evaluator(self):
        """Executor awaits async evaluator and returns EvalOutput."""
        executor = InProcessExecutor()

        async def async_evaluator(input: EvalInput) -> EvalOutput:
            return EvalOutput(score=0.9, label="good")

        eval_input = EvalInput(example={"id": "ex1"}, actual_output="response")
        output = await executor.execute_evaluator(async_evaluator, eval_input)

        assert isinstance(output, EvalOutput)
        assert output.score == 0.9
        assert output.label == "good"

    @pytest.mark.asyncio
    async def test_execute_sync_evaluator(self):
        """Executor runs sync evaluator via to_thread and returns EvalOutput."""
        executor = InProcessExecutor()

        def sync_evaluator(input: EvalInput) -> EvalOutput:
            return EvalOutput(score=0.8)

        eval_input = EvalInput(example={"id": "ex1"}, actual_output="response")
        output = await executor.execute_evaluator(sync_evaluator, eval_input)

        assert output.score == 0.8

    @pytest.mark.asyncio
    async def test_execute_sync_evaluator_uses_to_thread(self):
        """Verify sync evaluator execution goes through to_thread."""
        executor = InProcessExecutor()

        def sync_evaluator(input: EvalInput) -> EvalOutput:
            return EvalOutput(score=0.8)

        eval_input = EvalInput(example={"id": "ex1"}, actual_output="response")

        with patch(
            "cat.experiments.runner.executor.asyncio.to_thread", new_callable=AsyncMock
        ) as mock:
            mock.return_value = EvalOutput(score=0.8)
            await executor.execute_evaluator(sync_evaluator, eval_input)

        mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_evaluator_captures_timing(self):
        """EvalOutput includes timing metadata."""
        executor = InProcessExecutor()

        async def async_evaluator(input: EvalInput) -> EvalOutput:
            return EvalOutput(score=1.0)

        eval_input = EvalInput(example={"id": "ex1"}, actual_output="response")
        output = await executor.execute_evaluator(async_evaluator, eval_input)

        assert output.metadata is not None
        assert "execution_time_ms" in output.metadata

    @pytest.mark.asyncio
    async def test_execute_evaluator_handles_exception(self):
        """On evaluator exception, returns EvalOutput with error/zero score."""
        executor = InProcessExecutor()

        async def failing_evaluator(input: EvalInput) -> EvalOutput:
            raise RuntimeError("Eval failed")

        eval_input = EvalInput(example={"id": "ex1"}, actual_output="response")
        output = await executor.execute_evaluator(failing_evaluator, eval_input)

        assert output.score == 0.0
        assert output.metadata is not None
        assert "error" in output.metadata


class TestExecutorProtocol:
    """Test Executor protocol compliance."""

    def test_in_process_executor_implements_protocol(self):
        """InProcessExecutor satisfies Executor protocol."""
        executor = InProcessExecutor()
        assert isinstance(executor, Executor)


class TestExecutorNewProtocol:
    """Test new executor protocol methods (discover, init, run_task, run_eval, shutdown)."""

    @pytest.mark.asyncio
    async def test_discover_returns_discover_result(self):
        """discover() returns DiscoverResult with protocol version."""
        from cat.experiments.protocol import DiscoverResult

        executor = InProcessExecutor()
        result = await executor.discover()

        assert isinstance(result, DiscoverResult)
        assert result.protocol_version == "1.0"

    @pytest.mark.asyncio
    async def test_discover_with_registered_task(self):
        """discover() finds registered @task function."""
        from cat.experiments.sdk.decorators import clear_registry, task

        clear_registry()

        @task
        def my_task(input: TaskInput) -> TaskOutput:
            return TaskOutput(output="done")

        executor = InProcessExecutor()
        result = await executor.discover()

        assert result.task == "my_task"
        clear_registry()

    @pytest.mark.asyncio
    async def test_discover_with_registered_evaluators(self):
        """discover() finds registered @evaluator functions."""
        from cat.experiments.sdk.decorators import clear_registry, evaluator, task

        clear_registry()

        @task
        def my_task(input: TaskInput) -> TaskOutput:
            return TaskOutput(output="done")

        @evaluator
        def eval_one(input: EvalInput) -> EvalOutput:
            return EvalOutput(score=1.0)

        @evaluator
        def eval_two(input: EvalInput) -> EvalOutput:
            return EvalOutput(score=0.5)

        executor = InProcessExecutor()
        result = await executor.discover()

        assert "eval_one" in result.evaluators
        assert "eval_two" in result.evaluators
        clear_registry()

    @pytest.mark.asyncio
    async def test_init_sets_max_workers(self):
        """init() configures max_workers for parallelism."""
        from cat.experiments.protocol import InitResult

        executor = InProcessExecutor()
        result = await executor.init(InitRequest(max_workers=4, params={"model": "gpt-4"}))

        assert isinstance(result, InitResult)
        assert result.ok is True
        assert executor._max_workers == 4
        assert executor._params == {"model": "gpt-4"}

    @pytest.mark.asyncio
    async def test_run_task_returns_result(self):
        """run_task() returns TaskResult for a single input."""
        from cat.experiments.protocol import TaskResult

        async def my_task(input: TaskInput) -> TaskOutput:
            return TaskOutput(output={"id": input.id})

        executor = InProcessExecutor(task_fn=my_task)
        await executor.init(InitRequest(max_workers=2))

        task_input = TaskInput(id="ex1", input={"q": "a"}, run_id="ex1#1")
        result = await executor.run_task(task_input)

        assert isinstance(result, TaskResult)
        assert result.run_id == "ex1#1"
        assert result.output == {"id": "ex1"}
        assert result.error is None

    @pytest.mark.asyncio
    async def test_run_task_handles_errors(self):
        """run_task() captures errors in TaskResult.error."""

        async def failing_task(input: TaskInput) -> TaskOutput:
            raise ValueError(f"Failed for {input.id}")

        executor = InProcessExecutor(task_fn=failing_task)
        await executor.init(InitRequest(max_workers=1))

        task_input = TaskInput(id="ex1", input={}, run_id="ex1#1")
        result = await executor.run_task(task_input)

        assert result.run_id == "ex1#1"
        assert result.error == "Failed for ex1"

    @pytest.mark.asyncio
    async def test_run_eval_returns_result_for_single_evaluator(self):
        """run_eval() returns EvalResult for the specified evaluator."""
        from cat.experiments.protocol import EvalResult

        def eval_a(input: EvalInput) -> EvalOutput:
            return EvalOutput(score=0.8)

        def eval_b(input: EvalInput) -> EvalOutput:
            return EvalOutput(score=0.9)

        executor = InProcessExecutor(evaluator_fns=[eval_a, eval_b])
        await executor.init(InitRequest(max_workers=2))

        eval_input = EvalInput(example={"id": "ex1", "run_id": "ex1#1"}, actual_output="a")
        result_a = await executor.run_eval(eval_input, "eval_a")
        result_b = await executor.run_eval(eval_input, "eval_b")

        assert isinstance(result_a, EvalResult)
        assert result_a.evaluator == "eval_a"
        assert result_a.score == 0.8

        assert isinstance(result_b, EvalResult)
        assert result_b.evaluator == "eval_b"
        assert result_b.score == 0.9

    @pytest.mark.asyncio
    async def test_run_eval_returns_error_for_unknown_evaluator(self):
        """run_eval() returns error for unknown evaluator."""
        from cat.experiments.protocol import EvalResult

        def eval_a(input: EvalInput) -> EvalOutput:
            return EvalOutput(score=0.8)

        executor = InProcessExecutor(evaluator_fns=[eval_a])
        await executor.init(InitRequest(max_workers=2))

        eval_input = EvalInput(example={"id": "ex1", "run_id": "ex1#1"}, actual_output="a")
        result = await executor.run_eval(eval_input, "unknown_eval")

        assert isinstance(result, EvalResult)
        assert result.evaluator == "unknown_eval"
        assert result.score == 0.0
        assert result.error is not None
        assert "not found" in result.error

    @pytest.mark.asyncio
    async def test_run_eval_handles_errors(self):
        """run_eval() captures errors in EvalResult.error."""

        def failing_eval(input: EvalInput) -> EvalOutput:
            raise RuntimeError("Eval failed")

        executor = InProcessExecutor(evaluator_fns=[failing_eval])
        await executor.init(InitRequest(max_workers=1))

        eval_input = EvalInput(example={"id": "ex1", "run_id": "ex1#1"}, actual_output="a")
        result = await executor.run_eval(eval_input, "failing_eval")

        assert result.score == 0.0
        assert result.error == "Eval failed"

    @pytest.mark.asyncio
    async def test_shutdown_returns_ok(self):
        """shutdown() returns ShutdownResult with ok=True."""
        from cat.experiments.protocol import ShutdownResult

        executor = InProcessExecutor()
        await executor.init(InitRequest(max_workers=2))

        result = await executor.shutdown()

        assert isinstance(result, ShutdownResult)
        assert result.ok is True
        assert executor._initialized is False
