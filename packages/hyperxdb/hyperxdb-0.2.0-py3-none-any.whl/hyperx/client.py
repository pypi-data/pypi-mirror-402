"""HyperX client - main entry point for the SDK."""

from hyperx.http import DEFAULT_BASE_URL, HTTPClient
from hyperx.resources.entities import EntitiesAPI
from hyperx.resources.hyperedges import HyperedgesAPI
from hyperx.resources.paths import PathsAPI
from hyperx.resources.search import SearchAPI


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
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
    ):
        """Initialize HyperX client.

        Args:
            api_key: Your HyperX API key (starts with hx_sk_)
            base_url: API base URL (default: https://api.hyperxdb.dev)
            timeout: Request timeout in seconds (default: 30)
        """
        if not api_key.startswith("hx_sk_"):
            raise ValueError("API key must start with 'hx_sk_'")

        self._http = HTTPClient(api_key, base_url, timeout)
        self.entities = EntitiesAPI(self._http)
        self.hyperedges = HyperedgesAPI(self._http)
        self.paths = PathsAPI(self._http)
        self.search = SearchAPI(self._http)

    def close(self) -> None:
        """Close the client and release resources."""
        self._http.close()

    def __enter__(self) -> "HyperX":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
