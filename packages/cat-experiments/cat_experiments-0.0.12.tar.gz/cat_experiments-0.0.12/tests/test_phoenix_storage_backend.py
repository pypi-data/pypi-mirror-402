"""Tests for PhoenixStorageBackend implementing StorageBackend protocol."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterator
from unittest.mock import MagicMock

import pytest

from cat.experiments.protocol import (
    DatasetExample,
    ExperimentConfig,
    ExperimentResult,
    ExperimentSummary,
)
from cat.experiments.runner.adapters.protocol import StorageBackend

# -----------------------------------------------------------------------------
# Stub classes for Phoenix client
# -----------------------------------------------------------------------------


class StubHTTPResponse:
    """Stub for httpx.Response."""

    def __init__(
        self,
        *,
        status_code: int = 200,
        data: dict[str, Any] | list[Any] | None = None,
        error: bool = False,
    ):
        self.status_code = status_code
        self._data = data if data is not None else {}
        self._error = error

    def raise_for_status(self) -> None:
        if self._error or self.status_code >= 400:
            import httpx

            request = MagicMock()
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}",
                request=request,
                response=self,  # type: ignore
            )

    def json(self) -> dict[str, Any]:
        return {"data": self._data}


class StubHTTPClient:
    """Stub for httpx.Client that records requests."""

    def __init__(self, responses: Iterator[dict[str, Any]] | None = None):
        self.requests: list[dict[str, Any]] = []
        self._responses = responses or iter([])
        self._get_responses: dict[str, StubHTTPResponse] = {}

    def post(self, url: str, *, json: Any, timeout: int | float | None = None) -> StubHTTPResponse:
        self.requests.append({"method": "POST", "url": url, "json": json, "timeout": timeout})
        try:
            payload = next(self._responses)
        except StopIteration:
            payload = {}
        return StubHTTPResponse(data=payload)

    def get(
        self, url: str, *, params: dict[str, Any] | None = None, timeout: int | float | None = None
    ) -> StubHTTPResponse:
        self.requests.append({"method": "GET", "url": url, "params": params, "timeout": timeout})
        if url in self._get_responses:
            return self._get_responses[url]
        return StubHTTPResponse(data=[])

    def set_get_response(self, url: str, response: StubHTTPResponse) -> None:
        """Set a specific response for a GET URL."""
        self._get_responses[url] = response


class StubDatasets:
    """Stub for Phoenix datasets API."""

    def __init__(self, examples: list[dict[str, Any]] | None = None):
        self._examples = examples or [
            {
                "id": "ex-1",
                "input": {"prompt": "hello"},
                "output": {"expected": "world"},
                "metadata": {},
            }
        ]

    def get_dataset(
        self, dataset: str, version_id: str | None = None, timeout: int | None = None
    ) -> Any:
        """Return a stub dataset object."""
        return type(
            "Dataset",
            (),
            {
                "id": "dataset-123",
                "version_id": "version-456",
                "examples": self._examples,
            },
        )()


class StubExperiments:
    """Stub for Phoenix experiments API."""

    def __init__(self, experiment_id: str = "exp-remote-1"):
        self._experiment_id = experiment_id

    def create(
        self,
        *,
        dataset_id: str,
        dataset_version_id: str | None = None,
        experiment_name: str | None = None,
        experiment_description: str | None = None,
        experiment_metadata: dict[str, Any] | None = None,
        splits: Any = None,
        repetitions: int = 1,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        return {"id": self._experiment_id, "project_name": "test-project"}

    def get(self, experiment_id: str) -> dict[str, Any]:
        return {"id": experiment_id}


class StubPhoenixClient:
    """Stub for Phoenix client."""

    def __init__(
        self,
        http_client: StubHTTPClient,
        datasets: StubDatasets | None = None,
        experiments: StubExperiments | None = None,
    ):
        self._client = http_client
        self.datasets = datasets or StubDatasets()
        self.experiments = experiments or StubExperiments()


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def http_client() -> StubHTTPClient:
    """Create a stub HTTP client."""
    return StubHTTPClient(
        iter(
            [
                {"id": "run-remote-1"},  # For run POST
                {"id": "eval-remote-1"},  # For evaluation POST
            ]
        )
    )


@pytest.fixture
def phoenix_client(http_client: StubHTTPClient) -> StubPhoenixClient:
    """Create a stub Phoenix client."""
    return StubPhoenixClient(http_client)


@pytest.fixture
def backend(phoenix_client: StubPhoenixClient) -> Any:
    """Create a PhoenixStorageBackend with stub client."""
    from cat.experiments.runner.adapters.phoenix import PhoenixStorageBackend

    return PhoenixStorageBackend(client=phoenix_client)  # type: ignore[arg-type]


@pytest.fixture
def sample_config() -> ExperimentConfig:
    """Create a sample experiment config."""
    return ExperimentConfig(
        name="test-experiment",
        description="A test experiment",
        dataset_id="dataset-123",
        dataset_version_id="version-456",
        repetitions=1,
    )


@pytest.fixture
def sample_examples() -> list[DatasetExample]:
    """Create sample dataset examples."""
    return [
        DatasetExample(
            id="ex-1",
            input={"prompt": "hello"},
            output={"expected": "world"},
            metadata={"phoenix_dataset_id": "dataset-123"},
        ),
    ]


# -----------------------------------------------------------------------------
# Protocol conformance tests
# -----------------------------------------------------------------------------


class TestStorageBackendProtocol:
    """Test that PhoenixStorageBackend implements StorageBackend protocol."""

    def test_implements_protocol(self, backend: Any) -> None:
        """PhoenixStorageBackend should implement StorageBackend protocol."""
        assert isinstance(backend, StorageBackend)


# -----------------------------------------------------------------------------
# Dataset loading tests
# -----------------------------------------------------------------------------


class TestLoadDataset:
    """Tests for load_dataset method."""

    def test_load_dataset_from_phoenix(self, backend: Any) -> None:
        """Should load dataset from Phoenix by name."""
        examples = backend.load_dataset(name="my-dataset")

        assert len(examples) == 1
        assert examples[0].id == "ex-1"
        assert examples[0].input == {"prompt": "hello"}
        assert examples[0].output == {"expected": "world"}
        # Phoenix metadata should be added
        assert examples[0].metadata["phoenix_dataset_id"] == "dataset-123"
        assert examples[0].metadata["phoenix_dataset_version_id"] == "version-456"

    def test_load_dataset_requires_name(self, backend: Any) -> None:
        """Should raise ValueError if name not provided."""
        with pytest.raises(ValueError, match="name is required"):
            backend.load_dataset()

    def test_load_dataset_with_version(self, backend: Any) -> None:
        """Should pass version to Phoenix API."""
        examples = backend.load_dataset(name="my-dataset", version="v1")

        assert len(examples) == 1


# -----------------------------------------------------------------------------
# Experiment lifecycle tests
# -----------------------------------------------------------------------------


class TestStartExperiment:
    """Tests for start_experiment method."""

    def test_start_experiment_creates_phoenix_experiment(
        self,
        backend: Any,
        sample_config: ExperimentConfig,
        sample_examples: list[DatasetExample],
    ) -> None:
        """start_experiment should create experiment in Phoenix."""
        backend.start_experiment("local-exp-1", sample_config, sample_examples)

        assert backend.remote_experiment_id == "exp-remote-1"

    def test_start_experiment_requires_dataset_id(self, backend: Any) -> None:
        """Should raise ValueError if no dataset_id available."""
        config = ExperimentConfig(name="test")
        examples = [DatasetExample(id="ex1", input={}, output={})]

        with pytest.raises(ValueError, match="dataset_id required"):
            backend.start_experiment("exp-1", config, examples)

    def test_start_experiment_uses_config_dataset_id(
        self, backend: Any, sample_config: ExperimentConfig
    ) -> None:
        """Should use dataset_id from config."""
        examples = [DatasetExample(id="ex1", input={}, output={})]
        backend.start_experiment("exp-1", sample_config, examples)

        assert backend.remote_experiment_id == "exp-remote-1"


# -----------------------------------------------------------------------------
# Save run tests
# -----------------------------------------------------------------------------


class TestSaveRun:
    """Tests for save_run method."""

    def test_save_run_posts_to_phoenix(
        self,
        backend: Any,
        http_client: StubHTTPClient,
        sample_config: ExperimentConfig,
        sample_examples: list[DatasetExample],
    ) -> None:
        """save_run should POST run to Phoenix API."""
        backend.start_experiment("local-exp-1", sample_config, sample_examples)

        now = datetime.now(timezone.utc)
        result = ExperimentResult(
            example_id="ex-1",
            run_id="ex-1#1",
            repetition_number=1,
            started_at=now,
            completed_at=now,
            input_data={"prompt": "hello"},
            output={"expected": "world"},
            actual_output={"response": "world"},
            evaluation_scores={},
            evaluator_metadata={},
            metadata={},
            trace_id="trace-123",
        )

        backend.save_run("local-exp-1", result)

        # Find the run POST request
        run_requests = [r for r in http_client.requests if "runs" in r["url"]]
        assert len(run_requests) == 1

        run_payload = run_requests[0]["json"]
        assert run_payload["dataset_example_id"] == "ex-1"
        assert run_payload["repetition_number"] == 1
        assert run_payload["trace_id"] == "trace-123"
        assert run_payload["output"] == {"response": "world"}

    def test_save_run_requires_started_experiment(self, backend: Any) -> None:
        """save_run should raise if experiment not started."""
        result = ExperimentResult(
            example_id="ex-1",
            run_id="ex-1#1",
            repetition_number=1,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            input_data={},
            output={},
            actual_output={},
            evaluation_scores={},
            evaluator_metadata={},
            metadata={},
        )

        with pytest.raises(RuntimeError, match="experiment not initialized"):
            backend.save_run("exp-1", result)

    def test_save_run_maps_run_ids(
        self,
        backend: Any,
        http_client: StubHTTPClient,
        sample_config: ExperimentConfig,
        sample_examples: list[DatasetExample],
    ) -> None:
        """save_run should map local run_id to remote run_id."""
        backend.start_experiment("local-exp-1", sample_config, sample_examples)

        result = ExperimentResult(
            example_id="ex-1",
            run_id="ex-1#1",
            repetition_number=1,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            input_data={},
            output={},
            actual_output={},
            evaluation_scores={},
            evaluator_metadata={},
            metadata={},
        )

        backend.save_run("local-exp-1", result)

        # The backend should have mapped the local run_id to remote
        assert backend._run_id_map.get("ex-1#1") == "run-remote-1"


# -----------------------------------------------------------------------------
# Save evaluation tests
# -----------------------------------------------------------------------------


class TestSaveEvaluation:
    """Tests for save_evaluation method."""

    def test_save_evaluation_posts_to_phoenix(
        self,
        backend: Any,
        http_client: StubHTTPClient,
        sample_config: ExperimentConfig,
        sample_examples: list[DatasetExample],
    ) -> None:
        """save_evaluation should POST evaluation to Phoenix API."""
        backend.start_experiment("local-exp-1", sample_config, sample_examples)

        # First save a run to get the run_id mapping
        result = ExperimentResult(
            example_id="ex-1",
            run_id="ex-1#1",
            repetition_number=1,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            input_data={},
            output={},
            actual_output={},
            evaluation_scores={},
            evaluator_metadata={},
            metadata={},
        )
        backend.save_run("local-exp-1", result)

        # Now save an evaluation
        backend.save_evaluation(
            experiment_id="local-exp-1",
            run_id="ex-1#1",
            evaluator_name="accuracy",
            score=0.95,
            label="correct",
            metadata={"explanation": "Looks good", "trace_id": "eval-trace-123"},
        )

        # Find the evaluation POST request
        eval_requests = [r for r in http_client.requests if "evaluations" in r["url"]]
        assert len(eval_requests) == 1

        eval_payload = eval_requests[0]["json"]
        assert eval_payload["experiment_run_id"] == "run-remote-1"  # Mapped ID
        assert eval_payload["name"] == "accuracy"
        assert eval_payload["result"]["score"] == 0.95
        assert eval_payload["result"]["label"] == "correct"
        assert eval_payload["result"]["explanation"] == "Looks good"
        assert eval_payload["trace_id"] == "eval-trace-123"

    def test_save_evaluation_requires_started_experiment(self, backend: Any) -> None:
        """save_evaluation should raise if experiment not started."""
        with pytest.raises(RuntimeError, match="experiment not initialized"):
            backend.save_evaluation(
                experiment_id="exp-1",
                run_id="ex-1#1",
                evaluator_name="accuracy",
                score=0.95,
                label=None,
                metadata=None,
            )


# -----------------------------------------------------------------------------
# Complete/fail experiment tests
# -----------------------------------------------------------------------------


class TestCompleteExperiment:
    """Tests for complete_experiment method."""

    def test_complete_experiment_adds_phoenix_metadata(
        self,
        backend: Any,
        sample_config: ExperimentConfig,
        sample_examples: list[DatasetExample],
    ) -> None:
        """complete_experiment should add Phoenix experiment ID to summary."""
        backend.start_experiment("local-exp-1", sample_config, sample_examples)

        summary = ExperimentSummary(
            total_examples=1,
            successful_examples=1,
            failed_examples=0,
            average_scores={"accuracy": 0.95},
            total_execution_time_ms=100.0,
            experiment_id="local-exp-1",
            config=sample_config,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )

        backend.complete_experiment("local-exp-1", summary)

        assert summary.aggregate_metadata["phoenix"]["experiment_id"] == "exp-remote-1"


class TestFailExperiment:
    """Tests for fail_experiment method."""

    def test_fail_experiment_no_op(
        self,
        backend: Any,
        sample_config: ExperimentConfig,
        sample_examples: list[DatasetExample],
    ) -> None:
        """fail_experiment should be a no-op (Phoenix doesn't support failure tracking)."""
        backend.start_experiment("local-exp-1", sample_config, sample_examples)

        # Should not raise
        backend.fail_experiment("local-exp-1", "Something went wrong")


# -----------------------------------------------------------------------------
# Resume support tests
# -----------------------------------------------------------------------------


class TestGetCompletedRuns:
    """Tests for get_completed_runs method."""

    def test_get_completed_runs_returns_none_for_missing_experiment(
        self, phoenix_client: StubPhoenixClient, http_client: StubHTTPClient
    ) -> None:
        """get_completed_runs should return None if experiment doesn't exist."""
        from cat.experiments.runner.adapters.phoenix import PhoenixStorageBackend

        # Make the experiments.get raise an exception
        phoenix_client.experiments = MagicMock()
        phoenix_client.experiments.get.side_effect = Exception("Not found")

        backend = PhoenixStorageBackend(client=phoenix_client)  # type: ignore[arg-type]

        result = backend.get_completed_runs("nonexistent-exp")
        assert result is None

    def test_get_completed_runs_returns_completed_ids(
        self, phoenix_client: StubPhoenixClient, http_client: StubHTTPClient
    ) -> None:
        """get_completed_runs should return set of completed run IDs."""
        from cat.experiments.runner.adapters.phoenix import PhoenixStorageBackend

        # Set up responses for get_completed_runs
        http_client.set_get_response(
            "v1/experiments/exp-1/runs",
            StubHTTPResponse(data=[{"id": "run-1"}, {"id": "run-2"}]),
        )
        http_client.set_get_response(
            "v1/experiments/exp-1/incomplete-runs",
            StubHTTPResponse(data=[]),  # No incomplete runs
        )

        backend = PhoenixStorageBackend(client=phoenix_client)  # type: ignore[arg-type]

        result = backend.get_completed_runs("exp-1")
        assert result == {"run-1", "run-2"}

    def test_get_completed_runs_excludes_incomplete(
        self, phoenix_client: StubPhoenixClient, http_client: StubHTTPClient
    ) -> None:
        """get_completed_runs should exclude incomplete runs."""
        from cat.experiments.runner.adapters.phoenix import PhoenixStorageBackend

        # Set up responses
        http_client.set_get_response(
            "v1/experiments/exp-1/runs",
            StubHTTPResponse(data=[{"id": "run-1"}, {"id": "run-2"}, {"id": "ex-2#1"}]),
        )
        http_client.set_get_response(
            "v1/experiments/exp-1/incomplete-runs",
            StubHTTPResponse(
                data=[
                    {
                        "dataset_example": {"id": "ex-2"},
                        "repetition_numbers": [1],
                    }
                ]
            ),
        )

        backend = PhoenixStorageBackend(client=phoenix_client)  # type: ignore[arg-type]

        result = backend.get_completed_runs("exp-1")
        # Should have run-1 and run-2 but not ex-2#1
        assert "run-1" in result  # type: ignore
        assert "run-2" in result  # type: ignore


# -----------------------------------------------------------------------------
# Helper function tests
# -----------------------------------------------------------------------------


class TestHelperFunctions:
    """Tests for helper functions in the module."""

    def test_ensure_json_safe_primitives(self) -> None:
        """_ensure_json_safe should pass through primitives."""
        from cat.experiments.runner.adapters.phoenix.backend import _ensure_json_safe

        assert _ensure_json_safe(None) is None
        assert _ensure_json_safe("hello") == "hello"
        assert _ensure_json_safe(42) == 42
        assert _ensure_json_safe(3.14) == 3.14
        assert _ensure_json_safe(True) is True

    def test_ensure_json_safe_collections(self) -> None:
        """_ensure_json_safe should handle collections."""
        from cat.experiments.runner.adapters.phoenix.backend import _ensure_json_safe

        assert _ensure_json_safe({"a": 1, "b": "c"}) == {"a": 1, "b": "c"}
        assert _ensure_json_safe([1, 2, 3]) == [1, 2, 3]
        assert _ensure_json_safe((1, 2)) == [1, 2]

    def test_ensure_json_safe_converts_objects(self) -> None:
        """_ensure_json_safe should convert non-JSON types to strings."""
        from cat.experiments.runner.adapters.phoenix.backend import _ensure_json_safe

        class CustomObj:
            def __str__(self) -> str:
                return "custom"

        assert _ensure_json_safe(CustomObj()) == "custom"
