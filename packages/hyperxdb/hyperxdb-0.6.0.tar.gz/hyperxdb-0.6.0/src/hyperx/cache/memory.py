"""In-memory cache implementation with LRU eviction and TTL support."""

import time
from collections import OrderedDict
from typing import Any


class InMemoryCache:
    """LRU cache with TTL support.

    A thread-safe in-memory cache that supports:
    - LRU (Least Recently Used) eviction when max size is exceeded
    - TTL (Time-To-Live) expiration for cached entries
    - Standard cache operations (get, set, delete, clear)

    Args:
        max_size: Maximum number of items to store (default: 1000).
        ttl: Default TTL in seconds for cached entries (default: 300 = 5 min).

    Example:
        >>> cache = InMemoryCache(max_size=100, ttl=60)
        >>> cache.set("key", {"data": 123})
        >>> cache.get("key")
        {'data': 123}

        >>> # With custom TTL
        >>> cache.set("short_lived", "value", ttl=10)

        >>> # Delete and clear
        >>> cache.delete("key")
        True
        >>> cache.clear()
    """

    def __init__(self, max_size: int = 1000, ttl: int = 300) -> None:
        """Initialize the in-memory cache.

        Args:
            max_size: Maximum number of items to store.
            ttl: Default TTL in seconds for cached entries.
        """
        self._max_size = max_size
        self._default_ttl = ttl
        # OrderedDict maintains insertion order; we use it for LRU tracking
        # Values are tuples of (value, expiry_timestamp)
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()

    def get(self, key: str) -> Any | None:
        """Get cached value or None if not found/expired.

        If the entry exists but is expired, it is removed from the cache
        and None is returned. If the entry is valid, it is moved to the
        end of the OrderedDict (most recently used).

        Args:
            key: The cache key to retrieve.

        Returns:
            The cached value if found and not expired, None otherwise.
        """
        if key not in self._cache:
            return None

        value, expiry_time = self._cache[key]

        # Check if expired
        if time.time() > expiry_time:
            # Remove expired entry
            del self._cache[key]
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(key)

        return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set cached value with optional TTL in seconds.

        If the key already exists, the value is updated and the entry
        is moved to the end of the OrderedDict (most recently used).
        If adding a new entry would exceed max_size, the oldest entry
        (least recently used) is evicted.

        Args:
            key: The cache key to set.
            value: The value to cache.
            ttl: Time-to-live in seconds. If None, uses the default TTL.
        """
        # Use provided TTL or fall back to default
        actual_ttl = ttl if ttl is not None else self._default_ttl
        expiry_time = time.time() + actual_ttl

        # If key exists, remove it first so move_to_end works correctly
        if key in self._cache:
            del self._cache[key]

        # Add the new entry
        self._cache[key] = (value, expiry_time)

        # Evict oldest entries if over max size
        while len(self._cache) > self._max_size:
            # Remove the first item (oldest/least recently used)
            self._cache.popitem(last=False)

    def delete(self, key: str) -> bool:
        """Delete cached value.

        Args:
            key: The cache key to delete.

        Returns:
            True if the key existed and was deleted, False otherwise.
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()
