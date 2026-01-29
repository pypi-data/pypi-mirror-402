"""Fluent query builder for complex hypergraph queries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from hyperx.http import AsyncHTTPClient, HTTPClient
    from hyperx.models import SearchResult


@dataclass
class RoleFilter:
    """A single role-based filter condition.

    Attributes:
        role: The role name to filter on (e.g., "subject", "author", "object")
        entity: Optional specific entity ID to match
        entity_type: Optional entity type filter
    """

    role: str
    entity: str | None = None
    entity_type: str | None = None


class Query:
    """Fluent query builder for role-based hypergraph queries.

    Build complex queries with role-based filtering, graph traversal,
    temporal constraints, and text search.

    Example:
        >>> query = (
        ...     Query()
        ...     .where(role="subject", entity="e:react")
        ...     .or_where(role="subject", entity="e:vue")
        ...     .with_hops(max=2)
        ...     .limit(20)
        ... )
        >>> results = db.query(query).execute()
    """

    def __init__(self) -> None:
        """Initialize an empty query builder."""
        self._where_filters: list[RoleFilter] = []
        self._or_filters: list[RoleFilter] = []
        self._max_hops: int | None = None
        self._limit: int = 100
        self._offset: int = 0
        self._as_of: datetime | None = None
        self._text_query: str | None = None

    def where(
        self,
        role: str,
        *,
        entity: str | None = None,
        entity_type: str | None = None,
    ) -> Query:
        """Add AND filter condition.

        Multiple where() calls are combined with AND logic - all conditions
        must match for a result to be included.

        Args:
            role: Required role name (e.g., "subject", "author", "object")
            entity: Optional specific entity ID to match
            entity_type: Optional entity type filter

        Returns:
            Self for method chaining
        """
        self._where_filters.append(
            RoleFilter(
                role=role,
                entity=entity,
                entity_type=entity_type,
            )
        )
        return self

    def or_where(
        self,
        role: str,
        *,
        entity: str | None = None,
        entity_type: str | None = None,
    ) -> Query:
        """Add OR filter condition.

        Results matching any or_where() condition are included in addition
        to results matching where() conditions.

        Args:
            role: Required role name (e.g., "subject", "author", "object")
            entity: Optional specific entity ID to match
            entity_type: Optional entity type filter

        Returns:
            Self for method chaining
        """
        self._or_filters.append(
            RoleFilter(
                role=role,
                entity=entity,
                entity_type=entity_type,
            )
        )
        return self

    def with_hops(self, max: int) -> Query:
        """Set maximum graph hops for expansion.

        When set, the query will expand results to include connected
        entities and hyperedges up to the specified number of hops away.

        Args:
            max: Maximum number of graph hops to traverse

        Returns:
            Self for method chaining
        """
        self._max_hops = max
        return self

    def limit(self, n: int) -> Query:
        """Set result limit.

        Args:
            n: Maximum number of results to return

        Returns:
            Self for method chaining
        """
        self._limit = n
        return self

    def offset(self, n: int) -> Query:
        """Set result offset for pagination.

        Args:
            n: Number of results to skip

        Returns:
            Self for method chaining
        """
        self._offset = n
        return self

    def temporal(self, as_of: datetime | str) -> Query:
        """Filter to graph state as of given time.

        Query the hypergraph as it existed at a specific point in time,
        using bi-temporal validity periods.

        Args:
            as_of: Timestamp to query (datetime object or ISO format string)

        Returns:
            Self for method chaining
        """
        if isinstance(as_of, str):
            as_of = datetime.fromisoformat(as_of)
        self._as_of = as_of
        return self

    def text(self, query: str) -> Query:
        """Add text search query.

        Combines role-based filtering with full-text search across
        entity names and hyperedge descriptions.

        Args:
            query: Text search query string

        Returns:
            Self for method chaining
        """
        self._text_query = query
        return self

    def to_dict(self) -> dict[str, Any]:
        """Serialize query to API format.

        Returns:
            Dictionary representation suitable for API request body
        """
        result: dict[str, Any] = {
            "limit": self._limit,
            "offset": self._offset,
        }

        if self._where_filters:
            result["where"] = [
                {
                    k: v
                    for k, v in [
                        ("role", f.role),
                        ("entity", f.entity),
                        ("entity_type", f.entity_type),
                    ]
                    if v is not None
                }
                for f in self._where_filters
            ]

        if self._or_filters:
            result["or_where"] = [
                {
                    k: v
                    for k, v in [
                        ("role", f.role),
                        ("entity", f.entity),
                        ("entity_type", f.entity_type),
                    ]
                    if v is not None
                }
                for f in self._or_filters
            ]

        if self._max_hops is not None:
            result["max_hops"] = self._max_hops

        if self._as_of is not None:
            result["as_of"] = self._as_of.isoformat()

        if self._text_query is not None:
            result["text"] = self._text_query

        return result


class QueryExecutor:
    """Executes a Query against the HyperX API (synchronous).

    This class is returned by HyperX.query() and provides the execute()
    method to run the query.

    Example:
        >>> executor = db.query(Query().where(role="subject"))
        >>> results = executor.execute()
    """

    def __init__(self, http: HTTPClient, query: Query) -> None:
        """Initialize the query executor.

        Args:
            http: HTTP client for making API requests
            query: Query object to execute
        """
        self._http = http
        self._query = query

    def execute(self) -> SearchResult:
        """Execute the query and return results.

        Returns:
            SearchResult containing matched entities and hyperedges
        """
        from hyperx.models import SearchResult

        data = self._http.post("/v1/query", json=self._query.to_dict())
        return SearchResult.model_validate(data)


class AsyncQueryExecutor:
    """Executes a Query against the HyperX API (asynchronous).

    This class is returned by AsyncHyperX.query() and provides the execute()
    coroutine to run the query.

    Example:
        >>> executor = db.query(Query().where(role="subject"))
        >>> results = await executor.execute()
    """

    def __init__(self, http: AsyncHTTPClient, query: Query) -> None:
        """Initialize the async query executor.

        Args:
            http: Async HTTP client for making API requests
            query: Query object to execute
        """
        self._http = http
        self._query = query

    async def execute(self) -> SearchResult:
        """Execute the query and return results.

        Returns:
            SearchResult containing matched entities and hyperedges
        """
        from hyperx.models import SearchResult

        data = await self._http.post("/v1/query", json=self._query.to_dict())
        return SearchResult.model_validate(data)
