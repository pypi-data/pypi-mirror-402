"""Runner package for CLI orchestration and experiment execution.

This package contains the components needed by the CLI orchestrator:
- Orchestrator: Main experiment runner
- Executor: Task/evaluator execution (InProcessExecutor)
- Progress: Progress listener protocol and implementations
- Datasets: Dataset loading utilities
- Adapters: Storage backends (local, phoenix, cat_cafe)
- CLI: Command-line interface

These components are designed to be portable to a Go/Rust implementation
for distribution as a single binary.
"""

from __future__ import annotations

# Adapters are imported from the adapters subpackage
from .adapters import (
    AsyncStorageBackend,
    CatCafeStorageBackend,
    LocalStorageBackend,
    PhoenixStorageBackend,
    StorageBackend,
)
from .datasets import (
    CatCafeLoader,
    DatasetLoader,
    FileLoader,
    PhoenixLoader,
    load_dataset,
)
from .executor import InProcessExecutor
from .orchestrator import Orchestrator
from .progress import NullProgressListener, ProgressListener

__all__ = [
    # Orchestrator
    "Orchestrator",
    # Executor
    "InProcessExecutor",
    # Progress
    "ProgressListener",
    "NullProgressListener",
    # Datasets
    "DatasetLoader",
    "FileLoader",
    "CatCafeLoader",
    "PhoenixLoader",
    "load_dataset",
    # Storage backends
    "StorageBackend",
    "AsyncStorageBackend",
    "LocalStorageBackend",
    "PhoenixStorageBackend",
    "CatCafeStorageBackend",
]
