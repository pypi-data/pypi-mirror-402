"""Core protocol types for cat-experiments.

These types define the JSON-serializable data structures that flow between
components. They are designed to be language-agnostic and portable.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

# -----------------------------------------------------------------------------
# DateTime helpers (inline to avoid circular imports)
# -----------------------------------------------------------------------------


def _ensure_datetime(value: datetime | str | int | float | None) -> datetime | None:
    """Parse various datetime representations into timezone-aware datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    if isinstance(value, str):
        normalized = value.strip()
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            return None
    return None


def _serialize_datetime(value: datetime | None) -> str | None:
    """Convert datetime to ISO string."""
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat()


# -----------------------------------------------------------------------------
# Dataset types
# -----------------------------------------------------------------------------


@dataclass
class DatasetExample:
    """Dataset example structure aligned with external evaluation tooling expectations."""

    input: dict[str, Any]
    """Arbitrary structured input payload (e.g. {"messages": [...]})."""

    output: dict[str, Any]
    """Reference/expected output payload (e.g. {"messages": [...]})."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional context such as tags or trace provenance."""

    id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.id is None:
            self.id = str(uuid4())
        self.created_at = _ensure_datetime(self.created_at) or datetime.now(timezone.utc)
        self.updated_at = _ensure_datetime(self.updated_at) or self.created_at

    @property
    def tags(self) -> list[str]:
        """Tags are persisted within metadata."""
        return list(self.metadata.get("tags", []))

    @tags.setter
    def tags(self, value: list[str]) -> None:
        self.metadata["tags"] = list(value)

    @property
    def source_trace_id(self) -> str | None:
        """Trace identifier stored in metadata for provenance."""
        return self.metadata.get("source_trace_id")

    @source_trace_id.setter
    def source_trace_id(self, value: str | None) -> None:
        if value is None:
            self.metadata.pop("source_trace_id", None)
        else:
            self.metadata["source_trace_id"] = value

    @property
    def source_node_id(self) -> str | None:
        """Node identifier stored in metadata for provenance."""
        return self.metadata.get("source_node_id")

    @source_node_id.setter
    def source_node_id(self, value: str | None) -> None:
        if value is None:
            self.metadata.pop("source_node_id", None)
        else:
            self.metadata["source_node_id"] = value

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "input": self.input,
            "output": self.output,
            "metadata": self.metadata,
            "created_at": _serialize_datetime(self.created_at),
            "updated_at": _serialize_datetime(self.updated_at),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DatasetExample:
        """Create from dictionary."""
        metadata = dict(payload.get("metadata", {}))
        tags = payload.get("tags")
        if tags and "tags" not in metadata:
            metadata["tags"] = list(tags)
        for key in ("source_trace_id", "source_node_id", "expected_tool_calls"):
            value = payload.get(key)
            if value is not None and key not in metadata:
                metadata[key] = value

        return cls(
            input=dict(payload.get("input", {})),
            output=dict(payload.get("output", {})),
            metadata=metadata,
            id=payload.get("id"),
            created_at=_ensure_datetime(payload.get("created_at")),
            updated_at=_ensure_datetime(payload.get("updated_at")),
        )


# -----------------------------------------------------------------------------
# Task protocol types (CLI subprocess communication)
# -----------------------------------------------------------------------------


@dataclass
class TaskInput:
    """JSON input to a task subprocess."""

    id: str
    input: dict[str, Any]
    output: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None

    # Runner context
    experiment_id: str | None = None
    run_id: str | None = None
    repetition_number: int | None = None

    # Experiment parameters
    params: dict[str, Any] = field(default_factory=dict)

    # Trace context for span propagation (from Go CLI)
    trace_id: str | None = None
    parent_span_id: str | None = None

    @classmethod
    def from_dataset_example(
        cls,
        example: DatasetExample,
        *,
        experiment_id: str | None = None,
        run_id: str | None = None,
        repetition_number: int | None = None,
        params: dict[str, Any] | None = None,
    ) -> TaskInput:
        """Create TaskInput from a DatasetExample."""
        return cls(
            id=example.id or "",
            input=dict(example.input),
            output=dict(example.output) if example.output else None,
            metadata=dict(example.metadata) if example.metadata else None,
            experiment_id=experiment_id,
            run_id=run_id,
            repetition_number=repetition_number,
            params=params or {},
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(asdict(self))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_json(cls, data: str) -> TaskInput:
        """Deserialize from JSON string."""
        payload = json.loads(data)
        return cls.from_dict(payload)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> TaskInput:
        """Create from dictionary."""
        return cls(
            id=payload["id"],
            input=payload.get("input", {}),
            output=payload.get("output"),
            metadata=payload.get("metadata"),
            experiment_id=payload.get("experiment_id"),
            run_id=payload.get("run_id"),
            repetition_number=payload.get("repetition_number"),
            params=payload.get("params", {}),
            trace_id=payload.get("trace_id"),
            parent_span_id=payload.get("parent_span_id"),
        )


@dataclass
class TaskOutput:
    """JSON output from a task subprocess.

    The output can be any JSON-serializable value. If you need to include
    tool calls for evaluation, include them in the output dict:

        return TaskOutput(output={
            "answer": "...",
            "tool_calls": [{"name": "search", "args": {...}}],
        })
    """

    output: str | dict[str, Any] | list[Any] | None
    metadata: dict[str, Any] | None = None
    error: str | None = None

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(asdict(self))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_json(cls, data: str) -> TaskOutput:
        """Deserialize from JSON string."""
        payload = json.loads(data)
        return cls.from_dict(payload)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> TaskOutput:
        """Create from dictionary."""
        return cls(
            output=payload.get("output"),
            metadata=payload.get("metadata"),
            error=payload.get("error"),
        )


# -----------------------------------------------------------------------------
# Evaluator protocol types (CLI subprocess communication)
# -----------------------------------------------------------------------------


@dataclass
class EvalInput:
    """JSON input to an evaluator subprocess.

    Tool calls can be extracted from task_spans using extract_tool_calls():

        from cat.experiments.sdk.tracing import extract_tool_calls
        tool_calls = extract_tool_calls(input.task_spans or [])
    """

    example: dict[str, Any]  # TaskInput as dict
    actual_output: Any
    expected_output: Any | None = None
    task_metadata: dict[str, Any] | None = None

    # Experiment parameters
    params: dict[str, Any] = field(default_factory=dict)

    # Spans captured during task execution (for extracting tool calls, etc.)
    task_spans: list[dict[str, Any]] | None = None

    # Run correlation and trace context for span propagation (from Go CLI)
    run_id: str | None = None
    trace_id: str | None = None
    parent_span_id: str | None = None

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(asdict(self))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_json(cls, data: str) -> EvalInput:
        """Deserialize from JSON string."""
        payload = json.loads(data)
        return cls.from_dict(payload)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> EvalInput:
        """Create from dictionary."""
        return cls(
            example=payload["example"],
            actual_output=payload["actual_output"],
            expected_output=payload.get("expected_output"),
            task_metadata=payload.get("task_metadata"),
            params=payload.get("params", {}),
            task_spans=payload.get("task_spans"),
            run_id=payload.get("run_id"),
            trace_id=payload.get("trace_id"),
            parent_span_id=payload.get("parent_span_id"),
        )

    @classmethod
    def from_evaluation_context(
        cls,
        context: EvaluationContext,
        *,
        params: dict[str, Any] | None = None,
    ) -> EvalInput:
        """Create EvalInput from an EvaluationContext."""
        example_dict = {
            "id": context.example_id,
            "input": context.input,
            "output": context.output,
            "metadata": context.metadata,
        }

        return cls(
            example=example_dict,
            actual_output=context.actual_output,
            expected_output=context.output,
            task_metadata=context.execution_metadata,
            params=params or {},
        )


@dataclass
class EvalOutput:
    """JSON output from an evaluator subprocess."""

    score: float
    label: str | None = None
    metadata: dict[str, Any] | None = None
    explanation: str | None = None
    """Optional human-readable explanation (e.g., LLM-as-judge reasoning)"""

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(asdict(self))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_json(cls, data: str) -> EvalOutput:
        """Deserialize from JSON string."""
        payload = json.loads(data)
        return cls.from_dict(payload)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> EvalOutput:
        """Create from dictionary."""
        return cls(
            score=float(payload["score"]),
            label=payload.get("label"),
            metadata=payload.get("metadata"),
            explanation=payload.get("explanation"),
        )


# -----------------------------------------------------------------------------
# Experiment configuration and results
# -----------------------------------------------------------------------------


@dataclass
class ExperimentConfig:
    """Configuration for an experiment run."""

    name: str
    description: str = ""
    dataset_id: str | None = None
    dataset_version_id: str | None = None
    project_name: str | None = None
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    params: dict[str, Any] = field(default_factory=dict)
    """User-defined experiment parameters (e.g. model, prompt_version, temperature)."""
    repetitions: int = 1
    """Number of times to execute each selected example."""
    preview_examples: int | None = None
    """Optional preview subset size. None means run all examples."""
    preview_seed: int = 42
    """Deterministic seed for preview example selection."""
    max_workers: int = 1

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "dataset_id": self.dataset_id,
            "dataset_version_id": self.dataset_version_id,
            "project_name": self.project_name,
            "tags": list(self.tags),
            "metadata": dict(self.metadata),
            "params": dict(self.params),
            "repetitions": self.repetitions,
            "preview_examples": self.preview_examples,
            "preview_seed": self.preview_seed,
            "max_workers": self.max_workers,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ExperimentConfig:
        """Create from dictionary."""
        return cls(
            name=payload["name"],
            description=payload.get("description", ""),
            dataset_id=payload.get("dataset_id"),
            dataset_version_id=payload.get("dataset_version_id"),
            project_name=payload.get("project_name"),
            tags=list(payload.get("tags", [])),
            metadata=dict(payload.get("metadata", {})),
            params=dict(payload.get("params", {})),
            repetitions=int(payload.get("repetitions") or 1),
            preview_examples=payload.get("preview_examples"),
            preview_seed=payload.get("preview_seed", 42),
            max_workers=int(payload.get("max_workers") or 1),
        )


@dataclass
class ExperimentResult:
    """Complete result from processing a single dataset example."""

    example_id: str
    run_id: str
    repetition_number: int
    started_at: datetime | None
    completed_at: datetime | None
    input_data: dict[str, Any]
    output: dict[str, Any]
    actual_output: str | dict[str, Any] | list[Any] | None
    evaluation_scores: dict[str, float]
    evaluator_metadata: dict[str, dict[str, Any]]
    metadata: dict[str, Any]
    trace_id: str | None = None
    error: str | None = None
    execution_time_ms: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "example_id": self.example_id,
            "run_id": self.run_id,
            "repetition_number": self.repetition_number,
            "started_at": _serialize_datetime(self.started_at),
            "completed_at": _serialize_datetime(self.completed_at),
            "input_data": self.input_data,
            "output": self.output,
            "actual_output": self.actual_output,
            "evaluation_scores": self.evaluation_scores,
            "evaluator_metadata": self.evaluator_metadata,
            "metadata": self.metadata,
            "trace_id": self.trace_id,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ExperimentResult:
        """Create from dictionary."""
        return cls(
            example_id=payload["example_id"],
            run_id=payload.get("run_id") or payload["example_id"],
            repetition_number=int(payload.get("repetition_number") or 1),
            started_at=_ensure_datetime(payload.get("started_at")),
            completed_at=_ensure_datetime(payload.get("completed_at")),
            input_data=dict(payload.get("input_data", {})),
            output=dict(payload.get("output", {})),
            actual_output=payload.get("actual_output"),
            evaluation_scores=dict(payload.get("evaluation_scores", {})),
            evaluator_metadata=dict(payload.get("evaluator_metadata", {})),
            metadata=dict(payload.get("metadata", {})),
            trace_id=payload.get("trace_id"),
            error=payload.get("error"),
            execution_time_ms=payload.get("execution_time_ms"),
        )


@dataclass
class ExperimentSummary:
    """Summary statistics for a completed experiment."""

    total_examples: int
    successful_examples: int
    failed_examples: int
    average_scores: dict[str, float]
    total_execution_time_ms: float
    experiment_id: str
    config: ExperimentConfig
    started_at: datetime
    completed_at: datetime | None = None
    aggregate_scores: dict[str, float] = field(default_factory=dict)
    aggregate_metadata: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "total_examples": self.total_examples,
            "successful_examples": self.successful_examples,
            "failed_examples": self.failed_examples,
            "average_scores": self.average_scores,
            "aggregate_scores": self.aggregate_scores,
            "aggregate_metadata": self.aggregate_metadata,
            "total_execution_time_ms": self.total_execution_time_ms,
            "experiment_id": self.experiment_id,
            "started_at": _serialize_datetime(self.started_at),
            "completed_at": _serialize_datetime(self.completed_at),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any], *, config: ExperimentConfig) -> ExperimentSummary:
        """Create from dictionary."""
        started_at = _ensure_datetime(payload.get("started_at")) or datetime.now(timezone.utc)
        completed_at = _ensure_datetime(payload.get("completed_at"))
        return cls(
            total_examples=int(payload.get("total_examples") or 0),
            successful_examples=int(payload.get("successful_examples") or 0),
            failed_examples=int(payload.get("failed_examples") or 0),
            average_scores=dict(payload.get("average_scores", {})),
            aggregate_scores=dict(payload.get("aggregate_scores", {})),
            aggregate_metadata=dict(payload.get("aggregate_metadata", {})),
            total_execution_time_ms=float(payload.get("total_execution_time_ms") or 0.0),
            experiment_id=payload.get("experiment_id") or config.name,
            config=config,
            started_at=started_at,
            completed_at=completed_at,
        )


# -----------------------------------------------------------------------------
# Evaluation context types (used by evaluators)
# -----------------------------------------------------------------------------


@dataclass
class EvaluationContext:
    """Rich evaluation context providing evaluators with all available data.

    Gives evaluators access to:
    - Original dataset input/output (flexible dicts)
    - Actual output from test function
    - Execution metadata and timing
    - Full context for sophisticated evaluation logic
    """

    example_id: str
    run_id: str
    repetition_number: int
    actual_output: Any
    """The actual output from the test function (string, dict, etc.)"""

    # Flexible input/output from dataset example
    input: dict[str, Any] = field(default_factory=dict)
    """Original input data from dataset example"""

    output: dict[str, Any] = field(default_factory=dict)
    """Reference output data from dataset example"""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Full metadata from original dataset example"""

    # Execution context
    started_at: datetime | None = None
    """UTC timestamp when execution for this context started"""

    completed_at: datetime | None = None
    """UTC timestamp when execution for this context completed"""

    execution_time_ms: float | None = None
    error: str | None = None
    execution_metadata: dict[str, Any] = field(default_factory=dict)
    """Additional execution context (traces, performance, etc.)"""

    trace_id: str | None = None
    """Trace identifier captured during execution, if available"""

    params: dict[str, Any] = field(default_factory=dict)
    """Experiment parameters passed from ExperimentConfig."""


@dataclass
class EvaluationMetric:
    """Structured evaluation result with rich metadata support."""

    name: str
    """Name of the evaluation metric"""

    score: float
    """Numerical score (0.0 to 1.0 typical, but not enforced)"""

    metadata: dict[str, Any] = field(default_factory=dict)
    """
    Rich metadata about the evaluation:
    - Reasoning: {"reason": "Response includes required information"}
    - Confidence: {"confidence": 0.95}
    - Breakdown: {"accuracy": 0.9, "completeness": 0.8}
    - Custom: {"any_field": "any_value"}
    """

    label: str | None = None
    """Optional categorical label (e.g., "good", "bad", "correct")"""

    explanation: str | None = None
    """Optional human-readable explanation"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "score": self.score,
            "metadata": self.metadata,
            "label": self.label,
            "explanation": self.explanation,
        }


@dataclass
class TestCase:
    """Describes a planned execution of a dataset example (input to the runner)."""

    example: DatasetExample
    repetition_number: int = 1
    run_id: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    """Experiment parameters passed from ExperimentConfig."""
    __test__ = False  # Prevent pytest from treating this as a test container

    def __post_init__(self) -> None:
        if self.repetition_number < 1:
            raise ValueError("repetition_number must be >= 1")
        if not self.run_id:
            if self.example.id:
                self.run_id = f"{self.example.id}#{self.repetition_number}"
            else:
                self.run_id = uuid4().hex

    @property
    def example_id(self) -> str:
        """Convenience accessor for the underlying example ID."""
        return self.example.id or ""


@dataclass
class AggregateEvaluationContext:
    """Context passed to aggregate evaluators.

    Provides access to the full run: raw contexts, example results, config,
    examples, and experiment metadata.
    """

    experiment_id: str
    config: ExperimentConfig
    contexts: list[EvaluationContext]
    results: list[ExperimentResult]
    examples: list[DatasetExample]
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @property
    def total_examples(self) -> int:
        """Total number of runs executed."""
        return len(self.results)

    @property
    def successful_examples(self) -> int:
        """Number of runs without errors."""
        return len([r for r in self.results if not getattr(r, "error", None)])

    @property
    def failed_examples(self) -> int:
        """Number of runs that failed."""
        return self.total_examples - self.successful_examples


# -----------------------------------------------------------------------------
# Executor Protocol Messages
# -----------------------------------------------------------------------------
# These types define the message format for communication between the
# orchestrator and executor (in-process or subprocess).


@dataclass
class DiscoverResult:
    """Response from executor discover command.

    Returns metadata about the experiment file: task name, evaluators,
    default params, etc.
    """

    protocol_version: str = "1.0"
    name: str | None = None
    description: str | None = None
    task: str | None = None
    evaluators: list[str] = field(default_factory=list)
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocol_version": self.protocol_version,
            "name": self.name,
            "description": self.description,
            "task": self.task,
            "evaluators": self.evaluators,
            "params": self.params,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DiscoverResult:
        return cls(
            protocol_version=payload.get("protocol_version", "1.0"),
            name=payload.get("name"),
            description=payload.get("description"),
            task=payload.get("task"),
            evaluators=list(payload.get("evaluators", [])),
            params=dict(payload.get("params", {})),
        )


@dataclass
class InitRequest:
    """Request to initialize the executor."""

    max_workers: int = 1
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_workers": self.max_workers,
            "params": self.params,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> InitRequest:
        return cls(
            max_workers=int(payload.get("max_workers", 1)),
            params=dict(payload.get("params", {})),
        )


@dataclass
class InitResult:
    """Response from executor init command."""

    ok: bool = True
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"ok": self.ok}
        if self.error:
            result["error"] = self.error
        return result

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> InitResult:
        return cls(
            ok=bool(payload.get("ok", True)),
            error=payload.get("error"),
        )


@dataclass
class TaskResult:
    """Single task result streamed from executor."""

    run_id: str
    output: str | dict[str, Any] | list[Any] | None = None
    metadata: dict[str, Any] | None = None
    error: str | None = None
    # Child spans captured during execution
    spans: list[dict[str, Any]] | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"run_id": self.run_id}
        if self.output is not None:
            result["output"] = self.output
        if self.metadata:
            result["metadata"] = self.metadata
        if self.error:
            result["error"] = self.error
        if self.spans:
            result["spans"] = self.spans
        return result

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> TaskResult:
        return cls(
            run_id=payload["run_id"],
            output=payload.get("output"),
            metadata=payload.get("metadata"),
            error=payload.get("error"),
            spans=payload.get("spans"),
        )


@dataclass
class EvalResult:
    """Single evaluation result streamed from executor."""

    run_id: str
    evaluator: str
    score: float
    label: str | None = None
    metadata: dict[str, Any] | None = None
    error: str | None = None
    explanation: str | None = None
    """Optional human-readable explanation (e.g., LLM-as-judge reasoning)"""
    # Child spans captured during evaluation
    spans: list[dict[str, Any]] | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "run_id": self.run_id,
            "evaluator": self.evaluator,
            "score": self.score,
        }
        if self.label:
            result["label"] = self.label
        if self.metadata:
            result["metadata"] = self.metadata
        if self.error:
            result["error"] = self.error
        if self.explanation:
            result["explanation"] = self.explanation
        if self.spans:
            result["spans"] = self.spans
        return result

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> EvalResult:
        return cls(
            run_id=payload["run_id"],
            evaluator=payload["evaluator"],
            score=float(payload.get("score", 0.0)),
            label=payload.get("label"),
            metadata=payload.get("metadata"),
            error=payload.get("error"),
            explanation=payload.get("explanation"),
            spans=payload.get("spans"),
        )


@dataclass
class ShutdownResult:
    """Response from executor shutdown command."""

    ok: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ShutdownResult:
        return cls(ok=bool(payload.get("ok", True)))


# -----------------------------------------------------------------------------
# Type aliases
# -----------------------------------------------------------------------------

# Type alias for test function output - simple types only
TestFunctionOutput = str | dict[str, Any] | list[Any]

# Type alias for evaluator results
EvaluatorResult = float | tuple[float, dict[str, Any]] | EvaluationMetric


__all__ = [
    # Dataset types
    "DatasetExample",
    # Task protocol
    "TaskInput",
    "TaskOutput",
    # Evaluator protocol
    "EvalInput",
    "EvalOutput",
    # Experiment types
    "ExperimentConfig",
    "ExperimentResult",
    "ExperimentSummary",
    # Evaluation context
    "EvaluationContext",
    "EvaluationMetric",
    "TestCase",
    "AggregateEvaluationContext",
    # Executor protocol messages
    "DiscoverResult",
    "InitRequest",
    "InitResult",
    "TaskResult",
    "EvalResult",
    "ShutdownResult",
    # Type aliases
    "TestFunctionOutput",
    "EvaluatorResult",
]
