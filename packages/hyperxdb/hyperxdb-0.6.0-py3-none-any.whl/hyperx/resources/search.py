"""Search API resource."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

from hyperx.http import HTTPClient
from hyperx.models import Entity, Hyperedge, SearchResult

if TYPE_CHECKING:
    from hyperx.cache.base import Cache


class SearchAPI:
    """API for searching HyperX.

    Supports hybrid search combining vector similarity and text matching.

    Example:
        >>> results = db.search("react state management")
        >>> for entity in results.entities:
        ...     print(entity.name)
    """

    def __init__(self, http: HTTPClient, cache: Cache | None = None):
        self._http = http
        self._cache = cache

    def _cache_key(self, prefix: str, query: str, limit: int) -> str:
        """Generate a cache key for search parameters."""
        query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
        return f"{prefix}:{query_hash}:{limit}"

    def _cache_key_vector(self, embedding: list[float], limit: int) -> str:
        """Generate a cache key for vector search parameters."""
        # Hash the embedding for a compact key
        embedding_str = ",".join(f"{v:.6f}" for v in embedding)
        embedding_hash = hashlib.md5(embedding_str.encode()).hexdigest()[:8]
        return f"search_vector:{embedding_hash}:{limit}"

    def __call__(
        self,
        query: str,
        limit: int = 10,
        *,
        cache: bool | None = None,
        role_filter: dict[str, str] | None = None,
    ) -> SearchResult:
        """Hybrid search across entities and hyperedges.

        Args:
            query: Search query string
            limit: Maximum results to return
            cache: Override cache behavior. None uses client default,
                   True forces caching, False bypasses cache.
            role_filter: Filter hyperedges by role conditions.
                - {"subject": "e:react"} - only hyperedges where React is subject
                - {"subject_type": "library"} - subject is any library type entity
                - Multiple keys are AND conditions

        Returns:
            SearchResult with matching entities and hyperedges
        """
        # Determine if caching is enabled
        use_cache = cache if cache is not None else (self._cache is not None)
        cache_key = self._cache_key("search_hybrid", query, limit)

        # Check cache if enabled
        if use_cache and self._cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return SearchResult(
                    entities=[Entity.model_validate(e) for e in cached.get("entities", [])],
                    hyperedges=[Hyperedge.model_validate(h) for h in cached.get("hyperedges", [])],
                )

        # Build request payload
        payload: dict = {"query": query, "limit": limit}
        if role_filter:
            payload["role_filter"] = role_filter

        # Make API call
        data = self._http.post("/v1/search", json=payload)
        result = SearchResult(
            entities=[Entity.model_validate(e) for e in data.get("entities", [])],
            hyperedges=[Hyperedge.model_validate(h) for h in data.get("hyperedges", [])],
        )

        # Store in cache if enabled
        if use_cache and self._cache:
            self._cache.set(cache_key, {
                "entities": [e.model_dump() for e in result.entities],
                "hyperedges": [h.model_dump() for h in result.hyperedges],
            })

        return result

    def vector(
        self,
        embedding: list[float],
        limit: int = 10,
        *,
        cache: bool | None = None,
        role_filter: dict[str, str] | None = None,
    ) -> SearchResult:
        """Vector-only search using embedding similarity.

        Args:
            embedding: Query embedding vector
            limit: Maximum results to return
            cache: Override cache behavior. None uses client default,
                   True forces caching, False bypasses cache.
            role_filter: Filter hyperedges by role conditions.
                - {"subject": "e:react"} - only hyperedges where React is subject
                - {"subject_type": "library"} - subject is any library type entity
                - Multiple keys are AND conditions

        Returns:
            SearchResult with matching entities and hyperedges
        """
        # Determine if caching is enabled
        use_cache = cache if cache is not None else (self._cache is not None)
        cache_key = self._cache_key_vector(embedding, limit)

        # Check cache if enabled
        if use_cache and self._cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return SearchResult(
                    entities=[Entity.model_validate(e) for e in cached.get("entities", [])],
                    hyperedges=[Hyperedge.model_validate(h) for h in cached.get("hyperedges", [])],
                )

        # Build request payload
        payload: dict = {"embedding": embedding, "limit": limit}
        if role_filter:
            payload["role_filter"] = role_filter

        # Make API call
        data = self._http.post("/v1/search/vector", json=payload)
        result = SearchResult(
            entities=[Entity.model_validate(e) for e in data.get("entities", [])],
            hyperedges=[Hyperedge.model_validate(h) for h in data.get("hyperedges", [])],
        )

        # Store in cache if enabled
        if use_cache and self._cache:
            self._cache.set(cache_key, {
                "entities": [e.model_dump() for e in result.entities],
                "hyperedges": [h.model_dump() for h in result.hyperedges],
            })

        return result

    def text(
        self,
        query: str,
        limit: int = 10,
        *,
        cache: bool | None = None,
        role_filter: dict[str, str] | None = None,
    ) -> SearchResult:
        """Text-only search using BM25 ranking.

        Args:
            query: Text query string
            limit: Maximum results to return
            cache: Override cache behavior. None uses client default,
                   True forces caching, False bypasses cache.
            role_filter: Filter hyperedges by role conditions.
                - {"subject": "e:react"} - only hyperedges where React is subject
                - {"subject_type": "library"} - subject is any library type entity
                - Multiple keys are AND conditions

        Returns:
            SearchResult with matching entities and hyperedges
        """
        # Determine if caching is enabled
        use_cache = cache if cache is not None else (self._cache is not None)
        cache_key = self._cache_key("search_text", query, limit)

        # Check cache if enabled
        if use_cache and self._cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return SearchResult(
                    entities=[Entity.model_validate(e) for e in cached.get("entities", [])],
                    hyperedges=[Hyperedge.model_validate(h) for h in cached.get("hyperedges", [])],
                )

        # Build request payload
        payload: dict = {"query": query, "limit": limit}
        if role_filter:
            payload["role_filter"] = role_filter

        # Make API call
        data = self._http.post("/v1/search/text", json=payload)
        result = SearchResult(
            entities=[Entity.model_validate(e) for e in data.get("entities", [])],
            hyperedges=[Hyperedge.model_validate(h) for h in data.get("hyperedges", [])],
        )

        # Store in cache if enabled
        if use_cache and self._cache:
            self._cache.set(cache_key, {
                "entities": [e.model_dump() for e in result.entities],
                "hyperedges": [h.model_dump() for h in result.hyperedges],
            })

        return result
