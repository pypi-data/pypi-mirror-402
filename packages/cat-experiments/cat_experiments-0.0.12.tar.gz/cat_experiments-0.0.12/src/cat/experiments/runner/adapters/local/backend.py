"""Local file-based storage backend implementing StorageBackend protocol.

Storage structure:
    {base_dir}/{experiment_id}/
    ├── config.json      # ExperimentConfig
    ├── examples.jsonl   # DatasetExamples
    ├── runs.jsonl       # ExperimentResults (task output, timing)
    ├── evaluations.jsonl # Evaluation results (score, label, metadata per evaluator)
    └── summary.json     # ExperimentSummary (written on completion)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ....protocol import (
    DatasetExample,
    ExperimentConfig,
    ExperimentResult,
    ExperimentSummary,
)
from ....protocol.serde import (
    dataset_example_from_dict,
    dataset_example_to_dict,
    experiment_result_from_dict,
    experiment_result_to_dict,
    experiment_summary_to_dict,
)


class LocalStorageBackend:
    """Local file-based implementation of StorageBackend protocol.

    Stores experiment data in a directory structure under base_dir.
    Each experiment gets its own subdirectory with JSON/JSONL files.

    This implementation supports:
    - Streaming writes (runs and evaluations written as they complete)
    - Resume (via get_completed_runs)
    - Crash recovery (data is flushed to disk immediately)
    """

    def __init__(self, base_dir: str | Path | None = None) -> None:
        """Initialize LocalStorageBackend.

        Args:
            base_dir: Base directory for storage. Defaults to .cat_cache in cwd.
        """
        self._base_dir = Path(base_dir) if base_dir else Path.cwd() / ".cat_cache"

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
        """Load a dataset from a local file.

        Args:
            name: Not used for local backend
            path: Path to JSON or JSONL file
            version: Not used for local backend

        Returns:
            List of dataset examples

        Raises:
            ValueError: If path not provided
            FileNotFoundError: If file doesn't exist
        """
        if not path:
            raise ValueError("path is required for local storage backend")

        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {file_path}")

        examples: list[DatasetExample] = []
        with open(file_path, encoding="utf-8") as f:
            if file_path.suffix == ".jsonl":
                for line in f:
                    line = line.strip()
                    if line:
                        examples.append(dataset_example_from_dict(json.loads(line)))
            else:
                content = json.load(f)
                if not isinstance(content, list):
                    raise ValueError(f"Expected JSON array, got {type(content).__name__}")
                for item in content:
                    examples.append(dataset_example_from_dict(item))

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
        """Initialize storage for an experiment.

        Creates the experiment directory and writes config + examples.
        """
        exp_dir = self._base_dir / experiment_id
        exp_dir.mkdir(parents=True, exist_ok=True)

        # Write config
        config_path = exp_dir / "config.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config.to_dict(), f, indent=2)

        # Write examples
        examples_path = exp_dir / "examples.jsonl"
        with open(examples_path, "w", encoding="utf-8") as f:
            for example in examples:
                json.dump(dataset_example_to_dict(example), f)
                f.write("\n")

        # Initialize empty runs and evaluations files
        (exp_dir / "runs.jsonl").touch()
        (exp_dir / "evaluations.jsonl").touch()

    def save_run(
        self,
        experiment_id: str,
        result: ExperimentResult,
    ) -> None:
        """Append a run result to the runs file."""
        exp_dir = self._base_dir / experiment_id
        runs_path = exp_dir / "runs.jsonl"

        with open(runs_path, "a", encoding="utf-8") as f:
            json.dump(experiment_result_to_dict(result), f)
            f.write("\n")

    def save_evaluation(
        self,
        experiment_id: str,
        run_id: str,
        evaluator_name: str,
        score: float,
        label: str | None,
        metadata: dict[str, object] | None,
    ) -> None:
        """Append an evaluation result to the evaluations file."""
        exp_dir = self._base_dir / experiment_id
        evals_path = exp_dir / "evaluations.jsonl"

        eval_record: dict[str, Any] = {
            "run_id": run_id,
            "evaluator_name": evaluator_name,
            "score": score,
        }
        if label is not None:
            eval_record["label"] = label
        if metadata:
            eval_record["metadata"] = metadata

        with open(evals_path, "a", encoding="utf-8") as f:
            json.dump(eval_record, f)
            f.write("\n")

    def complete_experiment(
        self,
        experiment_id: str,
        summary: ExperimentSummary,
    ) -> None:
        """Write the experiment summary."""
        exp_dir = self._base_dir / experiment_id
        summary_path = exp_dir / "summary.json"

        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(experiment_summary_to_dict(summary), f, indent=2)

    def fail_experiment(
        self,
        experiment_id: str,
        error: str,
    ) -> None:
        """Record experiment failure."""
        exp_dir = self._base_dir / experiment_id
        error_path = exp_dir / "error.txt"

        with open(error_path, "w", encoding="utf-8") as f:
            f.write(error)

    # -------------------------------------------------------------------------
    # Resume support
    # -------------------------------------------------------------------------

    def get_completed_runs(
        self,
        experiment_id: str,
    ) -> set[str] | None:
        """Get set of completed run_ids for resume.

        Returns None if experiment doesn't exist.
        """
        exp_dir = self._base_dir / experiment_id
        if not exp_dir.exists():
            return None

        runs_path = exp_dir / "runs.jsonl"
        if not runs_path.exists():
            return set()

        completed: set[str] = set()
        with open(runs_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    run_id = record.get("run_id")
                    # Only count as completed if no error
                    if run_id and not record.get("error"):
                        completed.add(str(run_id))
                except json.JSONDecodeError:
                    continue

        return completed

    # -------------------------------------------------------------------------
    # Additional helpers for reading back data
    # -------------------------------------------------------------------------

    def load_experiment(
        self,
        experiment_id: str,
    ) -> tuple[ExperimentConfig, list[DatasetExample], list[ExperimentResult]] | None:
        """Load all experiment data for re-evaluation or inspection.

        Returns None if experiment doesn't exist.
        """
        exp_dir = self._base_dir / experiment_id
        if not exp_dir.exists():
            return None

        # Load config
        config_path = exp_dir / "config.json"
        if not config_path.exists():
            return None
        with open(config_path, encoding="utf-8") as f:
            config = ExperimentConfig.from_dict(json.load(f))

        # Load examples
        examples: list[DatasetExample] = []
        examples_path = exp_dir / "examples.jsonl"
        if examples_path.exists():
            with open(examples_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        examples.append(dataset_example_from_dict(json.loads(line)))

        # Load runs
        results: list[ExperimentResult] = []
        runs_path = exp_dir / "runs.jsonl"
        if runs_path.exists():
            with open(runs_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        results.append(experiment_result_from_dict(json.loads(line)))

        # Load evaluations and merge into results
        evals_path = exp_dir / "evaluations.jsonl"
        if evals_path.exists():
            evals_by_run: dict[str, list[dict[str, Any]]] = {}
            with open(evals_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        eval_record = json.loads(line)
                        run_id = eval_record.get("run_id", "")
                        evals_by_run.setdefault(run_id, []).append(eval_record)

            # Merge evaluations into results
            for result in results:
                run_evals = evals_by_run.get(result.run_id, [])
                for eval_record in run_evals:
                    name = eval_record.get("evaluator_name", "")
                    if name:
                        result.evaluation_scores[name] = eval_record.get("score", 0.0)
                        if eval_record.get("metadata") or eval_record.get("label"):
                            meta: dict[str, Any] = dict(eval_record.get("metadata") or {})
                            if eval_record.get("label"):
                                meta["label"] = eval_record["label"]
                            result.evaluator_metadata[name] = meta

        return config, examples, results


__all__ = ["LocalStorageBackend"]
