"""Tests for CatCafeStorageBackend implementing StorageBackend protocol."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest

from cat.experiments.protocol import (
    DatasetExample,
    ExperimentConfig,
    ExperimentResult,
    ExperimentSummary,
)
from cat.experiments.runner.adapters.protocol import StorageBackend

# -----------------------------------------------------------------------------
# Stub classes for Cat Cafe client
# -----------------------------------------------------------------------------


class StubCatCafeClient:
    """Stub for CATCafeClient that records requests."""

    def __init__(
        self,
        experiment_id: str = "exp-remote-1",
        examples: list[dict[str, Any]] | None = None,
    ):
        self._experiment_id = experiment_id
        self._examples = examples or [
            {
                "id": "ex-1",
                "input": {"prompt": "hello"},
                "output": {"expected": "world"},
                "metadata": {},
            }
        ]

        # Record calls
        self.start_experiment_calls: list[Any] = []
        self.create_run_calls: list[tuple[str, dict[str, Any]]] = []
        self.append_evaluation_calls: list[tuple[str, str, dict[str, Any]]] = []
        self.complete_experiment_calls: list[tuple[str, dict[str, Any]]] = []
        self.get_dataset_examples_calls: list[tuple[str, dict[str, Any]]] = []
        self.get_experiment_detail_calls: list[str] = []

        # Response configuration
        self._run_id_counter = 0
        self._experiment_detail: dict[str, Any] | None = None

    def start_experiment(self, experiment_config: Any) -> str:
        self.start_experiment_calls.append(experiment_config)
        return self._experiment_id

    def create_run(self, experiment_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.create_run_calls.append((experiment_id, payload))
        self._run_id_counter += 1
        return {"id": f"run-remote-{self._run_id_counter}"}

    def append_evaluation(
        self, experiment_id: str, run_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        self.append_evaluation_calls.append((experiment_id, run_id, payload))
        return {"id": f"eval-{len(self.append_evaluation_calls)}"}

    def complete_experiment(self, experiment_id: str, summary: dict[str, Any]) -> None:
        self.complete_experiment_calls.append((experiment_id, summary))

    def get_dataset_examples(self, dataset_id: str, **kwargs: Any) -> list[dict[str, Any]]:
        self.get_dataset_examples_calls.append((dataset_id, kwargs))
        return self._examples

    def get_experiment_detail(self, experiment_id: str) -> dict[str, Any]:
        self.get_experiment_detail_calls.append(experiment_id)
        if self._experiment_detail:
            return self._experiment_detail
        return {
            "experiment": {"dataset_id": "dataset-123"},
            "results": [],
        }


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def cat_cafe_client() -> StubCatCafeClient:
    """Create a stub Cat Cafe client."""
    return StubCatCafeClient()


@pytest.fixture
def backend(cat_cafe_client: StubCatCafeClient) -> Any:
    """Create a CatCafeStorageBackend with stub client."""
    from cat.experiments.runner.adapters.cat_cafe import CatCafeStorageBackend

    return CatCafeStorageBackend(client=cat_cafe_client)


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
            metadata={"cat_cafe_dataset_id": "dataset-123"},
        ),
    ]


# -----------------------------------------------------------------------------
# Protocol conformance tests
# -----------------------------------------------------------------------------


class TestStorageBackendProtocol:
    """Test that CatCafeStorageBackend implements StorageBackend protocol."""

    def test_implements_protocol(self, backend: Any) -> None:
        """CatCafeStorageBackend should implement StorageBackend protocol."""
        assert isinstance(backend, StorageBackend)


# -----------------------------------------------------------------------------
# Dataset loading tests
# -----------------------------------------------------------------------------


class TestLoadDataset:
    """Tests for load_dataset method."""

    def test_load_dataset_from_cat_cafe(
        self, backend: Any, cat_cafe_client: StubCatCafeClient
    ) -> None:
        """Should load dataset from Cat Cafe by name."""
        examples = backend.load_dataset(name="my-dataset")

        assert len(examples) == 1
        assert examples[0].id == "ex-1"
        assert examples[0].input == {"prompt": "hello"}
        assert examples[0].output == {"expected": "world"}
        # Cat Cafe metadata should be added
        assert examples[0].metadata["cat_cafe_dataset_id"] == "my-dataset"

        # Verify client was called
        assert len(cat_cafe_client.get_dataset_examples_calls) == 1
        assert cat_cafe_client.get_dataset_examples_calls[0][0] == "my-dataset"

    def test_load_dataset_requires_name(self, backend: Any) -> None:
        """Should raise ValueError if name not provided."""
        with pytest.raises(ValueError, match="name is required"):
            backend.load_dataset()

    def test_load_dataset_with_version(
        self, backend: Any, cat_cafe_client: StubCatCafeClient
    ) -> None:
        """Should pass version to Cat Cafe API."""
        examples = backend.load_dataset(name="my-dataset", version="v1")

        assert len(examples) == 1
        # Verify version was passed
        assert cat_cafe_client.get_dataset_examples_calls[0][1].get("version") == "v1"


# -----------------------------------------------------------------------------
# Experiment lifecycle tests
# -----------------------------------------------------------------------------


class TestStartExperiment:
    """Tests for start_experiment method."""

    def test_start_experiment_creates_cat_cafe_experiment(
        self,
        backend: Any,
        cat_cafe_client: StubCatCafeClient,
        sample_config: ExperimentConfig,
        sample_examples: list[DatasetExample],
    ) -> None:
        """start_experiment should create experiment in Cat Cafe."""
        backend.start_experiment("local-exp-1", sample_config, sample_examples)

        assert backend.remote_experiment_id == "exp-remote-1"
        assert len(cat_cafe_client.start_experiment_calls) == 1

    def test_start_experiment_requires_dataset_id(self, backend: Any) -> None:
        """Should raise ValueError if no dataset_id available."""
        config = ExperimentConfig(name="test")
        examples = [DatasetExample(id="ex1", input={}, output={})]

        with pytest.raises(ValueError, match="dataset_id required"):
            backend.start_experiment("exp-1", config, examples)

    def test_start_experiment_uses_config_dataset_id(
        self, backend: Any, cat_cafe_client: StubCatCafeClient, sample_config: ExperimentConfig
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

    def test_save_run_posts_to_cat_cafe(
        self,
        backend: Any,
        cat_cafe_client: StubCatCafeClient,
        sample_config: ExperimentConfig,
        sample_examples: list[DatasetExample],
    ) -> None:
        """save_run should POST run to Cat Cafe API."""
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

        # Verify create_run was called
        assert len(cat_cafe_client.create_run_calls) == 1
        exp_id, payload = cat_cafe_client.create_run_calls[0]

        assert exp_id == "exp-remote-1"
        assert payload["run_id"] == "ex-1#1"
        assert payload["repetition_number"] == 1
        assert payload["trace_id"] == "trace-123"
        assert payload["actual_output"] == {"response": "world"}

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
        cat_cafe_client: StubCatCafeClient,
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

    def test_save_evaluation_posts_to_cat_cafe(
        self,
        backend: Any,
        cat_cafe_client: StubCatCafeClient,
        sample_config: ExperimentConfig,
        sample_examples: list[DatasetExample],
    ) -> None:
        """save_evaluation should POST evaluation to Cat Cafe API."""
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

        # Verify append_evaluation was called
        assert len(cat_cafe_client.append_evaluation_calls) == 1
        exp_id, run_id, payload = cat_cafe_client.append_evaluation_calls[0]

        assert exp_id == "exp-remote-1"
        assert run_id == "run-remote-1"  # Mapped ID
        assert payload["evaluator_name"] == "accuracy"
        assert payload["score"] == 0.95
        assert payload["label"] == "correct"
        assert payload["explanation"] == "Looks good"
        assert payload["trace_id"] == "eval-trace-123"

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

    def test_complete_experiment_calls_cat_cafe(
        self,
        backend: Any,
        cat_cafe_client: StubCatCafeClient,
        sample_config: ExperimentConfig,
        sample_examples: list[DatasetExample],
    ) -> None:
        """complete_experiment should call Cat Cafe complete_experiment API."""
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

        # Verify complete_experiment was called
        assert len(cat_cafe_client.complete_experiment_calls) == 1
        exp_id, payload = cat_cafe_client.complete_experiment_calls[0]
        assert exp_id == "exp-remote-1"
        assert payload["total_examples"] == 1
        assert payload["average_scores"] == {"accuracy": 0.95}

        # Verify Cat Cafe metadata was added to summary
        assert summary.aggregate_metadata["cat_cafe"]["experiment_id"] == "exp-remote-1"


class TestFailExperiment:
    """Tests for fail_experiment method."""

    def test_fail_experiment_calls_complete_with_error(
        self,
        backend: Any,
        cat_cafe_client: StubCatCafeClient,
        sample_config: ExperimentConfig,
        sample_examples: list[DatasetExample],
    ) -> None:
        """fail_experiment should call complete_experiment with error status."""
        backend.start_experiment("local-exp-1", sample_config, sample_examples)

        backend.fail_experiment("local-exp-1", "Something went wrong")

        # Verify complete_experiment was called with error
        assert len(cat_cafe_client.complete_experiment_calls) == 1
        exp_id, payload = cat_cafe_client.complete_experiment_calls[0]
        assert exp_id == "exp-remote-1"
        assert payload["status"] == "failed"
        assert payload["error"] == "Something went wrong"


# -----------------------------------------------------------------------------
# Resume support tests
# -----------------------------------------------------------------------------


class TestGetCompletedRuns:
    """Tests for get_completed_runs method."""

    def test_get_completed_runs_returns_none_for_missing_experiment(self) -> None:
        """get_completed_runs should return None if experiment doesn't exist."""
        from cat.experiments.runner.adapters.cat_cafe import CatCafeStorageBackend

        # Create a client without get_experiment_detail method
        class ClientWithoutDetail:
            def get_dataset_examples(self, dataset_id: str, **kwargs: Any) -> list[dict[str, Any]]:
                return []

        backend = CatCafeStorageBackend(client=ClientWithoutDetail())  # type: ignore

        result = backend.get_completed_runs("nonexistent-exp")
        assert result is None

    def test_get_completed_runs_returns_completed_ids(
        self, cat_cafe_client: StubCatCafeClient
    ) -> None:
        """get_completed_runs should return set of completed run IDs."""
        from cat.experiments.runner.adapters.cat_cafe import CatCafeStorageBackend

        cat_cafe_client._experiment_detail = {
            "experiment": {"dataset_id": "dataset-123"},
            "results": [
                {"run_id": "run-1", "error": None},
                {"run_id": "run-2", "error": None},
            ],
        }

        backend = CatCafeStorageBackend(client=cat_cafe_client)

        result = backend.get_completed_runs("exp-1")
        assert result == {"run-1", "run-2"}

    def test_get_completed_runs_excludes_failed(self, cat_cafe_client: StubCatCafeClient) -> None:
        """get_completed_runs should exclude runs with errors."""
        from cat.experiments.runner.adapters.cat_cafe import CatCafeStorageBackend

        cat_cafe_client._experiment_detail = {
            "experiment": {"dataset_id": "dataset-123"},
            "results": [
                {"run_id": "run-1", "error": None},
                {"run_id": "run-2", "error": "Task failed"},
            ],
        }

        backend = CatCafeStorageBackend(client=cat_cafe_client)

        result = backend.get_completed_runs("exp-1")
        assert result == {"run-1"}


# -----------------------------------------------------------------------------
# Helper function tests
# -----------------------------------------------------------------------------


class TestHelperFunctions:
    """Tests for helper functions in the module."""

    def test_normalize_output_dict(self) -> None:
        """_normalize_output should pass through dicts."""
        from cat.experiments.runner.adapters.cat_cafe.backend import _normalize_output

        assert _normalize_output({"a": 1}) == {"a": 1}

    def test_normalize_output_string(self) -> None:
        """_normalize_output should pass through strings."""
        from cat.experiments.runner.adapters.cat_cafe.backend import _normalize_output

        assert _normalize_output("hello") == "hello"

    def test_normalize_output_none(self) -> None:
        """_normalize_output should convert None to empty string."""
        from cat.experiments.runner.adapters.cat_cafe.backend import _normalize_output

        assert _normalize_output(None) == ""

    def test_normalize_output_other(self) -> None:
        """_normalize_output should convert other types to repr."""
        from cat.experiments.runner.adapters.cat_cafe.backend import _normalize_output

        assert _normalize_output(123) == "123"
        assert _normalize_output([1, 2]) == "[1, 2]"

    def test_example_signature(self) -> None:
        """_example_signature should create consistent signatures."""
        from cat.experiments.runner.adapters.cat_cafe.backend import _example_signature

        sig1 = _example_signature({"input": {"a": 1}, "output": {"b": 2}})
        sig2 = _example_signature({"input": {"a": 1}, "output": {"b": 2}})
        sig3 = _example_signature({"input": {"a": 2}, "output": {"b": 2}})

        assert sig1 == sig2
        assert sig1 != sig3
