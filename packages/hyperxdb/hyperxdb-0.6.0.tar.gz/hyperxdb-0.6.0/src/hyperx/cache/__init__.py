"""Cache package for HyperX SDK.

This package provides caching functionality with a protocol-based design
allowing for different cache backend implementations.

Available backends:
    - InMemoryCache: LRU cache with TTL support (always available)
    - RedisCache: Redis-backed cache for distributed environments
                  (requires: pip install hyperx[redis])

Example:
    >>> from hyperx.cache import Cache, InMemoryCache
    >>> cache = InMemoryCache(max_size=100, ttl=60)
    >>> cache.set("key", {"data": 123})
    >>> cache.get("key")
    {'data': 123}
    >>> isinstance(cache, Cache)
    True

    >>> # Redis cache (if redis is installed)
    >>> from hyperx.cache import RedisCache
    >>> cache = RedisCache(url="redis://localhost:6379")
    >>> cache.set("key", {"data": 123})
"""

from hyperx.cache.base import Cache
from hyperx.cache.memory import InMemoryCache

__all__ = ["Cache", "InMemoryCache"]

# Conditional export for Redis cache backend
try:
    from hyperx.cache.redis import RedisCache

    __all__.append("RedisCache")
except ImportError:
    pass  # Redis not installed
