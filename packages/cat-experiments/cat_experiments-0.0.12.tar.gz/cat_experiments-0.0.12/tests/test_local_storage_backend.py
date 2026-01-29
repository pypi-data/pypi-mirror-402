"""Tests for LocalStorageBackend implementing StorageBackend protocol."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from cat.experiments.protocol import (
    DatasetExample,
    ExperimentConfig,
    ExperimentResult,
    ExperimentSummary,
)
from cat.experiments.runner.adapters import LocalStorageBackend, StorageBackend


@pytest.fixture
def backend(tmp_path: Path) -> LocalStorageBackend:
    """Create a LocalStorageBackend with a temp directory."""
    return LocalStorageBackend(base_dir=tmp_path)


@pytest.fixture
def sample_examples() -> list[DatasetExample]:
    """Create sample dataset examples."""
    return [
        DatasetExample(
            id="ex1",
            input={"query": "What is 2+2?"},
            output={"answer": "4"},
        ),
        DatasetExample(
            id="ex2",
            input={"query": "What is 3+3?"},
            output={"answer": "6"},
        ),
    ]


@pytest.fixture
def sample_config() -> ExperimentConfig:
    """Create a sample experiment config."""
    return ExperimentConfig(
        name="test-experiment",
        description="A test experiment",
        repetitions=1,
        max_workers=1,
    )


class TestStorageBackendProtocol:
    """Test that LocalStorageBackend implements StorageBackend protocol."""

    def test_implements_protocol(self, backend: LocalStorageBackend) -> None:
        """LocalStorageBackend should implement StorageBackend protocol."""
        assert isinstance(backend, StorageBackend)


class TestLoadDataset:
    """Tests for load_dataset method."""

    def test_load_jsonl_dataset(self, backend: LocalStorageBackend, tmp_path: Path) -> None:
        """Should load dataset from JSONL file."""
        dataset_path = tmp_path / "data.jsonl"
        dataset_path.write_text(
            '{"id": "1", "input": {"q": "a"}, "output": {"a": "b"}}\n'
            '{"id": "2", "input": {"q": "c"}, "output": {"a": "d"}}\n'
        )

        examples = backend.load_dataset(path=str(dataset_path))

        assert len(examples) == 2
        assert examples[0].id == "1"
        assert examples[0].input == {"q": "a"}
        assert examples[1].id == "2"

    def test_load_json_dataset(self, backend: LocalStorageBackend, tmp_path: Path) -> None:
        """Should load dataset from JSON array file."""
        dataset_path = tmp_path / "data.json"
        dataset_path.write_text(
            '[{"id": "1", "input": {"q": "a"}, "output": {"a": "b"}},'
            '{"id": "2", "input": {"q": "c"}, "output": {"a": "d"}}]'
        )

        examples = backend.load_dataset(path=str(dataset_path))

        assert len(examples) == 2
        assert examples[0].id == "1"
        assert examples[1].id == "2"

    def test_load_dataset_requires_path(self, backend: LocalStorageBackend) -> None:
        """Should raise ValueError if path not provided."""
        with pytest.raises(ValueError, match="path is required"):
            backend.load_dataset()

    def test_load_dataset_file_not_found(self, backend: LocalStorageBackend) -> None:
        """Should raise FileNotFoundError if file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            backend.load_dataset(path="/nonexistent/file.jsonl")


class TestExperimentLifecycle:
    """Tests for experiment lifecycle methods."""

    def test_start_experiment_creates_directory(
        self,
        backend: LocalStorageBackend,
        tmp_path: Path,
        sample_config: ExperimentConfig,
        sample_examples: list[DatasetExample],
    ) -> None:
        """start_experiment should create experiment directory with config and examples."""
        backend.start_experiment("exp-001", sample_config, sample_examples)

        exp_dir = tmp_path / "exp-001"
        assert exp_dir.exists()
        assert (exp_dir / "config.json").exists()
        assert (exp_dir / "examples.jsonl").exists()
        assert (exp_dir / "runs.jsonl").exists()
        assert (exp_dir / "evaluations.jsonl").exists()

        # Verify config
        config_data = json.loads((exp_dir / "config.json").read_text())
        assert config_data["name"] == "test-experiment"

        # Verify examples
        examples_lines = (exp_dir / "examples.jsonl").read_text().strip().split("\n")
        assert len(examples_lines) == 2

    def test_save_run_appends_to_file(
        self,
        backend: LocalStorageBackend,
        tmp_path: Path,
        sample_config: ExperimentConfig,
        sample_examples: list[DatasetExample],
    ) -> None:
        """save_run should append run result to runs.jsonl."""
        backend.start_experiment("exp-001", sample_config, sample_examples)

        result = ExperimentResult(
            example_id="ex1",
            run_id="ex1#1",
            repetition_number=1,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            input_data={"query": "What is 2+2?"},
            output={"answer": "4"},
            actual_output="4",
            evaluation_scores={},
            evaluator_metadata={},
            metadata={},
        )

        backend.save_run("exp-001", result)

        runs_path = tmp_path / "exp-001" / "runs.jsonl"
        runs_lines = runs_path.read_text().strip().split("\n")
        assert len(runs_lines) == 1
        run_data = json.loads(runs_lines[0])
        assert run_data["run_id"] == "ex1#1"
        assert run_data["actual_output"] == "4"

    def test_save_evaluation_appends_to_file(
        self,
        backend: LocalStorageBackend,
        tmp_path: Path,
        sample_config: ExperimentConfig,
        sample_examples: list[DatasetExample],
    ) -> None:
        """save_evaluation should append evaluation to evaluations.jsonl."""
        backend.start_experiment("exp-001", sample_config, sample_examples)

        backend.save_evaluation(
            experiment_id="exp-001",
            run_id="ex1#1",
            evaluator_name="accuracy",
            score=0.95,
            label="correct",
            metadata={"confidence": 0.9},
        )

        evals_path = tmp_path / "exp-001" / "evaluations.jsonl"
        evals_lines = evals_path.read_text().strip().split("\n")
        assert len(evals_lines) == 1
        eval_data = json.loads(evals_lines[0])
        assert eval_data["run_id"] == "ex1#1"
        assert eval_data["evaluator_name"] == "accuracy"
        assert eval_data["score"] == 0.95
        assert eval_data["label"] == "correct"
        assert eval_data["metadata"] == {"confidence": 0.9}

    def test_complete_experiment_writes_summary(
        self,
        backend: LocalStorageBackend,
        tmp_path: Path,
        sample_config: ExperimentConfig,
        sample_examples: list[DatasetExample],
    ) -> None:
        """complete_experiment should write summary.json."""
        backend.start_experiment("exp-001", sample_config, sample_examples)

        summary = ExperimentSummary(
            total_examples=2,
            successful_examples=2,
            failed_examples=0,
            average_scores={"accuracy": 0.95},
            total_execution_time_ms=1000.0,
            experiment_id="exp-001",
            config=sample_config,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )

        backend.complete_experiment("exp-001", summary)

        summary_path = tmp_path / "exp-001" / "summary.json"
        assert summary_path.exists()
        summary_data = json.loads(summary_path.read_text())
        assert summary_data["total_examples"] == 2
        assert summary_data["average_scores"] == {"accuracy": 0.95}

    def test_fail_experiment_writes_error(
        self,
        backend: LocalStorageBackend,
        tmp_path: Path,
        sample_config: ExperimentConfig,
        sample_examples: list[DatasetExample],
    ) -> None:
        """fail_experiment should write error.txt."""
        backend.start_experiment("exp-001", sample_config, sample_examples)

        backend.fail_experiment("exp-001", "Something went wrong")

        error_path = tmp_path / "exp-001" / "error.txt"
        assert error_path.exists()
        assert error_path.read_text() == "Something went wrong"


class TestResumeSupport:
    """Tests for resume functionality."""

    def test_get_completed_runs_returns_none_for_missing_experiment(
        self, backend: LocalStorageBackend
    ) -> None:
        """get_completed_runs should return None if experiment doesn't exist."""
        result = backend.get_completed_runs("nonexistent")
        assert result is None

    def test_get_completed_runs_returns_empty_set_for_new_experiment(
        self,
        backend: LocalStorageBackend,
        sample_config: ExperimentConfig,
        sample_examples: list[DatasetExample],
    ) -> None:
        """get_completed_runs should return empty set for experiment with no runs."""
        backend.start_experiment("exp-001", sample_config, sample_examples)

        result = backend.get_completed_runs("exp-001")

        assert result == set()

    def test_get_completed_runs_returns_successful_run_ids(
        self,
        backend: LocalStorageBackend,
        sample_config: ExperimentConfig,
        sample_examples: list[DatasetExample],
    ) -> None:
        """get_completed_runs should return run_ids of successful runs."""
        backend.start_experiment("exp-001", sample_config, sample_examples)

        # Save two successful runs
        for i, ex in enumerate(sample_examples):
            result = ExperimentResult(
                example_id=ex.id or "",
                run_id=f"{ex.id}#1",
                repetition_number=1,
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                input_data=ex.input,
                output=ex.output,
                actual_output="result",
                evaluation_scores={},
                evaluator_metadata={},
                metadata={},
            )
            backend.save_run("exp-001", result)

        completed = backend.get_completed_runs("exp-001")

        assert completed == {"ex1#1", "ex2#1"}

    def test_get_completed_runs_excludes_failed_runs(
        self,
        backend: LocalStorageBackend,
        sample_config: ExperimentConfig,
        sample_examples: list[DatasetExample],
    ) -> None:
        """get_completed_runs should not include runs with errors."""
        backend.start_experiment("exp-001", sample_config, sample_examples)

        # Save one successful run
        success = ExperimentResult(
            example_id="ex1",
            run_id="ex1#1",
            repetition_number=1,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            input_data={},
            output={},
            actual_output="result",
            evaluation_scores={},
            evaluator_metadata={},
            metadata={},
        )
        backend.save_run("exp-001", success)

        # Save one failed run
        failed = ExperimentResult(
            example_id="ex2",
            run_id="ex2#1",
            repetition_number=1,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            input_data={},
            output={},
            actual_output=None,
            evaluation_scores={},
            evaluator_metadata={},
            metadata={},
            error="Task failed",
        )
        backend.save_run("exp-001", failed)

        completed = backend.get_completed_runs("exp-001")

        assert completed == {"ex1#1"}


class TestLoadExperiment:
    """Tests for load_experiment helper method."""

    def test_load_experiment_returns_none_for_missing(self, backend: LocalStorageBackend) -> None:
        """load_experiment should return None if experiment doesn't exist."""
        result = backend.load_experiment("nonexistent")
        assert result is None

    def test_load_experiment_merges_evaluations(
        self,
        backend: LocalStorageBackend,
        sample_config: ExperimentConfig,
        sample_examples: list[DatasetExample],
    ) -> None:
        """load_experiment should merge evaluations into results."""
        backend.start_experiment("exp-001", sample_config, sample_examples)

        # Save a run
        result = ExperimentResult(
            example_id="ex1",
            run_id="ex1#1",
            repetition_number=1,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            input_data={"query": "test"},
            output={"answer": "result"},
            actual_output="result",
            evaluation_scores={},
            evaluator_metadata={},
            metadata={},
        )
        backend.save_run("exp-001", result)

        # Save evaluations
        backend.save_evaluation("exp-001", "ex1#1", "accuracy", 0.95, "correct", None)
        backend.save_evaluation("exp-001", "ex1#1", "relevance", 0.87, None, {"reason": "good"})

        # Load and verify merge
        loaded = backend.load_experiment("exp-001")
        assert loaded is not None

        config, examples, results = loaded
        assert config.name == "test-experiment"
        assert len(examples) == 2
        assert len(results) == 1

        loaded_result = results[0]
        assert loaded_result.evaluation_scores == {"accuracy": 0.95, "relevance": 0.87}
        assert loaded_result.evaluator_metadata["accuracy"]["label"] == "correct"
        assert loaded_result.evaluator_metadata["relevance"]["reason"] == "good"
