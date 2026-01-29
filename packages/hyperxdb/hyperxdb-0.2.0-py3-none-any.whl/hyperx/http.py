"""HTTP client wrapper for HyperX API."""

import contextlib
from typing import Any

import httpx

from hyperx._version import __version__
from hyperx.exceptions import (
    AuthenticationError,
    HyperXError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)

DEFAULT_BASE_URL = "https://api.hyperxdb.dev"
DEFAULT_TIMEOUT = 30.0


class HTTPClient:
    """Synchronous HTTP client for HyperX API."""

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers=self._headers(),
        )

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"hyperx-python/{__version__}",
        }

    def _handle_response(self, response: httpx.Response) -> Any:
        """Handle API response and raise appropriate exceptions."""
        if 200 <= response.status_code < 300:
            return response.json() if response.content else None

        error_body = None
        with contextlib.suppress(ValueError, TypeError):
            error_body = response.json()

        message = error_body.get("message", response.text) if error_body else response.text

        if response.status_code == 401:
            raise AuthenticationError(message, response.status_code, error_body)
        elif response.status_code == 404:
            raise NotFoundError(message, response.status_code, error_body)
        elif response.status_code == 400:
            raise ValidationError(message, response.status_code, error_body)
        elif response.status_code == 429:
            raise RateLimitError(message, response.status_code, error_body)
        elif response.status_code >= 500:
            raise ServerError(message, response.status_code, error_body)
        else:
            raise HyperXError(message, response.status_code, error_body)

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Make GET request."""
        response = self._client.get(path, params=params)
        return self._handle_response(response)

    def post(self, path: str, json: dict[str, Any] | None = None) -> Any:
        """Make POST request."""
        response = self._client.post(path, json=json)
        return self._handle_response(response)

    def put(self, path: str, json: dict[str, Any] | None = None) -> Any:
        """Make PUT request."""
        response = self._client.put(path, json=json)
        return self._handle_response(response)

    def delete(self, path: str) -> Any:
        """Make DELETE request."""
        response = self._client.delete(path)
        return self._handle_response(response)

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()


class AsyncHTTPClient:
    """Asynchronous HTTP client for HyperX API."""

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers=self._headers(),
        )

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"hyperx-python/{__version__}",
        }

    def _handle_response(self, response: httpx.Response) -> Any:
        """Handle API response and raise appropriate exceptions."""
        if 200 <= response.status_code < 300:
            return response.json() if response.content else None

        error_body = None
        with contextlib.suppress(ValueError, TypeError):
            error_body = response.json()

        message = error_body.get("message", response.text) if error_body else response.text

        if response.status_code == 401:
            raise AuthenticationError(message, response.status_code, error_body)
        elif response.status_code == 404:
            raise NotFoundError(message, response.status_code, error_body)
        elif response.status_code == 400:
            raise ValidationError(message, response.status_code, error_body)
        elif response.status_code == 429:
            raise RateLimitError(message, response.status_code, error_body)
        elif response.status_code >= 500:
            raise ServerError(message, response.status_code, error_body)
        else:
            raise HyperXError(message, response.status_code, error_body)

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Make GET request."""
        response = await self._client.get(path, params=params)
        return self._handle_response(response)

    async def post(self, path: str, json: dict[str, Any] | None = None) -> Any:
        """Make POST request."""
        response = await self._client.post(path, json=json)
        return self._handle_response(response)

    async def put(self, path: str, json: dict[str, Any] | None = None) -> Any:
        """Make PUT request."""
        response = await self._client.put(path, json=json)
        return self._handle_response(response)

    async def delete(self, path: str) -> Any:
        """Make DELETE request."""
        response = await self._client.delete(path)
        return self._handle_response(response)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
