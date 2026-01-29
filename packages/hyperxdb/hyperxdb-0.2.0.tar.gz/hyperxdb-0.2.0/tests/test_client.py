"""Tests for HyperX client."""

import pytest

from hyperx import HyperX


def test_api_key_validation():
    """API key must start with hx_sk_."""
    with pytest.raises(ValueError, match="must start with"):
        HyperX(api_key="invalid_key")


def test_api_key_accepted():
    """Valid API key format is accepted."""
    client = HyperX(api_key="hx_sk_test_12345678", base_url="http://localhost:8080")
    assert client is not None
    client.close()


def test_context_manager():
    """Client works as context manager."""
    with HyperX(api_key="hx_sk_test_12345678", base_url="http://localhost:8080") as db:
        assert db is not None


def test_custom_timeout():
    """Client accepts custom timeout."""
    client = HyperX(
        api_key="hx_sk_test_12345678",
        base_url="http://localhost:8080",
        timeout=60.0,
    )
    assert client is not None
    client.close()


def test_resources_available():
    """Client has all expected resources."""
    with HyperX(api_key="hx_sk_test_12345678", base_url="http://localhost:8080") as db:
        assert hasattr(db, "entities")
        assert hasattr(db, "hyperedges")
        assert hasattr(db, "paths")
        assert hasattr(db, "search")
