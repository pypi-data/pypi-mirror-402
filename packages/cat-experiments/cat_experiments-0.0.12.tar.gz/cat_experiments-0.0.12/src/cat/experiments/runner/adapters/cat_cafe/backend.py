"""Cat Cafe storage backend implementing StorageBackend protocol.

This backend uses the Cat Cafe API to:
- Load datasets
- Create experiments and stream runs/evaluations
- Support resume via checking existing runs
"""

from __future__ import annotations

import inspect
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Mapping, Protocol, runtime_checkable

from ....protocol import (
    DatasetExample,
    ExperimentConfig,
    ExperimentResult,
    ExperimentSummary,
)

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from cat.cafe.client import CATCafeClient


# Fallback protocol/dataclass when SDK not installed
@runtime_checkable
class _CATCafeClientProtocol(Protocol):
    """Minimal protocol for CAT Cafe client interactions."""

    def start_experiment(self, experiment_config: Any) -> str: ...

    def create_run(self, experiment_id: str, payload: dict[str, Any]) -> dict[str, Any]: ...

    def append_evaluation(
        self, experiment_id: str, run_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]: ...

    def complete_experiment(self, experiment_id: str, summary: dict[str, Any]) -> None: ...

    def get_dataset_examples(
        self, dataset_id: str, **kwargs: Any
    ) -> list[dict[str, Any]] | dict[str, Any]: ...


@dataclass
class _CatCafeExperimentFallback:
    """Lightweight experiment representation when SDK unavailable."""

    name: str
    description: str
    dataset_id: str
    dataset_version: str | None = None
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class CatCafeStorageBackend:
    """Cat Cafe API implementation of StorageBackend protocol.

    This backend:
    - Loads datasets from Cat Cafe via the datasets API
    - Creates experiments and streams runs as they complete
    - Streams evaluations individually to Cat Cafe
    - Supports resume by fetching existing experiment runs
    """

    def __init__(
        self,
        client: CATCafeClient | _CATCafeClientProtocol | None = None,
        *,
        base_url: str | None = None,
    ) -> None:
        """Initialize CatCafeStorageBackend.

        Args:
            client: Existing CATCafeClient instance (optional)
            base_url: Cat Cafe server URL (uses CAT_BASE_URL env var if not provided)
        """
        if client is not None:
            self._client: _CATCafeClientProtocol = client  # type: ignore[assignment]
        else:
            import os

            try:
                from cat.cafe.client import CATCafeClient as _RealClient
            except ImportError as exc:  # pragma: no cover
                raise ImportError(
                    "Cat Cafe storage backend requires cat-cafe-client. "
                    "Install with: pip install cat-cafe-client"
                ) from exc

            resolved_url = base_url or os.getenv("CAT_BASE_URL", "http://localhost:8000")
            self._client = _RealClient(base_url=resolved_url)  # type: ignore[assignment]

        # State for current experiment
        self._remote_experiment_id: str | None = None
        self._dataset_id: str | None = None
        self._dataset_version_id: str | None = None
        self._run_id_map: dict[str, str] = {}  # local run_id -> remote run_id
        self._example_id_map: dict[str, str] = {}  # local example_id -> remote example_id
        self._experiment_started_at: datetime | None = None

    # -------------------------------------------------------------------------
    # Dataset loading
    # -------------------------------------------------------------------------

    def load_dataset(
        self,
        *,
        name: str | None = None,
        path: str | None = None,
        version: str | None = None,
    ) -> list[DatasetExample]:
        """Load a dataset from Cat Cafe.

        Args:
            name: Dataset name or ID
            path: Not used for Cat Cafe
            version: Optional dataset version

        Returns:
            List of dataset examples

        Raises:
            ValueError: If name not provided
        """
        if not name:
            raise ValueError("name is required for Cat Cafe storage backend")

        # Resolve dataset name to ID if needed
        dataset_id = self._resolve_dataset_id(name)

        examples_data = self._fetch_dataset_examples(dataset_id, version)

        # Store the resolved ID for later use (not the name)
        self._dataset_id = dataset_id
        self._dataset_version_id = version

        examples: list[DatasetExample] = []
        for item in examples_data:
            example = DatasetExample(
                id=item.get("id"),
                input=dict(item.get("input", {}) or item.get("input_data", {}) or {}),
                output=dict(item.get("output", {}) or {}),
                metadata=dict(item.get("metadata", {}) or {}),
            )
            # Store Cat Cafe metadata for later use (use resolved ID, not name)
            if dataset_id:
                example.metadata["cat_cafe_dataset_id"] = dataset_id
            if version:
                example.metadata["cat_cafe_dataset_version"] = version
            examples.append(example)

        return examples

    def _resolve_dataset_id(self, name: str) -> str:
        """Resolve a dataset name to its ID.

        Tries multiple resolution strategies:
        1. fetch_dataset_by_name (returns full dataset with ID)
        2. find_dataset_by_name (returns metadata with ID)
        3. Falls back to using name as ID
        """
        # Try fetch_dataset_by_name first
        fetch_by_name = getattr(self._client, "fetch_dataset_by_name", None)
        if callable(fetch_by_name):
            try:
                dataset_obj = fetch_by_name(name)
                if dataset_obj:
                    # Extract ID from dataset object
                    if isinstance(dataset_obj, dict):
                        dataset_id = dataset_obj.get("id") or dataset_obj.get("dataset_id")
                    else:
                        dataset_id = getattr(dataset_obj, "id", None) or getattr(
                            dataset_obj, "dataset_id", None
                        )
                    if dataset_id:
                        return str(dataset_id)
            except Exception:
                pass

        # Try find_dataset_by_name to resolve name -> ID
        find_by_name = getattr(self._client, "find_dataset_by_name", None)
        if callable(find_by_name):
            try:
                meta = find_by_name(name)
                if meta:
                    if isinstance(meta, dict):
                        dataset_id = meta.get("id") or meta.get("dataset_id")
                    else:
                        dataset_id = getattr(meta, "id", None) or getattr(meta, "dataset_id", None)
                    if dataset_id:
                        return str(dataset_id)
            except Exception:
                pass

        # Fallback: assume name is already an ID
        return name

    def _fetch_dataset_examples(self, dataset_id: str, version: str | None) -> list[dict[str, Any]]:
        """Fetch dataset examples with pagination support."""

        def _page_from_response(payload: Any) -> list[dict[str, Any]]:
            if isinstance(payload, list):
                return payload
            if isinstance(payload, dict) and "examples" in payload:
                nested = payload.get("examples")
                return nested if isinstance(nested, list) else []
            return []

        get_examples = getattr(self._client, "get_dataset_examples", None)
        if get_examples is None:
            raise RuntimeError("Cat Cafe client missing get_dataset_examples method.")

        sig = inspect.signature(get_examples)
        params = sig.parameters
        has_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
        supports_limit = "limit" in params or has_kwargs
        supports_offset = "offset" in params or has_kwargs

        common_kwargs: dict[str, Any] = {}
        if version is not None:
            common_kwargs["version"] = version

        # Paginate if SDK supports it
        if supports_limit or supports_offset:
            limit = 500
            offset = 0
            all_examples: list[dict[str, Any]] = []
            while True:
                page_kwargs = {**common_kwargs}
                if supports_limit:
                    page_kwargs["limit"] = limit
                if supports_offset:
                    page_kwargs["offset"] = offset
                payload = get_examples(dataset_id, **page_kwargs)
                page = _page_from_response(payload)
                all_examples.extend(page)
                if len(page) < limit:
                    break
                offset += limit
            return all_examples

        # Fallback: single call
        payload = get_examples(dataset_id, **common_kwargs)
        return _page_from_response(payload)

    # -------------------------------------------------------------------------
    # Experiment lifecycle
    # -------------------------------------------------------------------------

    def start_experiment(
        self,
        experiment_id: str,
        config: ExperimentConfig,
        examples: list[DatasetExample],
    ) -> None:
        """Create a new experiment in Cat Cafe.

        Uses dataset_id from config or from previously loaded dataset.
        """
        # Get dataset ID from config or cached value
        dataset_id = config.dataset_id or self._dataset_id
        dataset_version_id = config.dataset_version_id or self._dataset_version_id

        if not dataset_id:
            # Try to get from example metadata
            if examples and examples[0].metadata.get("cat_cafe_dataset_id"):
                dataset_id = examples[0].metadata["cat_cafe_dataset_id"]
                dataset_version_id = examples[0].metadata.get("cat_cafe_dataset_version")

        if not dataset_id:
            raise ValueError(
                "dataset_id required for Cat Cafe backend. "
                "Either load dataset via this backend or set config.dataset_id"
            )

        # Reset state
        self._run_id_map = {}
        self._example_id_map = {}
        self._dataset_id = dataset_id
        self._dataset_version_id = dataset_version_id
        self._experiment_started_at = datetime.now(timezone.utc)

        # Build example ID mapping for this dataset
        self._prepare_example_id_mapping(examples)

        # Create experiment config object
        try:
            from cat.cafe.client import Experiment as CatCafeExperiment

            cat_experiment: Any = CatCafeExperiment(
                name=config.name,
                description=config.description,
                dataset_id=dataset_id,
                dataset_version=dataset_version_id,
                tags=list(config.tags),
                metadata=dict(config.metadata),
            )
        except ImportError:
            cat_experiment = _CatCafeExperimentFallback(
                name=config.name,
                description=config.description,
                dataset_id=dataset_id,
                dataset_version=dataset_version_id,
                tags=list(config.tags),
                metadata=dict(config.metadata),
            )

        try:
            self._remote_experiment_id = self._client.start_experiment(cat_experiment)
        except Exception as exc:
            raise RuntimeError(f"Failed to create Cat Cafe experiment: {exc}") from exc

        if not self._remote_experiment_id:
            raise RuntimeError("Cat Cafe response missing experiment id")

    def save_run(
        self,
        experiment_id: str,
        result: ExperimentResult,
    ) -> None:
        """Submit a run to Cat Cafe."""
        if not self._remote_experiment_id:
            raise RuntimeError("Cat Cafe experiment not initialized")

        payload = self._build_run_payload(result)

        try:
            response = self._client.create_run(self._remote_experiment_id, payload)
        except Exception as exc:
            raise RuntimeError(f"Failed to submit Cat Cafe run: {exc}") from exc

        # Map local run_id to remote run_id
        remote_run_id = _extract_id(response, ["id", "run_id", "runId"])
        if remote_run_id:
            self._run_id_map[result.run_id] = remote_run_id

    def save_evaluation(
        self,
        experiment_id: str,
        run_id: str,
        evaluator_name: str,
        score: float,
        label: str | None,
        metadata: dict[str, object] | None,
    ) -> None:
        """Submit an evaluation to Cat Cafe."""
        if not self._remote_experiment_id:
            raise RuntimeError("Cat Cafe experiment not initialized")

        # Get remote run ID
        remote_run_id = self._run_id_map.get(run_id, run_id)

        # Build evaluation payload
        payload: dict[str, Any] = {
            "evaluator_name": evaluator_name,
            "score": score,
            "label": label,
        }

        if metadata:
            # Extract special fields
            meta_copy = dict(metadata)
            if "explanation" in meta_copy:
                payload["explanation"] = meta_copy.pop("explanation")
            if "trace_id" in meta_copy:
                payload["trace_id"] = meta_copy.pop("trace_id")
            if "started_at" in meta_copy:
                payload["started_at"] = meta_copy.pop("started_at")
            if "completed_at" in meta_copy:
                payload["completed_at"] = meta_copy.pop("completed_at")
            if "error" in meta_copy:
                payload["error"] = meta_copy.pop("error")
            payload["metadata"] = meta_copy

        try:
            self._client.append_evaluation(self._remote_experiment_id, remote_run_id, payload)
        except Exception as exc:
            raise RuntimeError(f"Failed to submit Cat Cafe evaluation: {exc}") from exc

    def complete_experiment(
        self,
        experiment_id: str,
        summary: ExperimentSummary,
    ) -> None:
        """Finalize experiment in Cat Cafe."""
        if not self._remote_experiment_id:
            return

        # Add Cat Cafe metadata to summary
        summary.aggregate_metadata.setdefault(
            "cat_cafe", {"experiment_id": self._remote_experiment_id}
        )

        summary_payload = self._build_summary_payload(summary)
        try:
            self._client.complete_experiment(self._remote_experiment_id, summary_payload)
        except Exception as exc:
            raise RuntimeError(f"Failed to complete Cat Cafe experiment: {exc}") from exc

    def fail_experiment(
        self,
        experiment_id: str,
        error: str,
    ) -> None:
        """Record experiment failure in Cat Cafe."""
        if not self._remote_experiment_id:
            return

        failure_summary = {
            "status": "failed",
            "error": error,
        }

        try:
            self._client.complete_experiment(self._remote_experiment_id, failure_summary)
        except Exception:
            # Best effort - don't raise on failure notification
            pass

    # -------------------------------------------------------------------------
    # Resume support
    # -------------------------------------------------------------------------

    def get_completed_runs(
        self,
        experiment_id: str,
    ) -> set[str] | None:
        """Get completed run IDs from Cat Cafe.

        Note: Cat Cafe doesn't have a direct API for this, so we fetch
        the experiment detail and extract completed run IDs.
        """
        try:
            get_detail = getattr(self._client, "get_experiment_detail", None)
            if not get_detail:
                return None

            detail = get_detail(experiment_id)
            if not detail:
                return None

            results = detail.get("results", [])
            if not results:
                return set()

            completed: set[str] = set()
            for result in results:
                run_id = result.get("run_id")
                error = result.get("error")
                # Only include successful runs
                if run_id and not error:
                    completed.add(run_id)

            return completed
        except Exception:
            return None

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _build_run_payload(self, result: ExperimentResult) -> dict[str, Any]:
        """Build Cat Cafe run payload from ExperimentResult."""
        run_id = result.run_id or f"{result.example_id}-rep-{result.repetition_number}"

        # Map example ID if we have a mapping
        example_id = self._example_id_map.get(result.example_id, result.example_id)

        # Build metadata
        metadata = dict(result.metadata)
        if result.started_at:
            metadata.setdefault("started_at", result.started_at.isoformat())
        if result.completed_at:
            metadata.setdefault("completed_at", result.completed_at.isoformat())
        metadata.setdefault("run_id", run_id)
        metadata.setdefault("repetition_number", result.repetition_number)
        if result.execution_time_ms is not None:
            metadata.setdefault("execution_time_ms", result.execution_time_ms)
        if result.error:
            metadata.setdefault("error", result.error)

        # Normalize actual output
        actual_output = result.actual_output
        if actual_output is None:
            actual_output = result.output
        actual_output = _normalize_output(actual_output)

        return {
            "run_id": run_id,
            "example_id": example_id,
            "repetition_number": result.repetition_number,
            "input_data": dict(result.input_data or {}),
            "output": dict(result.output or {}),
            "actual_output": actual_output,
            "trace_id": result.trace_id,
            "started_at": result.started_at.isoformat() if result.started_at else None,
            "completed_at": result.completed_at.isoformat() if result.completed_at else None,
            "execution_time_ms": result.execution_time_ms,
            "metadata": metadata,
        }

    def _build_summary_payload(self, summary: ExperimentSummary) -> dict[str, Any]:
        """Build Cat Cafe summary payload from ExperimentSummary."""
        payload: dict[str, Any] = {
            "total_examples": summary.total_examples,
            "successful_examples": summary.successful_examples,
            "failed_examples": summary.failed_examples,
            "average_scores": dict(summary.average_scores),
            "aggregate_scores": dict(summary.aggregate_scores),
            "aggregate_metadata": dict(summary.aggregate_metadata),
        }
        if summary.started_at:
            payload["started_at"] = summary.started_at.isoformat()
        if summary.completed_at:
            payload["completed_at"] = summary.completed_at.isoformat()
        if self._experiment_started_at:
            payload["listener_started_at"] = self._experiment_started_at.isoformat()
        return payload

    def _prepare_example_id_mapping(self, examples: list[DatasetExample]) -> None:
        """Align local DatasetExample IDs with remote dataset IDs."""
        if not self._dataset_id:
            return

        try:
            remote_examples = self._fetch_dataset_examples(
                self._dataset_id, self._dataset_version_id
            )
        except Exception:
            remote_examples = []

        if not remote_examples:
            # Use local IDs directly
            self._example_id_map = {str(ex.id): str(ex.id) for ex in examples if ex.id}
            return

        # Build signature-based mapping
        signature_to_id: dict[tuple[str, str], str] = {}
        for remote in remote_examples:
            remote_id = remote.get("id")
            if remote_id is None:
                continue
            signature_to_id.setdefault(_example_signature(remote), str(remote_id))

        mapping: dict[str, str] = {}
        for local in examples:
            if not local.id:
                continue
            local_dict = {
                "input": local.input,
                "output": local.output,
            }
            signature = _example_signature(local_dict)
            remote_id = signature_to_id.get(signature)
            if remote_id:
                mapping[str(local.id)] = remote_id

        # Fallback: positional matching
        if len(mapping) < len(examples) and len(remote_examples) == len(examples):
            for local, remote in zip(examples, remote_examples):
                if local.id and remote.get("id"):
                    mapping.setdefault(str(local.id), str(remote["id"]))

        self._example_id_map = mapping

    @property
    def remote_experiment_id(self) -> str | None:
        """Get the Cat Cafe experiment ID (for external reference)."""
        return self._remote_experiment_id


def _extract_id(response: Any, keys: list[str]) -> str | None:
    """Extract ID from response dict or object."""
    if isinstance(response, dict):
        for key in keys:
            value = response.get(key)
            if value is not None:
                return str(value)
    else:
        for key in keys:
            value = getattr(response, key, None)
            if value is not None:
                return str(value)
    return None


def _normalize_output(value: Any) -> str | dict[str, Any]:
    """Coerce output into JSON-safe form for Cat Cafe."""
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        return value
    return "" if value is None else repr(value)


def _example_signature(example: dict[str, Any] | Mapping[str, Any]) -> tuple[str, str]:
    """Stable signature combining input/output for mapping across sources."""
    input_data = example.get("input", {}) or example.get("input_data", {}) or {}
    output_data = example.get("output", {}) or {}
    return (
        json.dumps(input_data, sort_keys=True, ensure_ascii=False),
        json.dumps(output_data, sort_keys=True, ensure_ascii=False),
    )


__all__ = ["CatCafeStorageBackend"]
