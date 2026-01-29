"""Async Search API resource."""

from hyperx.http import AsyncHTTPClient
from hyperx.models import Entity, Hyperedge, SearchResult


class AsyncSearchAPI:
    """Async API for searching HyperX.

    Supports hybrid search combining vector similarity and text matching.

    Example:
        >>> async with AsyncHyperX(api_key="hx_sk_...") as db:
        ...     results = await db.search("react state management")
        ...     for entity in results.entities:
        ...         print(entity.name)
    """

    def __init__(self, http: AsyncHTTPClient):
        self._http = http

    async def __call__(self, query: str, limit: int = 10) -> SearchResult:
        """Hybrid search across entities and hyperedges.

        Args:
            query: Search query string
            limit: Maximum results to return

        Returns:
            SearchResult with matching entities and hyperedges
        """
        data = await self._http.post("/v1/search", json={"query": query, "limit": limit})
        return SearchResult(
            entities=[Entity.model_validate(e) for e in data.get("entities", [])],
            hyperedges=[Hyperedge.model_validate(h) for h in data.get("hyperedges", [])],
        )

    async def vector(self, embedding: list[float], limit: int = 10) -> SearchResult:
        """Vector-only search using embedding similarity.

        Args:
            embedding: Query embedding vector
            limit: Maximum results to return

        Returns:
            SearchResult with matching entities and hyperedges
        """
        data = await self._http.post(
            "/v1/search/vector", json={"embedding": embedding, "limit": limit}
        )
        return SearchResult(
            entities=[Entity.model_validate(e) for e in data.get("entities", [])],
            hyperedges=[Hyperedge.model_validate(h) for h in data.get("hyperedges", [])],
        )

    async def text(self, query: str, limit: int = 10) -> SearchResult:
        """Text-only search using BM25 ranking.

        Args:
            query: Text query string
            limit: Maximum results to return

        Returns:
            SearchResult with matching entities and hyperedges
        """
        data = await self._http.post("/v1/search/text", json={"query": query, "limit": limit})
        return SearchResult(
            entities=[Entity.model_validate(e) for e in data.get("entities", [])],
            hyperedges=[Hyperedge.model_validate(h) for h in data.get("hyperedges", [])],
        )
