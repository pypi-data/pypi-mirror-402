"""Tests for async HyperX client."""

import pytest

from hyperx import AsyncHyperX


def test_async_api_key_validation():
    """Async client also validates API key format."""
    with pytest.raises(ValueError, match="must start with"):
        AsyncHyperX(api_key="invalid_key")


def test_async_api_key_accepted():
    """Valid API key format is accepted by async client."""
    client = AsyncHyperX(api_key="hx_sk_test_12345678", base_url="http://localhost:8080")
    assert client is not None


def test_async_resources_available():
    """Async client has all expected resources."""
    client = AsyncHyperX(api_key="hx_sk_test_12345678", base_url="http://localhost:8080")

    assert hasattr(client, "entities")
    assert hasattr(client, "hyperedges")
    assert hasattr(client, "paths")
    assert hasattr(client, "search")


@pytest.mark.asyncio
async def test_async_context_manager():
    """Async client works as async context manager."""
    async with AsyncHyperX(
        api_key="hx_sk_test_12345678",
        base_url="http://localhost:8080"
    ) as db:
        assert db is not None
