"""Local storage adapter for running experiments without external services.

Provides file-based storage with no optional dependencies.
"""

from .backend import LocalStorageBackend

__all__ = ["LocalStorageBackend"]
