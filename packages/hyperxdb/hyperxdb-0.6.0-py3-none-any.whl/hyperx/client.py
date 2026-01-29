"""HyperX client - main entry point for the SDK."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from hyperx.events import Event, EventRegistry
from hyperx.http import DEFAULT_BASE_URL, HTTPClient
from hyperx.resources.batch import BatchAPI
from hyperx.resources.entities import EntitiesAPI
from hyperx.resources.events import EventsAPI
from hyperx.resources.hyperedges import HyperedgesAPI
from hyperx.resources.paths import PathsAPI
from hyperx.resources.search import SearchAPI
from hyperx.resources.triggers import TriggersAPI
from hyperx.resources.webhooks import WebhooksAPI

if TYPE_CHECKING:
    from hyperx.cache.base import Cache
    from hyperx.query import Query, QueryExecutor


class HyperX:
    """HyperX client for interacting with the HyperX API.

    Example:
        >>> from hyperx import HyperX
        >>> db = HyperX(api_key="hx_sk_...")
        >>> entity = db.entities.create(name="React", entity_type="concept")
        >>> edge = db.hyperedges.create(
        ...     description="React provides Hooks",
        ...     members=[
        ...         {"entity_id": entity.id, "role": "subject"},
        ...         {"entity_id": "e:hooks", "role": "object"},
        ...     ]
        ... )

        >>> # With caching
        >>> from hyperx.cache import InMemoryCache
        >>> cache = InMemoryCache(max_size=100, ttl=300)
        >>> db = HyperX(api_key="hx_sk_...", cache=cache)
        >>> # Repeated path queries will use cache
        >>> paths = db.paths.find("e:start", "e:end")
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
        """Initialize HyperX client.

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

        self._http = HTTPClient(api_key, base_url, timeout)
        self._cache = cache
        self._server_cache = server_cache
        self._event_registry = EventRegistry()

        self.entities = EntitiesAPI(self._http)
        self.hyperedges = HyperedgesAPI(self._http)
        self.paths = PathsAPI(self._http, cache=cache)
        self.search = SearchAPI(self._http, cache=cache)
        self.batch = BatchAPI(self._http)
        self.webhooks = WebhooksAPI(self._http)
        self.events = EventsAPI(self._http)
        self.triggers = TriggersAPI(self._http)

    def query(self, query: Query) -> QueryExecutor:
        """Create query executor for fluent queries.

        Build complex queries with role-based filtering using the Query builder,
        then execute them with the returned QueryExecutor.

        Args:
            query: A Query object built with the fluent Query builder

        Returns:
            QueryExecutor that can be used to execute the query

        Example:
            >>> from hyperx.query import Query
            >>> q = Query().where(role="subject", entity="e:react").limit(10)
            >>> results = db.query(q).execute()
        """
        from hyperx.query import QueryExecutor

        return QueryExecutor(self._http, query)

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

        Args:
            event: The event to dispatch

        Returns:
            Number of handlers that were called
        """
        return self._event_registry.dispatch(event)

    def close(self) -> None:
        """Close the client and release resources."""
        self._http.close()

    def __enter__(self) -> HyperX:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
