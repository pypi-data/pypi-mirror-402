"""Cache protocol definition for HyperX SDK."""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Cache(Protocol):
    """Protocol for cache backends.

    This protocol defines the interface that all cache implementations must follow.
    It is runtime-checkable, allowing isinstance() checks against cache implementations.

    Example:
        >>> from hyperx.cache import Cache, InMemoryCache
        >>> cache = InMemoryCache()
        >>> isinstance(cache, Cache)
        True
    """

    def get(self, key: str) -> Any | None:
        """Get cached value or None if not found/expired.

        Args:
            key: The cache key to retrieve.

        Returns:
            The cached value if found and not expired, None otherwise.
        """
        ...

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set cached value with optional TTL in seconds.

        Args:
            key: The cache key to set.
            value: The value to cache.
            ttl: Time-to-live in seconds. If None, uses the cache's default TTL.
        """
        ...

    def delete(self, key: str) -> bool:
        """Delete cached value.

        Args:
            key: The cache key to delete.

        Returns:
            True if the key existed and was deleted, False otherwise.
        """
        ...

    def clear(self) -> None:
        """Clear all cached values."""
        ...
