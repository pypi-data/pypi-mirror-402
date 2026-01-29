"""Protocol types and serialization for cat-experiments.

This package contains the core data structures that define the interface
between components. All types are JSON-serializable and designed to be
portable across language boundaries.
"""

from __future__ import annotations

from .serde import (
    dataset_example_from_dict,
    dataset_example_to_dict,
    deserialize_datetime,
    experiment_config_from_dict,
    experiment_config_to_dict,
    experiment_result_from_dict,
    experiment_result_to_dict,
    experiment_summary_from_dict,
    experiment_summary_to_dict,
    serialize_datetime,
)
from .types import (
    AggregateEvaluationContext,
    DatasetExample,
    DiscoverResult,
    EvalInput,
    EvalOutput,
    EvalResult,
    EvaluationContext,
    EvaluationMetric,
    EvaluatorResult,
    ExperimentConfig,
    ExperimentResult,
    ExperimentSummary,
    InitRequest,
    InitResult,
    ShutdownResult,
    TaskInput,
    TaskOutput,
    TaskResult,
    TestCase,
    TestFunctionOutput,
)

__all__ = [
    # Types
    "DatasetExample",
    "TaskInput",
    "TaskOutput",
    "EvalInput",
    "EvalOutput",
    "ExperimentConfig",
    "ExperimentResult",
    "ExperimentSummary",
    "EvaluationContext",
    "EvaluationMetric",
    "TestCase",
    "AggregateEvaluationContext",
    "TestFunctionOutput",
    "EvaluatorResult",
    # Executor protocol messages
    "DiscoverResult",
    "InitRequest",
    "InitResult",
    "TaskResult",
    "EvalResult",
    "ShutdownResult",
    # Serde functions
    "serialize_datetime",
    "deserialize_datetime",
    "experiment_config_to_dict",
    "experiment_config_from_dict",
    "dataset_example_to_dict",
    "dataset_example_from_dict",
    "experiment_result_to_dict",
    "experiment_result_from_dict",
    "experiment_summary_to_dict",
    "experiment_summary_from_dict",
]
