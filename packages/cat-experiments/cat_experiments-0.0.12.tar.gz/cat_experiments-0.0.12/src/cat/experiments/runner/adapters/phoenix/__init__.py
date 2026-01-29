"""Phoenix adapter package that mirrors experiments into Phoenix.

Importing from this module keeps the optional phoenix-client dependency isolated.
"""

from .backend import PhoenixStorageBackend

__all__ = ["PhoenixStorageBackend"]
