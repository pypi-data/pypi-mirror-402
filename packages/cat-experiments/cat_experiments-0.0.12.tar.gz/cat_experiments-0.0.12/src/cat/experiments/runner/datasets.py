"""Dataset loading utilities with pluggable backends.

This module provides a protocol for loading datasets from various sources,
with built-in implementations for local files, Cat Cafe, and Phoenix.

Example usage:
    # From local file (auto-detects JSON vs JSONL)
    examples = load_dataset("data/test.jsonl")
    examples = load_dataset(Path("data/test.json"))

    # From Cat Cafe
    examples = load_dataset("cat-cafe://helpdesk_v1")
    examples = load_dataset("cat-cafe://helpdesk_v1", base_url="http://localhost:8000")

    # From Phoenix
    examples = load_dataset("phoenix://helpdesk_v1")
    examples = load_dataset("phoenix://helpdesk_v1", version="v2")

    # Custom loader
    examples = load_dataset(MyCustomLoader(config))
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from ..protocol import DatasetExample
from ..protocol.serde import dataset_example_from_dict


@runtime_checkable
class DatasetLoader(Protocol):
    """Protocol for loading datasets from various sources.

    Implementations should return a list of DatasetExample objects.
    The source data is expected to be in the standard schema compatible
    with DatasetExample.from_dict().

    Example implementation:
        class MyLoader:
            def __init__(self, connection_string: str):
                self.conn = connection_string

            def load(self) -> list[DatasetExample]:
                data = fetch_from_my_source(self.conn)
        return [dataset_example_from_dict(item) for item in data]
    """

    def load(self) -> list[DatasetExample]:
        """Load all examples from the dataset."""
        ...


class FileLoader:
    """Load dataset from local JSON or JSONL file.

    Auto-detects format based on file extension:
    - .jsonl: One JSON object per line
    - .json (or other): JSON array at top level

    Args:
        path: Path to the dataset file

    Example:
        loader = FileLoader("data/test.jsonl")
        examples = loader.load()
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> list[DatasetExample]:
        """Load examples from the file."""
        if not self.path.exists():
            raise FileNotFoundError(f"Dataset file not found: {self.path}")

        with open(self.path, encoding="utf-8") as f:
            if self.path.suffix == ".jsonl":
                # JSONL: one JSON object per line
                data = [json.loads(line) for line in f if line.strip()]
            else:
                # JSON: expect array at top level
                content = json.load(f)
                if not isinstance(content, list):
                    raise ValueError(
                        f"Expected JSON array at top level, got {type(content).__name__}"
                    )
                data = content

        return [dataset_example_from_dict(item) for item in data]


class CatCafeLoader:
    """Load dataset from Cat Cafe API.

    Args:
        dataset_name: Name or ID of the dataset
        base_url: Cat Cafe server URL (defaults to CAT_CAFE_BASE_URL env var)

    Example:
        loader = CatCafeLoader("helpdesk_v1")
        examples = loader.load()

        # With custom URL
        loader = CatCafeLoader("helpdesk_v1", base_url="http://localhost:8000")
        examples = loader.load()
    """

    def __init__(
        self,
        dataset_name: str,
        *,
        base_url: str | None = None,
    ) -> None:
        self.dataset_name = dataset_name
        self.base_url = base_url or os.environ.get("CAT_CAFE_BASE_URL")

    def load(self) -> list[DatasetExample]:
        """Load examples from Cat Cafe."""
        try:
            from cat.cafe.client import CATCafeClient
        except ImportError as exc:
            raise ImportError(
                "Cat Cafe client required for CatCafeLoader. "
                "Install with: pip install cat-cafe-client"
            ) from exc

        client = CATCafeClient(base_url=self.base_url) if self.base_url else CATCafeClient()

        # Try fetch by name first
        examples_data: list[dict[str, Any]] = []
        dataset_obj = None

        fetch_by_name = getattr(client, "fetch_dataset_by_name", None)
        if callable(fetch_by_name):
            try:
                dataset_obj = fetch_by_name(self.dataset_name)
            except Exception:
                pass

        if dataset_obj:
            examples_data = _extract_examples(dataset_obj)

        # Fallback to ID-based fetch
        if not examples_data:
            dataset_id = self.dataset_name

            # Try to resolve name to ID
            find_by_name = getattr(client, "find_dataset_by_name", None)
            if callable(find_by_name):
                try:
                    meta = find_by_name(self.dataset_name)
                    if meta:
                        if isinstance(meta, dict):
                            dataset_id = meta.get("id") or meta.get("dataset_id") or dataset_id
                        else:
                            dataset_id = (
                                getattr(meta, "id", None)
                                or getattr(meta, "dataset_id", None)
                                or dataset_id
                            )
                except Exception:
                    pass

            examples_data = client.get_dataset_examples(dataset_id)

        return [dataset_example_from_dict(item) for item in examples_data]


class PhoenixLoader:
    """Load dataset from Phoenix API.

    Args:
        dataset_name: Name of the dataset
        base_url: Phoenix server URL (defaults to PHOENIX_BASE_URL env var)
        version: Optional dataset version ID

    Example:
        loader = PhoenixLoader("helpdesk_v1")
        examples = loader.load()

        # With version
        loader = PhoenixLoader("helpdesk_v1", version="v2")
        examples = loader.load()
    """

    def __init__(
        self,
        dataset_name: str,
        *,
        base_url: str | None = None,
        version: str | None = None,
    ) -> None:
        self.dataset_name = dataset_name
        self.base_url = base_url or os.environ.get("PHOENIX_BASE_URL")
        self.version = version

    def load(self) -> list[DatasetExample]:
        """Load examples from Phoenix.

        The returned examples will have dataset_id and dataset_version_id
        stored in their metadata for use by the Phoenix listener.
        """
        try:
            from phoenix.client import Client as PhoenixClient
        except ImportError as exc:
            raise ImportError(
                "Phoenix client required for PhoenixLoader. "
                "Install with: pip install arize-phoenix-client"
            ) from exc

        client_kwargs: dict[str, Any] = {}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url

        client = PhoenixClient(**client_kwargs)
        dataset = client.datasets.get_dataset(
            dataset=self.dataset_name,
            version_id=self.version,
        )

        # Extract dataset ID and version for Phoenix listener
        dataset_id = getattr(dataset, "id", None)
        dataset_version_id = getattr(dataset, "version_id", None)

        examples_data = _extract_examples(dataset)
        examples = [dataset_example_from_dict(item) for item in examples_data]

        # Store dataset metadata in each example for the Phoenix listener
        for example in examples:
            if dataset_id:
                example.metadata.setdefault("phoenix_dataset_id", dataset_id)
            if dataset_version_id:
                example.metadata.setdefault("phoenix_dataset_version_id", dataset_version_id)

        return examples


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
            # Convert object to dict
            result.append(
                {
                    "id": getattr(ex, "id", None),
                    "input": getattr(ex, "input", {}),
                    "output": getattr(ex, "output", {}),
                    "metadata": getattr(ex, "metadata", {}),
                }
            )
    return result


def load_dataset(
    source: str | Path | DatasetLoader,
    *,
    base_url: str | None = None,
    version: str | None = None,
) -> list[DatasetExample]:
    """Load dataset from various sources.

    Args:
        source: One of:
            - Path or string path to local JSON/JSONL file
            - URI string like "cat-cafe://dataset_name" or "phoenix://dataset_name"
            - Any object implementing the DatasetLoader protocol
        base_url: Base URL for remote loaders (Cat Cafe or Phoenix)
        version: Version ID for Phoenix datasets

    Returns:
        List of DatasetExample objects

    Example:
        # Local file
        examples = load_dataset("data/test.jsonl")
        examples = load_dataset(Path("data/test.json"))

        # Cat Cafe
        examples = load_dataset("cat-cafe://helpdesk_v1")
        examples = load_dataset("cat-cafe://helpdesk_v1", base_url="http://localhost:8000")

        # Phoenix
        examples = load_dataset("phoenix://helpdesk_v1")
        examples = load_dataset("phoenix://helpdesk_v1", version="v2")

        # Custom loader
        examples = load_dataset(MyCustomLoader(config))
    """
    # Already a loader
    if isinstance(source, DatasetLoader):
        return source.load()

    # Path object - use FileLoader
    if isinstance(source, Path):
        return FileLoader(source).load()

    # String - parse as URI or path
    source_str = str(source)

    if source_str.startswith("cat-cafe://"):
        dataset_name = source_str[len("cat-cafe://") :]
        return CatCafeLoader(dataset_name, base_url=base_url).load()

    if source_str.startswith("phoenix://"):
        dataset_name = source_str[len("phoenix://") :]
        return PhoenixLoader(dataset_name, base_url=base_url, version=version).load()

    if source_str.startswith("file://"):
        file_path = source_str[len("file://") :]
        return FileLoader(file_path).load()

    # Default: treat as file path
    return FileLoader(source_str).load()


__all__ = [
    "DatasetLoader",
    "FileLoader",
    "CatCafeLoader",
    "PhoenixLoader",
    "load_dataset",
]
