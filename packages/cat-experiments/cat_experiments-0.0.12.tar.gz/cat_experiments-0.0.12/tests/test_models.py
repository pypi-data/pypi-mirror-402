"""Test core data models."""

from __future__ import annotations

import os
import sys
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from cat.experiments.protocol import (
    DatasetExample,
    EvaluationContext,
    EvaluationMetric,
)


class TestDatasetExample:
    """Test DatasetExample data model."""

    def test_dataset_example_creation(self):
        """Test basic DatasetExample creation."""
        example = DatasetExample(
            input={"messages": [{"role": "user", "content": "Hello"}]},
            output={"messages": [{"role": "assistant", "content": "Hi!"}]},
            metadata={"category": "greeting"},
        )
        example.tags = ["test", "greeting"]

        assert example.input["messages"][0]["content"] == "Hello"
        assert example.output["messages"][0]["content"] == "Hi!"
        assert example.metadata["category"] == "greeting"
        assert "test" in example.tags
        assert example.id is not None
        assert isinstance(example.created_at, datetime)
        assert isinstance(example.updated_at, datetime)

    def test_dataset_example_flexible_data(self):
        """Test DatasetExample with various data structures."""
        # LLM example
        llm_example = DatasetExample(
            input={"messages": [], "temperature": 0.7}, output={"response": "Hello"}
        )
        assert llm_example.input["temperature"] == 0.7

        # ML example
        ml_example = DatasetExample(
            input={"age": 25, "income": 75000, "features": [1, 2, 3]},
            output={"prediction": 0.85, "class": "positive"},
        )
        assert ml_example.input["age"] == 25
        assert ml_example.output["prediction"] == 0.85

        # Vision example
        vision_example = DatasetExample(
            input={"image_url": "http://example.com/image.jpg"},
            output={"objects": [{"name": "cat", "confidence": 0.9}]},
        )
        assert "image_url" in vision_example.input
        assert vision_example.output["objects"][0]["name"] == "cat"


class TestEvaluationContext:
    """Test EvaluationContext data model."""

    def test_evaluation_context_creation(self):
        """Test basic EvaluationContext creation."""
        context = EvaluationContext(
            example_id="test_123",
            run_id="test_123#1",
            repetition_number=1,
            actual_output="Generated response",
            input={"query": "test"},
            output={"response": "expected"},
            metadata={"source": "test"},
            execution_time_ms=250.0,
            error=None,
        )

        assert context.example_id == "test_123"
        assert context.actual_output == "Generated response"
        assert context.input["query"] == "test"
        assert context.output["response"] == "expected"
        assert context.metadata["source"] == "test"
        assert context.execution_time_ms == 250.0
        assert context.error is None

    def test_evaluation_context_with_tool_calls_in_output(self):
        """Test EvaluationContext with tool calls in actual_output dict."""
        context = EvaluationContext(
            example_id="test_123",
            run_id="test_123#1",
            repetition_number=1,
            actual_output={
                "result": "Found results",
                "tool_calls": [
                    {"name": "search", "args": {"q": "python"}, "result": "found"},
                ],
            },
        )

        # Tool calls are now in the output dict
        tool_calls = context.actual_output.get("tool_calls", [])
        assert len(tool_calls) == 1
        assert tool_calls[0]["name"] == "search"
        assert tool_calls[0]["result"] == "found"

    def test_evaluation_context_error_handling(self):
        """Test EvaluationContext with error information."""
        context = EvaluationContext(
            example_id="test_123",
            run_id="test_123#1",
            repetition_number=1,
            actual_output="",
            error="Test function failed",
            execution_metadata={"error_traceback": "ValueError: test error"},
        )

        assert context.error == "Test function failed"
        assert context.execution_metadata["error_traceback"] == "ValueError: test error"


class TestEvaluationMetric:
    """Test EvaluationMetric data model."""

    def test_evaluation_metric_creation(self):
        """Test basic EvaluationMetric creation."""
        metric = EvaluationMetric(
            name="accuracy",
            score=0.85,
            label="good",
            explanation="The response was mostly accurate",
            metadata={"confidence": 0.9, "details": {"correct": 4, "total": 5}},
        )

        assert metric.name == "accuracy"
        assert metric.score == 0.85
        assert metric.label == "good"
        assert metric.explanation == "The response was mostly accurate"
        assert metric.metadata["confidence"] == 0.9
        assert metric.metadata["details"]["correct"] == 4

    def test_evaluation_metric_to_dict(self):
        """Test EvaluationMetric dictionary conversion."""
        metric = EvaluationMetric(
            name="correctness", score=0.75, metadata={"reason": "Partially correct"}
        )

        result = metric.to_dict()

        assert result["name"] == "correctness"
        assert result["score"] == 0.75
        assert result["metadata"]["reason"] == "Partially correct"
        assert result["label"] is None
        assert result["explanation"] is None

    def test_evaluation_metric_minimal(self):
        """Test EvaluationMetric with minimal required fields."""
        metric = EvaluationMetric(name="simple", score=1.0)

        assert metric.name == "simple"
        assert metric.score == 1.0
        assert metric.label is None
        assert metric.explanation is None
        assert metric.metadata == {}
