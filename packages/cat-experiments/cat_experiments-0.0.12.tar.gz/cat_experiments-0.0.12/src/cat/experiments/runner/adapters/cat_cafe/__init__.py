"""Cat Cafe adapter package that mirrors experiments into Cat Cafe.

Importing from this module keeps the optional cat-cafe-client dependency isolated.
"""

from .backend import CatCafeStorageBackend

__all__ = ["CatCafeStorageBackend"]
