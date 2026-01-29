"""Tests for CLI protocol types."""

from __future__ import annotations

import json

from cat.experiments.protocol import (
    DatasetExample,
    EvalInput,
    EvalOutput,
    EvaluationContext,
    TaskInput,
    TaskOutput,
)


class TestTaskInput:
    """Tests for TaskInput protocol type."""

    def test_basic_creation(self):
        """Test basic TaskInput creation."""
        task_input = TaskInput(
            id="test_001",
            input={"query": "What is 2+2?"},
            output={"answer": "4"},
            metadata={"category": "math"},
        )

        assert task_input.id == "test_001"
        assert task_input.input == {"query": "What is 2+2?"}
        assert task_input.output == {"answer": "4"}
        assert task_input.metadata == {"category": "math"}
        assert task_input.params == {}

    def test_with_params(self):
        """Test TaskInput with experiment params."""
        task_input = TaskInput(
            id="test_001",
            input={"query": "Hello"},
            params={"model": "gpt-4o", "temperature": 0.7},
        )

        assert task_input.params == {"model": "gpt-4o", "temperature": 0.7}

    def test_with_runner_context(self):
        """Test TaskInput with runner context fields."""
        task_input = TaskInput(
            id="test_001",
            input={"query": "Hello"},
            experiment_id="exp_123",
            run_id="test_001#1",
            repetition_number=1,
        )

        assert task_input.experiment_id == "exp_123"
        assert task_input.run_id == "test_001#1"
        assert task_input.repetition_number == 1

    def test_from_dataset_example(self):
        """Test creating TaskInput from DatasetExample."""
        example = DatasetExample(
            id="ex_001",
            input={"query": "What is Python?"},
            output={"answer": "A programming language"},
            metadata={"source": "test"},
        )

        task_input = TaskInput.from_dataset_example(
            example,
            experiment_id="exp_456",
            run_id="ex_001#2",
            repetition_number=2,
            params={"model": "gpt-4o-mini"},
        )

        assert task_input.id == "ex_001"
        assert task_input.input == {"query": "What is Python?"}
        assert task_input.output == {"answer": "A programming language"}
        assert task_input.metadata == {"source": "test"}
        assert task_input.experiment_id == "exp_456"
        assert task_input.run_id == "ex_001#2"
        assert task_input.repetition_number == 2
        assert task_input.params == {"model": "gpt-4o-mini"}

    def test_to_json(self):
        """Test JSON serialization."""
        task_input = TaskInput(
            id="test_001",
            input={"query": "Hello"},
            params={"model": "gpt-4o"},
        )

        json_str = task_input.to_json()
        parsed = json.loads(json_str)

        assert parsed["id"] == "test_001"
        assert parsed["input"] == {"query": "Hello"}
        assert parsed["params"] == {"model": "gpt-4o"}

    def test_from_json(self):
        """Test JSON deserialization."""
        json_str = json.dumps(
            {
                "id": "test_002",
                "input": {"text": "Hello world"},
                "output": {"response": "Hi"},
                "params": {"temperature": 0.5},
            }
        )

        task_input = TaskInput.from_json(json_str)

        assert task_input.id == "test_002"
        assert task_input.input == {"text": "Hello world"}
        assert task_input.output == {"response": "Hi"}
        assert task_input.params == {"temperature": 0.5}

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "id": "test_003",
            "input": {"query": "test"},
            "experiment_id": "exp_789",
            "params": {"key": "value"},
        }

        task_input = TaskInput.from_dict(data)

        assert task_input.id == "test_003"
        assert task_input.experiment_id == "exp_789"
        assert task_input.params == {"key": "value"}

    def test_roundtrip(self):
        """Test JSON roundtrip preserves data."""
        original = TaskInput(
            id="roundtrip_001",
            input={"query": "test query"},
            output={"expected": "result"},
            metadata={"tag": "test"},
            experiment_id="exp_rt",
            run_id="roundtrip_001#1",
            repetition_number=1,
            params={"model": "test-model", "temp": 0.8},
        )

        json_str = original.to_json()
        restored = TaskInput.from_json(json_str)

        assert restored.id == original.id
        assert restored.input == original.input
        assert restored.output == original.output
        assert restored.metadata == original.metadata
        assert restored.experiment_id == original.experiment_id
        assert restored.run_id == original.run_id
        assert restored.repetition_number == original.repetition_number
        assert restored.params == original.params


class TestTaskOutput:
    """Tests for TaskOutput protocol type."""

    def test_string_output(self):
        """Test TaskOutput with string output."""
        task_output = TaskOutput(output="Hello world")

        assert task_output.output == "Hello world"
        assert task_output.metadata is None

    def test_dict_output(self):
        """Test TaskOutput with dict output."""
        task_output = TaskOutput(
            output={"response": "Hello", "confidence": 0.95},
            metadata={"model": "gpt-4o"},
        )

        assert task_output.output == {"response": "Hello", "confidence": 0.95}
        assert task_output.metadata == {"model": "gpt-4o"}

    def test_list_output(self):
        """Test TaskOutput with list output."""
        task_output = TaskOutput(output=["item1", "item2", "item3"])

        assert task_output.output == ["item1", "item2", "item3"]

    def test_with_tool_calls_in_output(self):
        """Test TaskOutput with tool calls in output dict."""
        task_output = TaskOutput(
            output={
                "answer": "Routed to IT",
                "tool_calls": [
                    {"name": "route_message", "args": {"department": "IT"}},
                ],
            },
        )

        assert isinstance(task_output.output, dict)
        assert task_output.output["tool_calls"] is not None
        assert len(task_output.output["tool_calls"]) == 1
        assert task_output.output["tool_calls"][0]["name"] == "route_message"

    def test_json_roundtrip(self):
        """Test JSON roundtrip."""
        original = TaskOutput(
            output={"result": "success", "tool_calls": [{"name": "test_tool", "args": {"x": 1}}]},
            metadata={"timing_ms": 100},
        )

        json_str = original.to_json()
        restored = TaskOutput.from_json(json_str)

        assert restored.output == original.output
        assert restored.metadata == original.metadata


class TestEvalInput:
    """Tests for EvalInput protocol type."""

    def test_basic_creation(self):
        """Test basic EvalInput creation."""
        eval_input = EvalInput(
            example={"id": "ex_001", "input": {"query": "test"}},
            actual_output="actual result",
            expected_output={"expected": "result"},
        )

        assert eval_input.example["id"] == "ex_001"
        assert eval_input.actual_output == "actual result"
        assert eval_input.expected_output == {"expected": "result"}
        assert eval_input.params == {}

    def test_with_tool_calls_in_actual_output(self):
        """Test EvalInput with tool calls in actual_output dict."""
        eval_input = EvalInput(
            example={"id": "ex_001", "input": {}},
            actual_output={
                "result": "result",
                "tool_calls": [{"name": "search", "args": {"q": "test"}}],
            },
        )

        tool_calls = eval_input.actual_output.get("tool_calls", [])
        assert len(tool_calls) == 1
        assert tool_calls[0]["name"] == "search"

    def test_with_params(self):
        """Test EvalInput with experiment params."""
        eval_input = EvalInput(
            example={"id": "ex_001", "input": {}},
            actual_output="result",
            params={"model": "gpt-4o", "prompt_version": "v2"},
        )

        assert eval_input.params == {"model": "gpt-4o", "prompt_version": "v2"}

    def test_from_evaluation_context(self):
        """Test creating EvalInput from EvaluationContext."""
        context = EvaluationContext(
            example_id="ctx_001",
            run_id="ctx_001#1",
            repetition_number=1,
            actual_output="The answer is 4",
            input={"query": "What is 2+2?"},
            output={"answer": "4"},
            metadata={"source": "test"},
            execution_metadata={"timing_ms": 50},
        )

        eval_input = EvalInput.from_evaluation_context(
            context,
            params={"model": "gpt-4o"},
        )

        assert eval_input.example["id"] == "ctx_001"
        assert eval_input.example["input"] == {"query": "What is 2+2?"}
        assert eval_input.actual_output == "The answer is 4"
        assert eval_input.expected_output == {"answer": "4"}
        assert eval_input.params == {"model": "gpt-4o"}

    def test_json_roundtrip(self):
        """Test JSON roundtrip."""
        original = EvalInput(
            example={"id": "ex_rt", "input": {"q": "test"}, "output": {"a": "result"}},
            actual_output={"response": "test response"},
            expected_output={"a": "result"},
            task_metadata={"time": 100},
            params={"key": "value"},
        )

        json_str = original.to_json()
        restored = EvalInput.from_json(json_str)

        assert restored.example == original.example
        assert restored.actual_output == original.actual_output
        assert restored.expected_output == original.expected_output
        assert restored.task_metadata == original.task_metadata
        assert restored.params == original.params


class TestEvalOutput:
    """Tests for EvalOutput protocol type."""

    def test_basic_creation(self):
        """Test basic EvalOutput creation."""
        eval_output = EvalOutput(score=0.95)

        assert eval_output.score == 0.95
        assert eval_output.label is None
        assert eval_output.metadata is None

    def test_with_label(self):
        """Test EvalOutput with label."""
        eval_output = EvalOutput(score=1.0, label="pass")

        assert eval_output.score == 1.0
        assert eval_output.label == "pass"

    def test_with_metadata(self):
        """Test EvalOutput with metadata."""
        eval_output = EvalOutput(
            score=0.8,
            label="partial",
            metadata={"reason": "Missing some details", "confidence": 0.9},
        )

        assert eval_output.score == 0.8
        assert eval_output.metadata is not None
        assert eval_output.metadata["reason"] == "Missing some details"

    def test_json_roundtrip(self):
        """Test JSON roundtrip."""
        original = EvalOutput(
            score=0.75,
            label="good",
            metadata={"breakdown": {"accuracy": 0.8, "completeness": 0.7}},
        )

        json_str = original.to_json()
        restored = EvalOutput.from_json(json_str)

        assert restored.score == original.score
        assert restored.label == original.label
        assert restored.metadata == original.metadata

    def test_from_dict_converts_score(self):
        """Test that from_dict converts score to float."""
        data = {"score": 1, "label": "perfect"}  # int score

        eval_output = EvalOutput.from_dict(data)

        assert isinstance(eval_output.score, float)
        assert eval_output.score == 1.0
