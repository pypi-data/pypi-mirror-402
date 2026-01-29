"""Async Paths API resource - the hero feature.

Multi-hop reasoning paths across hypergraph relationships.
This is HyperX's key differentiator from vector databases.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from hyperx.http import AsyncHTTPClient
from hyperx.models import PathResult, PathsResponse

if TYPE_CHECKING:
    from hyperx.cache.base import Cache


class AsyncPathsAPI:
    """Async API for finding multi-hop paths between entities.

    This is HyperX's differentiating feature - intersection-constrained
    pathfinding across hypergraph relationships enables reasoning that
    vector databases cannot perform.

    Example:
        >>> async with AsyncHyperX(api_key="hx_sk_...") as db:
        ...     paths = await db.paths.find(
        ...         from_entity="e:useState",
        ...         to_entity="e:redux",
        ...         max_hops=4
        ...     )
        ...     for path in paths:
        ...         print(f"Cost: {path.cost}, Hops: {len(path.hyperedges)}")
    """

    def __init__(self, http: AsyncHTTPClient, cache: Cache | None = None):
        self._http = http
        self._cache = cache

    def _cache_key(
        self,
        from_entity: str,
        to_entity: str,
        max_hops: int,
        intersection_size: int,
        k_paths: int,
    ) -> str:
        """Generate a cache key for paths.find() parameters."""
        return f"paths:{from_entity}:{to_entity}:{max_hops}:{intersection_size}:{k_paths}"

    async def find(
        self,
        from_entity: str,
        to_entity: str,
        max_hops: int = 4,
        intersection_size: int = 1,
        k_paths: int = 3,
        *,
        cache: bool | None = None,
        cache_hint: Literal["short", "medium", "long"] | None = None,
    ) -> list[PathResult]:
        """Find multi-hop paths between two entities.

        This implements intersection-constrained pathfinding inspired by
        the HOG-DB paper from ETH Zurich. Paths traverse through hyperedges
        that share bridge entities.

        Args:
            from_entity: Starting entity ID
            to_entity: Target entity ID
            max_hops: Maximum number of hyperedge hops (default: 4)
            intersection_size: Minimum bridge size between hyperedges (default: 1)
            k_paths: Number of paths to return (default: 3)
            cache: Override cache behavior. None uses client default,
                   True forces caching, False bypasses cache.
            cache_hint: Server-side cache hint ("short", "medium", "long")
                        to indicate how long the server should cache results.

        Returns:
            List of PathResult objects, each containing:
            - hyperedges: Ordered list of hyperedge IDs in the path
            - bridges: Entity IDs that connect adjacent hyperedges
            - cost: Total path cost (lower is better)

        Example:
            >>> # Find how useState relates to Redux
            >>> async with AsyncHyperX(api_key="hx_sk_...") as db:
            ...     paths = await db.paths.find(
            ...         from_entity="e:useState",
            ...         to_entity="e:redux",
            ...         max_hops=4,
            ...         k_paths=5
            ...     )
            ...     for path in paths:
            ...         print(f"Path via: {' -> '.join(path.hyperedges)}")
        """
        # Determine if caching is enabled
        use_cache = cache if cache is not None else (self._cache is not None)

        # Generate cache key
        cache_key = self._cache_key(
            from_entity, to_entity, max_hops, intersection_size, k_paths
        )

        # Check cache if enabled (sync operation - InMemoryCache is synchronous)
        if use_cache and self._cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return [PathResult.model_validate(p) for p in cached]

        # Build payload
        payload = {
            "from": from_entity,
            "to": to_entity,
            "constraints": {
                "max_hops": max_hops,
                "intersection_size": intersection_size,
                "k_paths": k_paths,
            },
        }

        # Add server-side cache hint if provided
        if cache_hint is not None:
            payload["cache_hint"] = cache_hint

        # Make API call
        data = await self._http.post("/v1/paths", json=payload)
        response = PathsResponse.model_validate(data)

        # Store in cache if enabled (sync operation)
        if use_cache and self._cache:
            self._cache.set(cache_key, [p.model_dump() for p in response.paths])

        return response.paths
