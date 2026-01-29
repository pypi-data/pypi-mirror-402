"""Tests for CLI decorator functions."""

from __future__ import annotations

import pytest

from cat.experiments.protocol import EvalInput, EvalOutput, TaskInput, TaskOutput
from cat.experiments.sdk.decorators import (
    clear_registry,
    evaluator,
    get_evaluator,
    get_task,
    list_evaluators,
    list_tasks,
    task,
)


@pytest.fixture(autouse=True)
def clean_registry():
    """Clear registry before and after each test."""
    clear_registry()
    yield
    clear_registry()


class TestTaskDecorator:
    """Tests for @task decorator."""

    def test_sync_task_registration(self):
        """Test that sync task is registered."""

        @task
        def my_sync_task(input_data: TaskInput) -> TaskOutput:
            return TaskOutput(output=f"Processed: {input_data.input.get('query')}")

        assert "my_sync_task" in list_tasks()
        assert get_task("my_sync_task") is not None

    def test_async_task_registration(self):
        """Test that async task is registered."""

        @task
        async def my_async_task(input_data: TaskInput) -> TaskOutput:
            return TaskOutput(output="async result")

        assert "my_async_task" in list_tasks()
        fn = get_task("my_async_task")
        assert fn is not None
        assert getattr(fn, "_is_async", False) is True

    def test_sync_task_execution(self):
        """Test sync task can be executed."""

        @task
        def echo_task(input_data: TaskInput) -> TaskOutput:
            return TaskOutput(
                output=input_data.input,
                metadata={"params": input_data.params},
            )

        fn = get_task("echo_task")
        assert fn is not None
        task_input = TaskInput(
            id="test_001",
            input={"message": "hello"},
            params={"key": "value"},
        )

        result = fn(task_input)

        assert isinstance(result, TaskOutput)
        assert result.output == {"message": "hello"}
        assert result.metadata == {"params": {"key": "value"}}

    @pytest.mark.asyncio
    async def test_async_task_execution(self):
        """Test async task can be executed."""

        @task
        async def async_echo_task(input_data: TaskInput) -> TaskOutput:
            return TaskOutput(output=f"async: {input_data.id}")

        fn = get_task("async_echo_task")
        assert fn is not None
        task_input = TaskInput(id="async_001", input={})

        result = await fn(task_input)

        assert isinstance(result, TaskOutput)
        assert result.output == "async: async_001"

    def test_task_returns_dict_normalized(self):
        """Test that dict return is normalized to TaskOutput."""

        @task
        def dict_task(input_data: TaskInput) -> dict:
            return {"output": "from dict", "metadata": {"source": "test"}}

        fn = get_task("dict_task")
        assert fn is not None
        result = fn(TaskInput(id="test", input={}))

        assert isinstance(result, TaskOutput)
        assert result.output == "from dict"
        assert result.metadata == {"source": "test"}

    def test_task_returns_string_normalized(self):
        """Test that string return is normalized to TaskOutput."""

        @task
        def string_task(input_data: TaskInput) -> str:
            return "just a string"

        fn = get_task("string_task")
        assert fn is not None
        result = fn(TaskInput(id="test", input={}))

        assert isinstance(result, TaskOutput)
        assert result.output == "just a string"

    def test_task_returns_plain_dict_as_output(self):
        """Test that plain dict (without 'output' key) becomes the output."""

        @task
        def plain_dict_task(input_data: TaskInput) -> dict:
            return {"response": "hello", "confidence": 0.9}

        fn = get_task("plain_dict_task")
        assert fn is not None
        result = fn(TaskInput(id="test", input={}))

        assert isinstance(result, TaskOutput)
        assert result.output == {"response": "hello", "confidence": 0.9}

    def test_task_preserves_function_name(self):
        """Test that decorator preserves function name."""

        @task
        def named_task(input_data: TaskInput) -> TaskOutput:
            return TaskOutput(output="test")

        fn = get_task("named_task")
        assert fn is not None
        assert fn.__name__ == "named_task"


class TestEvaluatorDecorator:
    """Tests for @evaluator decorator."""

    def test_sync_evaluator_registration(self):
        """Test that sync evaluator is registered."""

        @evaluator
        def my_evaluator(input_data: EvalInput) -> EvalOutput:
            return EvalOutput(score=1.0)

        assert "my_evaluator" in list_evaluators()
        assert get_evaluator("my_evaluator") is not None

    def test_async_evaluator_registration(self):
        """Test that async evaluator is registered."""

        @evaluator
        async def async_evaluator(input_data: EvalInput) -> EvalOutput:
            return EvalOutput(score=0.5)

        assert "async_evaluator" in list_evaluators()
        fn = get_evaluator("async_evaluator")
        assert fn is not None
        assert getattr(fn, "_is_async", False) is True

    def test_sync_evaluator_execution(self):
        """Test sync evaluator can be executed."""

        @evaluator
        def accuracy_eval(input_data: EvalInput) -> EvalOutput:
            expected = input_data.expected_output
            actual = input_data.actual_output
            score = 1.0 if expected == actual else 0.0
            return EvalOutput(score=score, label="pass" if score > 0.5 else "fail")

        fn = get_evaluator("accuracy_eval")
        assert fn is not None
        eval_input = EvalInput(
            example={"id": "test", "input": {}},
            actual_output="hello",
            expected_output="hello",
        )

        result = fn(eval_input)

        assert isinstance(result, EvalOutput)
        assert result.score == 1.0
        assert result.label == "pass"

    @pytest.mark.asyncio
    async def test_async_evaluator_execution(self):
        """Test async evaluator can be executed."""

        @evaluator
        async def async_eval(input_data: EvalInput) -> EvalOutput:
            return EvalOutput(score=0.75, metadata={"async": True})

        fn = get_evaluator("async_eval")
        assert fn is not None
        eval_input = EvalInput(
            example={"id": "test", "input": {}},
            actual_output="result",
        )

        result = await fn(eval_input)

        assert isinstance(result, EvalOutput)
        assert result.score == 0.75
        assert result.metadata == {"async": True}

    def test_evaluator_returns_float_normalized(self):
        """Test that float return is normalized to EvalOutput."""

        @evaluator
        def float_eval(input_data: EvalInput) -> float:
            return 0.85

        fn = get_evaluator("float_eval")
        assert fn is not None
        result = fn(EvalInput(example={"id": "test", "input": {}}, actual_output="x"))

        assert isinstance(result, EvalOutput)
        assert result.score == 0.85

    def test_evaluator_returns_int_normalized(self):
        """Test that int return is normalized to EvalOutput."""

        @evaluator
        def int_eval(input_data: EvalInput) -> int:
            return 1

        fn = get_evaluator("int_eval")
        assert fn is not None
        result = fn(EvalInput(example={"id": "test", "input": {}}, actual_output="x"))

        assert isinstance(result, EvalOutput)
        assert result.score == 1.0
        assert isinstance(result.score, float)

    def test_evaluator_returns_tuple_normalized(self):
        """Test that tuple (score, metadata) return is normalized."""

        @evaluator
        def tuple_eval(input_data: EvalInput) -> tuple:
            return (0.9, {"reason": "Good match"})

        fn = get_evaluator("tuple_eval")
        assert fn is not None
        result = fn(EvalInput(example={"id": "test", "input": {}}, actual_output="x"))

        assert isinstance(result, EvalOutput)
        assert result.score == 0.9
        assert result.metadata == {"reason": "Good match"}

    def test_evaluator_returns_dict_with_score(self):
        """Test that dict with 'score' key is normalized."""

        @evaluator
        def dict_eval(input_data: EvalInput) -> dict:
            return {"score": 0.7, "label": "good", "metadata": {"detail": "test"}}

        fn = get_evaluator("dict_eval")
        assert fn is not None
        result = fn(EvalInput(example={"id": "test", "input": {}}, actual_output="x"))

        assert isinstance(result, EvalOutput)
        assert result.score == 0.7
        assert result.label == "good"


class TestRegistryFunctions:
    """Tests for registry helper functions."""

    def test_list_tasks_empty(self):
        """Test list_tasks with empty registry."""
        assert list_tasks() == []

    def test_list_evaluators_empty(self):
        """Test list_evaluators with empty registry."""
        assert list_evaluators() == []

    def test_get_task_not_found(self):
        """Test get_task returns None for unknown task."""
        assert get_task("nonexistent") is None

    def test_get_evaluator_not_found(self):
        """Test get_evaluator returns None for unknown evaluator."""
        assert get_evaluator("nonexistent") is None

    def test_multiple_registrations(self):
        """Test multiple tasks and evaluators can be registered."""

        @task
        def task_a(input_data: TaskInput) -> TaskOutput:
            return TaskOutput(output="a")

        @task
        def task_b(input_data: TaskInput) -> TaskOutput:
            return TaskOutput(output="b")

        @evaluator
        def eval_x(input_data: EvalInput) -> EvalOutput:
            return EvalOutput(score=1.0)

        @evaluator
        def eval_y(input_data: EvalInput) -> EvalOutput:
            return EvalOutput(score=0.5)

        tasks = list_tasks()
        evaluators = list_evaluators()

        assert len(tasks) == 2
        assert "task_a" in tasks
        assert "task_b" in tasks
        assert len(evaluators) == 2
        assert "eval_x" in evaluators
        assert "eval_y" in evaluators

    def test_clear_registry(self):
        """Test clear_registry removes all registrations."""

        @task
        def temp_task(input_data: TaskInput) -> TaskOutput:
            return TaskOutput(output="temp")

        @evaluator
        def temp_eval(input_data: EvalInput) -> EvalOutput:
            return EvalOutput(score=1.0)

        assert len(list_tasks()) == 1
        assert len(list_evaluators()) == 1

        clear_registry()

        assert len(list_tasks()) == 0
        assert len(list_evaluators()) == 0
