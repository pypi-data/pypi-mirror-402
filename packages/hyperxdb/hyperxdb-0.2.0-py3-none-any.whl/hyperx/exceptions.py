"""HyperX SDK exceptions."""

from typing import Any


class HyperXError(Exception):
    """Base exception for HyperX SDK."""

    def __init__(self, message: str, status_code: int | None = None, response: Any = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response = response


class AuthenticationError(HyperXError):
    """Raised when API key is invalid or missing."""
    pass


class NotFoundError(HyperXError):
    """Raised when a resource is not found."""
    pass


class ValidationError(HyperXError):
    """Raised when request validation fails."""
    pass


class RateLimitError(HyperXError):
    """Raised when rate limit is exceeded."""
    pass


class ServerError(HyperXError):
    """Raised when server returns 5xx error."""
    pass
