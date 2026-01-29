"""HyperX Python SDK - The knowledge layer for AI."""

from typing import Union

from hyperx._version import __version__
from hyperx.async_client import AsyncHyperX
from hyperx.batch import (
    BatchItemResult,
    BatchResult,
    EntityCreate,
    EntityDelete,
    HyperedgeCreate,
    HyperedgeDelete,
)
from hyperx.cache import Cache, InMemoryCache
from hyperx.client import HyperX
from hyperx.events import Event, EventHandler, EventRegistry, EventType
from hyperx.exceptions import (
    AuthenticationError,
    HyperXError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from hyperx.models import (
    Entity,
    Hyperedge,
    HyperedgeMember,
    PathResult,
    PathsResponse,
    SearchResult,
    Trigger,
    Webhook,
    WebhookDelivery,
)
from hyperx.query import AsyncQueryExecutor, Query, QueryExecutor, RoleFilter
from hyperx.resources.hyperedges import MemberInput

# Type alias for batch operations
BatchOperation = Union[EntityCreate, HyperedgeCreate, EntityDelete, HyperedgeDelete]

__all__ = [
    # Version
    "__version__",
    # Clients
    "HyperX",
    "AsyncHyperX",
    # Models
    "Entity",
    "Hyperedge",
    "HyperedgeMember",
    "MemberInput",
    "SearchResult",
    "PathResult",
    "PathsResponse",
    "Webhook",
    "WebhookDelivery",
    "Trigger",
    # Batch operations
    "BatchOperation",
    "BatchItemResult",
    "BatchResult",
    "EntityCreate",
    "EntityDelete",
    "HyperedgeCreate",
    "HyperedgeDelete",
    # Cache
    "Cache",
    "InMemoryCache",
    # Query builder
    "Query",
    "QueryExecutor",
    "AsyncQueryExecutor",
    "RoleFilter",
    # Event system
    "Event",
    "EventHandler",
    "EventRegistry",
    "EventType",
    # Exceptions
    "HyperXError",
    "AuthenticationError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "ServerError",
]

# Conditional export for Redis cache backend
try:
    from hyperx.cache import RedisCache

    __all__.append("RedisCache")
except ImportError:
    pass  # Redis not installed


# Lazy imports for optional integrations
def __getattr__(name: str):
    if name == "integrations":
        from hyperx import integrations

        return integrations
    if name == "agents":
        from hyperx import agents

        return agents
    if name == "RedisCache":
        # Provide helpful error message for RedisCache
        try:
            from hyperx.cache import RedisCache

            return RedisCache
        except ImportError:
            raise ImportError(
                "RedisCache requires the redis package. "
                "Install it with: pip install hyperx[redis]"
            ) from None
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
