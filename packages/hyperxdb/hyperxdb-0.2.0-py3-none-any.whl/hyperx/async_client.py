"""Async HyperX client - main entry point for async SDK usage."""

from hyperx.http import DEFAULT_BASE_URL, AsyncHTTPClient
from hyperx.resources.async_entities import AsyncEntitiesAPI
from hyperx.resources.async_hyperedges import AsyncHyperedgesAPI
from hyperx.resources.async_paths import AsyncPathsAPI
from hyperx.resources.async_search import AsyncSearchAPI


class AsyncHyperX:
    """Async HyperX client for interacting with the HyperX API.

    Use this client for async/await code patterns in asyncio applications.
    For synchronous code, use the regular HyperX client instead.

    Example:
        >>> from hyperx import AsyncHyperX
        >>> async with AsyncHyperX(api_key="hx_sk_...") as db:
        ...     entity = await db.entities.create(name="React", entity_type="concept")
        ...     paths = await db.paths.find("e:...", "e:...")
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
    ):
        """Initialize AsyncHyperX client.

        Args:
            api_key: Your HyperX API key (starts with hx_sk_)
            base_url: API base URL (default: https://api.hyperxdb.dev)
            timeout: Request timeout in seconds (default: 30)
        """
        if not api_key.startswith("hx_sk_"):
            raise ValueError("API key must start with 'hx_sk_'")

        self._http = AsyncHTTPClient(api_key, base_url, timeout)
        self.entities = AsyncEntitiesAPI(self._http)
        self.hyperedges = AsyncHyperedgesAPI(self._http)
        self.paths = AsyncPathsAPI(self._http)
        self.search = AsyncSearchAPI(self._http)

    async def close(self) -> None:
        """Close the client and release resources."""
        await self._http.close()

    async def __aenter__(self) -> "AsyncHyperX":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
