"""Redis cache backend.

Requires: pip install hyperx[redis]
"""

from __future__ import annotations

import json
from typing import Any

try:
    import redis
except ImportError as e:
    raise ImportError(
        "Redis cache requires the redis package. "
        "Install with: pip install hyperx[redis]"
    ) from e


class RedisCache:
    """Redis-backed cache for distributed environments.

    This cache implementation uses Redis as the backend storage, making it
    suitable for distributed systems where multiple processes or services
    need to share cached data.

    Args:
        url: Redis URL (default: redis://localhost:6379)
        prefix: Key prefix for namespacing (default: "hyperx:")
        ttl: Default TTL in seconds (default: 300)

    Example:
        >>> cache = RedisCache(url="redis://localhost:6379")
        >>> cache.set("key", {"data": 123})
        >>> cache.get("key")
        {'data': 123}

        >>> # With custom TTL
        >>> cache.set("short_lived", "value", ttl=60)

        >>> # Delete and clear
        >>> cache.delete("key")
        True
        >>> cache.clear()
    """

    def __init__(
        self,
        url: str = "redis://localhost:6379",
        prefix: str = "hyperx:",
        ttl: int = 300,
    ) -> None:
        """Initialize the Redis cache.

        Args:
            url: Redis connection URL.
            prefix: Key prefix for namespacing cache keys.
            ttl: Default time-to-live in seconds for cached entries.
        """
        self._client = redis.from_url(url)
        self._prefix = prefix
        self._default_ttl = ttl

    def _make_key(self, key: str) -> str:
        """Create a prefixed key for Redis storage.

        Args:
            key: The user-provided cache key.

        Returns:
            The key with the configured prefix prepended.
        """
        return f"{self._prefix}{key}"

    def get(self, key: str) -> Any | None:
        """Get cached value or None if not found/expired.

        Args:
            key: The cache key to retrieve.

        Returns:
            The cached value if found and not expired, None otherwise.
        """
        data = self._client.get(self._make_key(key))
        if data is None:
            return None
        return json.loads(data)

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set cached value with TTL.

        Args:
            key: The cache key to set.
            value: The value to cache. Must be JSON-serializable.
            ttl: Time-to-live in seconds. If None, uses the default TTL.
        """
        ttl = ttl if ttl is not None else self._default_ttl
        self._client.setex(
            self._make_key(key),
            ttl,
            json.dumps(value),
        )

    def delete(self, key: str) -> bool:
        """Delete cached value.

        Args:
            key: The cache key to delete.

        Returns:
            True if the key existed and was deleted, False otherwise.
        """
        return bool(self._client.delete(self._make_key(key)))

    def clear(self) -> None:
        """Clear all keys with our prefix.

        Uses Redis SCAN to iterate through keys matching the prefix pattern
        and deletes them in batches. This is safe for large key sets.
        """
        pattern = f"{self._prefix}*"
        cursor = 0
        while True:
            cursor, keys = self._client.scan(cursor, match=pattern)
            if keys:
                self._client.delete(*keys)
            if cursor == 0:
                break
