"""Async HyperX client - main entry point for async SDK usage."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from hyperx.events import Event, EventRegistry
from hyperx.http import DEFAULT_BASE_URL, AsyncHTTPClient
from hyperx.resources.async_batch import AsyncBatchAPI
from hyperx.resources.async_entities import AsyncEntitiesAPI
from hyperx.resources.async_events import AsyncEventsAPI
from hyperx.resources.async_hyperedges import AsyncHyperedgesAPI
from hyperx.resources.async_paths import AsyncPathsAPI
from hyperx.resources.async_search import AsyncSearchAPI
from hyperx.resources.async_triggers import AsyncTriggersAPI
from hyperx.resources.async_webhooks import AsyncWebhooksAPI

if TYPE_CHECKING:
    from hyperx.cache.base import Cache
    from hyperx.query import AsyncQueryExecutor, Query


class AsyncHyperX:
    """Async HyperX client for interacting with the HyperX API.

    Use this client for async/await code patterns in asyncio applications.
    For synchronous code, use the regular HyperX client instead.

    Example:
        >>> from hyperx import AsyncHyperX
        >>> async with AsyncHyperX(api_key="hx_sk_...") as db:
        ...     entity = await db.entities.create(name="React", entity_type="concept")
        ...     paths = await db.paths.find("e:...", "e:...")

        >>> # With caching
        >>> from hyperx.cache import InMemoryCache
        >>> cache = InMemoryCache(max_size=100, ttl=300)
        >>> async with AsyncHyperX(api_key="hx_sk_...", cache=cache) as db:
        ...     # Repeated path queries will use cache
        ...     paths = await db.paths.find("e:start", "e:end")
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        *,
        cache: Cache | None = None,
        server_cache: bool = False,
    ):
        """Initialize AsyncHyperX client.

        Args:
            api_key: Your HyperX API key (starts with hx_sk_)
            base_url: API base URL (default: https://api.hyperxdb.dev)
            timeout: Request timeout in seconds (default: 30)
            cache: Optional cache backend for client-side caching of expensive
                   operations like path queries and searches.
            server_cache: Enable server-side cache hints. When True, the server
                          may cache results for improved performance.
        """
        if not api_key.startswith("hx_sk_"):
            raise ValueError("API key must start with 'hx_sk_'")

        self._http = AsyncHTTPClient(api_key, base_url, timeout)
        self._cache = cache
        self._server_cache = server_cache
        self._event_registry = EventRegistry()

        self.entities = AsyncEntitiesAPI(self._http)
        self.hyperedges = AsyncHyperedgesAPI(self._http)
        self.paths = AsyncPathsAPI(self._http, cache=cache)
        self.search = AsyncSearchAPI(self._http, cache=cache)
        self.batch = AsyncBatchAPI(self._http)
        self.webhooks = AsyncWebhooksAPI(self._http)
        self.events = AsyncEventsAPI(self._http)
        self.triggers = AsyncTriggersAPI(self._http)

    def query(self, query: Query) -> AsyncQueryExecutor:
        """Create async query executor for fluent queries.

        Build complex queries with role-based filtering using the Query builder,
        then execute them with the returned AsyncQueryExecutor.

        Args:
            query: A Query object built with the fluent Query builder

        Returns:
            AsyncQueryExecutor that can be used to execute the query

        Example:
            >>> from hyperx.query import Query
            >>> q = Query().where(role="subject", entity="e:react").limit(10)
            >>> results = await db.query(q).execute()
        """
        from hyperx.query import AsyncQueryExecutor

        return AsyncQueryExecutor(self._http, query)

    def on(
        self,
        event_pattern: str,
        *,
        filter: dict[str, Any] | None = None,
    ) -> Callable[[Callable[[Event], None]], Callable[[Event], None]]:
        """Decorator to register an event handler.

        Args:
            event_pattern: Event type or pattern with wildcards
                - "entity.created" - specific event
                - "entity.*" - all entity events
                - "*" - all events
            filter: Optional filter conditions
                - {"role": "author"} - only hyperedges with author role

        Returns:
            Decorator function that registers the handler

        Example:
            >>> @db.on("entity.created")
            ... def handle_entity(event):
            ...     print(f"New entity: {event.data['name']}")

            >>> @db.on("hyperedge.created", filter={"role": "author"})
            ... def handle_authorship(event):
            ...     print(f"New authorship relation")
        """

        def decorator(func: Callable[[Event], None]) -> Callable[[Event], None]:
            self._event_registry.register(event_pattern, func, filter)
            return func

        return decorator

    def emit(self, event: Event) -> int:
        """Emit an event to all matching local handlers.

        Primarily for testing and internal use. In production,
        events come from webhooks or streaming.

        Note: This is synchronous even in the async client since event
        handlers are typically simple callbacks.

        Args:
            event: The event to dispatch

        Returns:
            Number of handlers that were called
        """
        return self._event_registry.dispatch(event)

    async def close(self) -> None:
        """Close the client and release resources."""
        await self._http.close()

    async def __aenter__(self) -> AsyncHyperX:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
