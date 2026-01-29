"""Phoenix storage backend implementing StorageBackend protocol.

This backend uses the Phoenix API to:
- Load datasets
- Create experiments and stream runs/evaluations
- Support resume via incomplete-runs endpoint
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Mapping

try:
    import httpx
    from phoenix.client import Client as PhoenixClient
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "Phoenix storage backend requires phoenix-client. "
        "Install with: pip install arize-phoenix-client"
    ) from exc

from ....protocol import (
    DatasetExample,
    ExperimentConfig,
    ExperimentResult,
    ExperimentSummary,
)

if TYPE_CHECKING:
    pass


class PhoenixStorageBackend:
    """Phoenix API implementation of StorageBackend protocol.

    This backend:
    - Loads datasets from Phoenix via the datasets API
    - Creates experiments and streams runs as they complete
    - Streams evaluations individually to Phoenix
    - Supports resume via the incomplete-runs endpoint
    """

    def __init__(
        self,
        client: PhoenixClient | None = None,
        *,
        base_url: str | None = None,
        timeout: int = 60,
    ) -> None:
        """Initialize PhoenixStorageBackend.

        Args:
            client: Existing PhoenixClient instance (optional)
            base_url: Phoenix server URL (uses PHOENIX_BASE_URL env var if not provided)
            timeout: HTTP timeout in seconds
        """
        if client is not None:
            self._client = client
        else:
            url = base_url or os.environ.get("PHOENIX_BASE_URL")
            client_kwargs: dict[str, Any] = {}
            if url:
                client_kwargs["base_url"] = url
            self._client = PhoenixClient(**client_kwargs)

        self._http: httpx.Client = self._client._client  # type: ignore[attr-defined]
        self._timeout = timeout

        # State for current experiment
        self._remote_experiment_id: str | None = None
        self._dataset_id: str | None = None
        self._dataset_version_id: str | None = None
        self._run_id_map: dict[str, str] = {}  # local run_id -> remote run_id

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
        """Load a dataset from Phoenix.

        Args:
            name: Dataset name or ID
            path: Not used for Phoenix
            version: Optional dataset version ID

        Returns:
            List of dataset examples with phoenix metadata

        Raises:
            ValueError: If name not provided
        """
        if not name:
            raise ValueError("name is required for Phoenix storage backend")

        dataset = self._client.datasets.get_dataset(  # type: ignore[attr-defined]
            dataset=name,
            version_id=version,
        )

        # Extract dataset ID and version
        dataset_id = _get_attr(dataset, "id")
        dataset_version_id = _get_attr(dataset, "version_id")

        # Store for later use
        self._dataset_id = dataset_id
        self._dataset_version_id = dataset_version_id

        # Extract examples
        examples_data = _extract_examples(dataset)
        examples: list[DatasetExample] = []

        for item in examples_data:
            example = DatasetExample(
                id=item.get("id"),
                input=dict(item.get("input", {})),
                output=dict(item.get("output", {})),
                metadata=dict(item.get("metadata", {})),
            )
            # Store Phoenix metadata for later use
            if dataset_id:
                example.metadata["phoenix_dataset_id"] = dataset_id
            if dataset_version_id:
                example.metadata["phoenix_dataset_version_id"] = dataset_version_id
            examples.append(example)

        return examples

    # -------------------------------------------------------------------------
    # Experiment lifecycle
    # -------------------------------------------------------------------------

    def start_experiment(
        self,
        experiment_id: str,
        config: ExperimentConfig,
        examples: list[DatasetExample],
    ) -> None:
        """Create a new experiment in Phoenix.

        Uses dataset_id from config or from previously loaded dataset.
        """
        # Get dataset ID from config or cached value
        dataset_id = config.dataset_id or self._dataset_id
        dataset_version_id = config.dataset_version_id or self._dataset_version_id

        if not dataset_id:
            # Try to get from example metadata
            if examples and examples[0].metadata.get("phoenix_dataset_id"):
                dataset_id = examples[0].metadata["phoenix_dataset_id"]
                dataset_version_id = examples[0].metadata.get("phoenix_dataset_version_id")

        if not dataset_id:
            raise ValueError(
                "dataset_id required for Phoenix backend. "
                "Either load dataset via this backend or set config.dataset_id"
            )

        # Reset state
        self._run_id_map = {}
        self._dataset_id = dataset_id
        self._dataset_version_id = dataset_version_id

        # Build metadata
        metadata: dict[str, Any] = dict(config.metadata)
        if config.params:
            metadata["params"] = config.params

        # Create experiment via Phoenix client
        try:
            experiment = self._client.experiments.create(  # type: ignore[attr-defined]
                dataset_id=dataset_id,
                dataset_version_id=dataset_version_id,
                experiment_name=config.name,
                experiment_description=config.description,
                experiment_metadata=metadata,
                repetitions=config.repetitions,
                timeout=self._timeout,
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to create Phoenix experiment: {exc}") from exc

        self._remote_experiment_id = experiment.get("id")
        if not self._remote_experiment_id:
            raise RuntimeError("Phoenix response missing experiment id")

    def save_run(
        self,
        experiment_id: str,
        result: ExperimentResult,
    ) -> None:
        """Submit a run to Phoenix."""
        if not self._remote_experiment_id:
            raise RuntimeError("Phoenix experiment not initialized")

        payload = self._build_run_payload(result)

        try:
            response = self._http.post(
                f"v1/experiments/{self._remote_experiment_id}/runs",
                json=payload,
                timeout=self._timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Failed to submit Phoenix run: {exc}") from exc

        # Map local run_id to remote run_id
        remote_run_id = response.json().get("data", {}).get("id")
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
        """Submit an evaluation to Phoenix."""
        if not self._remote_experiment_id:
            raise RuntimeError("Phoenix experiment not initialized")

        # Get remote run ID
        remote_run_id = self._run_id_map.get(run_id, run_id)

        # Build evaluation payload
        payload: dict[str, Any] = {
            "experiment_run_id": remote_run_id,
            "name": evaluator_name,
            "annotator_kind": "CODE",
            "result": {"score": score},
        }

        if label is not None:
            payload["result"]["label"] = label

        if metadata:
            # Extract special fields
            if "explanation" in metadata:
                payload["result"]["explanation"] = metadata["explanation"]
            if "trace_id" in metadata:
                payload["trace_id"] = metadata["trace_id"]

        # Add timestamps
        now = datetime.now(timezone.utc).isoformat()
        payload["start_time"] = now
        payload["end_time"] = now

        try:
            response = self._http.post(
                "v1/experiment_evaluations",
                json=payload,
                timeout=self._timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Failed to submit Phoenix evaluation: {exc}") from exc

    def complete_experiment(
        self,
        experiment_id: str,
        summary: ExperimentSummary,
    ) -> None:
        """Finalize experiment in Phoenix.

        Phoenix experiments are auto-completed when all runs are submitted,
        so this is mostly a no-op. We store the remote experiment ID in
        the summary for reference.
        """
        if self._remote_experiment_id:
            summary.aggregate_metadata.setdefault(
                "phoenix", {"experiment_id": self._remote_experiment_id}
            )

    def fail_experiment(
        self,
        experiment_id: str,
        error: str,
    ) -> None:
        """Record experiment failure.

        Phoenix doesn't have explicit failure tracking, so we just log it.
        """
        # Phoenix doesn't have an explicit failure endpoint
        # The experiment will show as incomplete
        pass

    # -------------------------------------------------------------------------
    # Resume support
    # -------------------------------------------------------------------------

    def get_completed_runs(
        self,
        experiment_id: str,
    ) -> set[str] | None:
        """Get completed run IDs from Phoenix.

        Uses the incomplete-runs endpoint to determine what's NOT done,
        then inverts to get what IS done.
        """
        try:
            # First get the experiment to check if it exists
            self._client.experiments.get(experiment_id=experiment_id)  # type: ignore[attr-defined]
        except Exception:
            return None

        # Get all runs for the experiment
        all_runs: set[str] = set()
        incomplete_runs: set[str] = set()

        # Fetch all runs
        try:
            response = self._http.get(
                f"v1/experiments/{experiment_id}/runs",
                timeout=self._timeout,
            )
            response.raise_for_status()
            runs_data = response.json().get("data", [])
            for run in runs_data:
                run_id = run.get("id")
                if run_id:
                    all_runs.add(run_id)
        except httpx.HTTPError:
            pass

        # Fetch incomplete runs
        cursor: str | None = None
        while True:
            params: dict[str, Any] = {"limit": 100}
            if cursor:
                params["cursor"] = cursor

            try:
                response = self._http.get(
                    f"v1/experiments/{experiment_id}/incomplete-runs",
                    params=params,
                    timeout=self._timeout,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 404:
                    # Endpoint not available, assume all runs are complete
                    return all_runs
                raise

            body = response.json()
            data = body.get("data", [])
            if not data:
                break

            for incomplete in data:
                # Get the run IDs that are incomplete
                example = incomplete.get("dataset_example", {})
                example_id = example.get("id", "")
                reps = incomplete.get("repetition_numbers", [])
                for rep in reps:
                    # Build the run_id in the same format we use
                    incomplete_runs.add(f"{example_id}#{rep}")

            cursor = body.get("next_cursor")
            if not cursor:
                break

        # Return completed = all - incomplete
        # But we need to map between Phoenix run IDs and our run_id format
        # For now, just return all_runs since Phoenix tracks by its own IDs
        return all_runs - incomplete_runs if incomplete_runs else all_runs

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _build_run_payload(self, result: ExperimentResult) -> dict[str, Any]:
        """Build Phoenix run payload from ExperimentResult."""
        output = result.actual_output
        if output is None:
            output = result.output

        payload: dict[str, Any] = {
            "dataset_example_id": result.example_id,
            "output": _ensure_json_safe(output),
            "repetition_number": result.repetition_number,
        }

        # Add timestamps
        if result.started_at:
            payload["start_time"] = result.started_at.isoformat()
        if result.completed_at:
            payload["end_time"] = result.completed_at.isoformat()

        # Add error if present
        if result.error:
            payload["error"] = result.error

        # Add trace_id if available
        if result.trace_id:
            payload["trace_id"] = result.trace_id

        return payload

    @property
    def remote_experiment_id(self) -> str | None:
        """Get the Phoenix experiment ID (for external reference)."""
        return self._remote_experiment_id


def _get_attr(obj: Any, name: str) -> Any:
    """Get attribute from object or dict."""
    if isinstance(obj, Mapping):
        return obj.get(name)
    return getattr(obj, name, None)


def _extract_examples(dataset_obj: Any) -> list[dict[str, Any]]:
    """Extract examples list from various dataset object shapes."""
    # Direct examples attribute
    examples = getattr(dataset_obj, "examples", None)
    if examples is not None:
        return _normalize_examples(examples)

    # Nested dataset.examples
    nested = getattr(dataset_obj, "dataset", None)
    if nested:
        examples = getattr(nested, "examples", None)
        if examples is not None:
            return _normalize_examples(examples)

    # Dict with examples key
    if isinstance(dataset_obj, dict):
        examples = dataset_obj.get("examples", [])
        return _normalize_examples(examples)

    return []


def _normalize_examples(examples: list[Any]) -> list[dict[str, Any]]:
    """Normalize examples to list of dicts."""
    result = []
    for ex in examples:
        if isinstance(ex, dict):
            result.append(ex)
        else:
            result.append(
                {
                    "id": getattr(ex, "id", None),
                    "input": getattr(ex, "input", {}),
                    "output": getattr(ex, "output", {}),
                    "metadata": getattr(ex, "metadata", {}),
                }
            )
    return result


def _ensure_json_safe(value: Any) -> Any:
    """Ensure value is JSON serializable."""
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {k: _ensure_json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_ensure_json_safe(v) for v in value]
    return str(value)


__all__ = ["PhoenixStorageBackend"]
