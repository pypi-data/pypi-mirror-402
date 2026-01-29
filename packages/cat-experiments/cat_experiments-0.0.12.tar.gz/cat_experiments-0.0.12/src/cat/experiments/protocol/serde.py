"""Serialization helpers for persisting experiment artifacts.

This module provides convenience functions for serializing protocol types.
The actual to_dict/from_dict methods live on the types themselves in types.py.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from .types import (
    DatasetExample,
    ExperimentConfig,
    ExperimentResult,
    ExperimentSummary,
)


def serialize_datetime(value: datetime | None) -> str | None:
    """Convert datetime objects into ISO strings for persistence."""
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat()


def deserialize_datetime(value: Any) -> datetime | None:
    """Parse ISO timestamps (or epoch) back into timezone-aware datetimes."""
    if value in (None, ""):
        return None

    if isinstance(value, datetime):
        return value.astimezone(timezone.utc)

    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)

    if isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            return None
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            return None

    return None


# Convenience functions that delegate to type methods
# These are kept for backward compatibility with existing code


def experiment_config_to_dict(config: ExperimentConfig) -> dict[str, Any]:
    """Convert ExperimentConfig to dictionary."""
    return config.to_dict()


def experiment_config_from_dict(payload: Mapping[str, Any]) -> ExperimentConfig:
    """Create ExperimentConfig from dictionary."""
    return ExperimentConfig.from_dict(dict(payload))


def dataset_example_to_dict(example: DatasetExample) -> dict[str, Any]:
    """Convert DatasetExample to dictionary."""
    return example.to_dict()


def dataset_example_from_dict(payload: Mapping[str, Any]) -> DatasetExample:
    """Create DatasetExample from dictionary."""
    return DatasetExample.from_dict(dict(payload))


def experiment_result_to_dict(result: ExperimentResult) -> dict[str, Any]:
    """Convert ExperimentResult to dictionary."""
    return result.to_dict()


def experiment_result_from_dict(payload: Mapping[str, Any]) -> ExperimentResult:
    """Create ExperimentResult from dictionary."""
    return ExperimentResult.from_dict(dict(payload))


def experiment_summary_to_dict(summary: ExperimentSummary) -> dict[str, Any]:
    """Convert ExperimentSummary to dictionary."""
    return summary.to_dict()


def experiment_summary_from_dict(
    payload: Mapping[str, Any], *, config: ExperimentConfig
) -> ExperimentSummary:
    """Create ExperimentSummary from dictionary."""
    return ExperimentSummary.from_dict(dict(payload), config=config)


__all__ = [
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
