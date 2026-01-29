"""Shared test fixtures for HyperX SDK tests."""

import pytest

from hyperx import HyperX

# Test constants
TEST_API_KEY = "hx_sk_test_12345678"
TEST_BASE_URL = "http://localhost:8080"


@pytest.fixture
def client() -> HyperX:
    """Properly scoped client with cleanup.

    Yields a HyperX client configured for testing, then ensures
    proper cleanup of resources when the test completes.
    """
    c = HyperX(api_key=TEST_API_KEY, base_url=TEST_BASE_URL)
    yield c
    c.close()
