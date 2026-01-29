"""Adapters that connect cat-experiments to external storage systems.

This package provides backend adapters for various storage systems:
- Local filesystem (built-in, no dependencies)
- Phoenix (requires arize-phoenix-client)
- Cat Cafe (requires cat-cafe-client)

The main protocol is StorageBackend, which provides:
- Dataset loading
- Streaming result persistence
- Resume support
"""

from .local import LocalStorageBackend
from .protocol import AsyncStorageBackend, StorageBackend

__all__ = [
    # Storage protocol
    "StorageBackend",
    "AsyncStorageBackend",
    # Local adapter
    "LocalStorageBackend",
    # Phoenix adapter (lazy import - requires arize-phoenix-client)
    "PhoenixStorageBackend",
    # Cat Cafe adapter (lazy import - requires cat-cafe-client)
    "CatCafeStorageBackend",
]


def __getattr__(name: str) -> type:
    """Lazy import for optional dependencies."""
    if name == "PhoenixStorageBackend":
        from .phoenix import PhoenixStorageBackend

        return PhoenixStorageBackend
    if name == "CatCafeStorageBackend":
        from .cat_cafe import CatCafeStorageBackend

        return CatCafeStorageBackend
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
