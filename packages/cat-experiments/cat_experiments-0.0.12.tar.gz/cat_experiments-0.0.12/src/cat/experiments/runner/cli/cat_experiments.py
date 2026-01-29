"""Main CLI entry point for cat-experiments.

Usage:
    cat-experiments run experiment.py --dataset data/test.jsonl
    cat-experiments run experiment.py --dataset-name small --storage phoenix
"""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ...sdk.decorators import clear_registry, get_task, list_evaluators, list_tasks

if TYPE_CHECKING:
    from ..adapters.protocol import StorageBackend


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="cat-experiments",
        description="Run experiments with cat-experiments framework",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # run subcommand
    run_parser = subparsers.add_parser("run", help="Run an experiment")
    _add_run_arguments(run_parser)

    args = parser.parse_args()

    if args.command == "run":
        asyncio.run(run_command(args))
    else:
        parser.print_help()
        sys.exit(1)


def _add_run_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments for the run subcommand."""
    # Experiment file (required)
    parser.add_argument(
        "experiment_file",
        type=Path,
        help="Path to experiment Python file",
    )

    # Dataset options
    dataset_group = parser.add_argument_group("Dataset Options")
    dataset_group.add_argument(
        "--dataset",
        "-d",
        help="Dataset file path (local) or name/ID (remote)",
    )
    dataset_group.add_argument(
        "--dataset-version",
        help="Dataset version (Phoenix)",
    )

    # Backend options
    backend_group = parser.add_argument_group("Backend Options")
    backend_group.add_argument(
        "--backend",
        "-b",
        choices=["local", "phoenix", "cat-cafe"],
        default="local",
        help="Storage backend (default: local)",
    )
    backend_group.add_argument(
        "--backend-url",
        help="URL for remote backend (uses defaults if not provided)",
    )

    # Experiment options
    exp_group = parser.add_argument_group("Experiment Options")
    exp_group.add_argument(
        "--param",
        action="append",
        dest="params",
        metavar="KEY=VALUE",
        help="Override params (can be repeated)",
    )
    exp_group.add_argument(
        "--max-workers",
        type=int,
        default=5,
        help="Parallel workers (default: 5)",
    )
    exp_group.add_argument(
        "--repetitions",
        type=int,
        default=1,
        help="Repetitions per example (default: 1)",
    )
    exp_group.add_argument(
        "--dry-run",
        type=int,
        nargs="?",
        const=1,
        metavar="N",
        help="Run N examples without persisting results (default: 1 if flag given)",
    )
    exp_group.add_argument(
        "--resume",
        metavar="EXPERIMENT_ID",
        help="Resume a previous experiment, skipping completed runs",
    )

    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )


async def run_command(args: argparse.Namespace) -> None:
    """Execute the run subcommand."""
    # Validate args
    if not args.experiment_file.exists():
        print(f"Error: Experiment file not found: {args.experiment_file}", file=sys.stderr)
        sys.exit(1)

    if not args.dataset:
        print("Error: --dataset is required", file=sys.stderr)
        sys.exit(1)

    # Load experiment file
    print(f"Loading experiment: {args.experiment_file}")
    experiment_module = load_experiment_file(args.experiment_file)

    # Discover task and evaluators
    task_names = list_tasks()
    evaluator_names = list_evaluators()

    if len(task_names) == 0:
        print("Error: No @task decorated function found in experiment file", file=sys.stderr)
        sys.exit(1)

    if len(task_names) > 1:
        print(
            f"Error: Multiple @task decorated functions found: {task_names}. "
            "Only one task per experiment file is allowed.",
            file=sys.stderr,
        )
        sys.exit(1)

    task_name = task_names[0]
    task_fn = get_task(task_name)
    assert task_fn is not None  # Validated above that task exists
    print(f"Task: {task_name}")
    print(f"Evaluators: {evaluator_names or ['(none)']}")

    # Read module-level config
    module_params = getattr(experiment_module, "params", {})
    experiment_name = getattr(experiment_module, "name", args.experiment_file.stem)
    experiment_description = getattr(experiment_module, "description", "")

    # Parse CLI param overrides
    cli_params = _parse_params(args.params or [])
    merged_params = {**module_params, **cli_params}

    if merged_params:
        print(f"Params: {merged_params}")

    # Load dataset using StorageBackend
    print("Loading dataset...")
    backend = create_backend(args)
    examples, dataset_id, dataset_version_id = load_dataset(args, backend)
    print(f"Loaded {len(examples)} examples")

    # Handle dry-run mode
    dry_run = args.dry_run
    if dry_run is not None:
        if dry_run > len(examples):
            print(f"Note: --dry-run {dry_run} exceeds dataset size, using all {len(examples)}")
            dry_run = len(examples)
        examples = examples[:dry_run]
        print(f"Dry run: limiting to {len(examples)} example(s)")

    # Build evaluator functions for the executor
    evaluator_fns = build_evaluator_functions(evaluator_names)

    # Build and run experiment
    from ...protocol import ExperimentConfig
    from ..executor import InProcessExecutor
    from ..orchestrator import Orchestrator
    from .progress import TqdmProgressListener

    # Create executor with task and evaluators
    executor = InProcessExecutor(task_fn=task_fn, evaluator_fns=evaluator_fns)

    # Build orchestrator with storage backend (None for dry-run)
    if dry_run is not None:
        orchestrator = Orchestrator(
            backend=None,
            executor=executor,
            progress=TqdmProgressListener(desc=experiment_name),
        )
        print("Dry run: results will not be persisted")
    else:
        orchestrator = Orchestrator(
            backend=backend,
            executor=executor,
            progress=TqdmProgressListener(desc=experiment_name),
        )

    # Build config
    config = ExperimentConfig(
        name=experiment_name,
        description=experiment_description,
        max_workers=args.max_workers,
        repetitions=args.repetitions,
        dataset_id=dataset_id,
        dataset_version_id=dataset_version_id,
        params=merged_params,
        metadata={
            "experiment_file": str(args.experiment_file),
            "task": task_name,
            "evaluators": evaluator_names,
        },
    )

    # The @task decorator already wraps to take TaskInput and return TaskOutput
    # The executor handles sync/async detection and TaskOutput unwrapping

    # Run experiment
    if args.resume:
        print(f"Resuming experiment: {args.resume}")
    else:
        print(f"Running experiment: {experiment_name}")

    summary = await orchestrator.run(
        dataset=examples,
        config=config,
        resume=args.resume,
    )

    # Output results
    if args.output == "json":
        output_json(summary)
    else:
        output_text(summary, args.backend)


def load_experiment_file(path: Path) -> Any:
    """Load experiment file as a Python module."""
    # Clear registries from any previous loads
    clear_registry()

    # Load the module
    spec = importlib.util.spec_from_file_location("experiment", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load experiment file: {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["experiment"] = module
    spec.loader.exec_module(module)

    return module


def create_backend(args: argparse.Namespace) -> StorageBackend:
    """Create a StorageBackend for dataset loading."""
    if args.backend == "local" or args.dataset:
        from ..adapters.local import LocalStorageBackend

        return LocalStorageBackend()
    elif args.backend == "phoenix":
        from ..adapters.phoenix import PhoenixStorageBackend

        return PhoenixStorageBackend(base_url=args.backend_url)
    elif args.backend == "cat-cafe":
        from ..adapters.cat_cafe import CatCafeStorageBackend

        return CatCafeStorageBackend(base_url=args.backend_url)
    else:
        # Fallback to local
        from ..adapters.local import LocalStorageBackend

        return LocalStorageBackend()


def load_dataset(
    args: argparse.Namespace,
    storage_backend: StorageBackend,
) -> tuple[list[Any], str, str | None]:
    """Load dataset using StorageBackend."""
    dataset = args.dataset

    # Determine if it's a local path or remote name/ID
    is_local = (
        args.backend == "local"
        or "/" in dataset
        or "\\" in dataset
        or dataset.endswith(".json")
        or dataset.endswith(".jsonl")
        or Path(dataset).exists()
    )

    if is_local:
        # Local file
        examples = storage_backend.load_dataset(path=dataset)
        dataset_id = Path(dataset).stem
        return examples, dataset_id, None

    # Load from remote backend
    examples = storage_backend.load_dataset(
        name=dataset,
        version=args.dataset_version,
    )

    # Extract actual IDs from loaded examples (backends add metadata)
    dataset_id = dataset
    version_id = args.dataset_version

    if examples:
        # Check for Phoenix metadata
        phoenix_id = examples[0].metadata.get("phoenix_dataset_id")
        if phoenix_id:
            dataset_id = phoenix_id
        phoenix_version = examples[0].metadata.get("phoenix_dataset_version_id")
        if phoenix_version:
            version_id = phoenix_version

        # Check for Cat Cafe metadata
        cafe_id = examples[0].metadata.get("cat_cafe_dataset_id")
        if cafe_id:
            dataset_id = cafe_id
        cafe_version = examples[0].metadata.get("cat_cafe_dataset_version")
        if cafe_version:
            version_id = cafe_version

    return examples, dataset_id, version_id


def build_evaluator_functions(evaluator_names: list[str]) -> list[Any]:
    """Build evaluator functions for the Orchestrator.

    The Orchestrator's executor calls evaluators with EvalInput and expects EvalOutput.
    The @evaluator decorator already creates functions with this signature, so we
    just need to retrieve them and set __name__ for the orchestrator to use.
    """
    from ...sdk.decorators import get_evaluator

    evaluator_fns = []

    for name in evaluator_names:
        eval_fn = get_evaluator(name)
        if eval_fn is None:
            continue

        # The @evaluator decorator already wraps to take EvalInput and return EvalOutput
        # Just ensure __name__ is set for the orchestrator to identify evaluators
        eval_fn.__name__ = name
        evaluator_fns.append(eval_fn)

    return evaluator_fns


def _parse_params(param_args: list[str]) -> dict[str, Any]:
    """Parse --param KEY=VALUE arguments into a dict."""
    params: dict[str, Any] = {}
    for param in param_args:
        if "=" not in param:
            print(f"Warning: Invalid param format '{param}', expected KEY=VALUE", file=sys.stderr)
            continue
        key, value = param.split("=", 1)
        # Try to parse as JSON for complex values
        try:
            params[key] = json.loads(value)
        except json.JSONDecodeError:
            params[key] = value
    return params


def output_text(summary: Any, backend: str) -> None:
    """Print summary as text."""
    print("\n" + "=" * 60)
    print("Experiment Complete")
    print("=" * 60)
    print(f"Experiment ID: {summary.experiment_id}")
    print(f"Total examples: {summary.total_examples}")
    print(f"Successful: {summary.successful_examples}")
    print(f"Failed: {summary.failed_examples}")

    if summary.average_scores:
        print("\nScores:")
        for name, score in summary.average_scores.items():
            print(f"  {name}: {score:.3f}")

    print(f"\nStorage: {backend}")


def output_json(summary: Any) -> None:
    """Print summary as JSON."""
    output = {
        "experiment_id": summary.experiment_id,
        "total_examples": summary.total_examples,
        "successful_examples": summary.successful_examples,
        "failed_examples": summary.failed_examples,
        "average_scores": summary.average_scores or {},
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
