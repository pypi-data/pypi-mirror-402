"""Tests for search role_filter parameter."""

import json

import pytest
from pytest_httpx import HTTPXMock

from hyperx import HyperX, AsyncHyperX


# Standard response data for reuse
SEARCH_RESPONSE = {
    "entities": [
        {
            "id": "e:react",
            "name": "React",
            "entity_type": "library",
            "attributes": {},
            "confidence": 1.0,
            "created_at": "2026-01-15T00:00:00Z",
            "updated_at": "2026-01-15T00:00:00Z",
        },
    ],
    "hyperedges": [
        {
            "id": "h:edge1",
            "description": "React provides state management",
            "members": [
                {"entity_id": "e:react", "role": "subject"},
                {"entity_id": "e:state-mgmt", "role": "object"},
            ],
            "attributes": {},
            "confidence": 1.0,
            "created_at": "2026-01-15T00:00:00Z",
            "updated_at": "2026-01-15T00:00:00Z",
        },
    ],
}


class TestSearchRoleFilter:
    """Tests for role_filter in hybrid search."""

    def test_search_with_single_role_filter(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test search with a single role filter."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/search",
            json=SEARCH_RESPONSE,
        )

        results = client.search(
            "state management",
            role_filter={"subject": "e:react"},
        )

        # Verify results
        assert len(results.entities) == 1
        assert results.entities[0].id == "e:react"

        # Verify request payload includes role_filter
        request = httpx_mock.get_request()
        assert request is not None
        payload = json.loads(request.content)
        assert payload["role_filter"] == {"subject": "e:react"}

    def test_search_with_multiple_role_filters(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test search with multiple role filters (AND condition)."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/search",
            json=SEARCH_RESPONSE,
        )

        results = client.search(
            "provides",
            role_filter={
                "subject": "e:react",
                "object": "e:state-mgmt",
            },
        )

        assert len(results.hyperedges) == 1

        # Verify request payload includes all filters
        request = httpx_mock.get_request()
        assert request is not None
        payload = json.loads(request.content)
        assert payload["role_filter"]["subject"] == "e:react"
        assert payload["role_filter"]["object"] == "e:state-mgmt"

    def test_search_with_role_type_filter(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test search with role + entity type filter."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/search",
            json=SEARCH_RESPONSE,
        )

        results = client.search(
            "provides",
            role_filter={
                "subject": "e:react",
                "object_type": "concept",
            },
        )

        assert len(results.entities) == 1

        # Verify type filter is passed
        request = httpx_mock.get_request()
        assert request is not None
        payload = json.loads(request.content)
        assert payload["role_filter"]["object_type"] == "concept"

    def test_search_without_role_filter(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test that None role_filter doesn't add to payload."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/search",
            json=SEARCH_RESPONSE,
        )

        client.search("state management", role_filter=None)

        # Verify role_filter not in payload
        request = httpx_mock.get_request()
        assert request is not None
        payload = json.loads(request.content)
        assert "role_filter" not in payload

    def test_search_default_no_role_filter(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test that default (no role_filter arg) doesn't add to payload."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/search",
            json=SEARCH_RESPONSE,
        )

        client.search("state management")

        # Verify role_filter not in payload
        request = httpx_mock.get_request()
        assert request is not None
        payload = json.loads(request.content)
        assert "role_filter" not in payload


class TestVectorSearchRoleFilter:
    """Tests for role_filter in vector search."""

    def test_vector_search_with_role_filter(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test vector search with role filter."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/search/vector",
            json=SEARCH_RESPONSE,
        )

        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        results = client.search.vector(
            embedding=embedding,
            role_filter={"subject": "e:react"},
        )

        assert len(results.entities) == 1

        # Verify request payload
        request = httpx_mock.get_request()
        assert request is not None
        payload = json.loads(request.content)
        assert payload["role_filter"] == {"subject": "e:react"}

    def test_vector_search_without_role_filter(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test vector search without role filter doesn't include it in payload."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/search/vector",
            json=SEARCH_RESPONSE,
        )

        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        client.search.vector(embedding=embedding)

        request = httpx_mock.get_request()
        assert request is not None
        payload = json.loads(request.content)
        assert "role_filter" not in payload


class TestTextSearchRoleFilter:
    """Tests for role_filter in text search."""

    def test_text_search_with_role_filter(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test text search with role filter."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/search/text",
            json=SEARCH_RESPONSE,
        )

        results = client.search.text(
            "state management",
            role_filter={"subject_type": "library"},
        )

        assert len(results.entities) == 1

        # Verify request payload
        request = httpx_mock.get_request()
        assert request is not None
        payload = json.loads(request.content)
        assert payload["role_filter"] == {"subject_type": "library"}

    def test_text_search_without_role_filter(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test text search without role filter doesn't include it in payload."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/search/text",
            json=SEARCH_RESPONSE,
        )

        client.search.text("state management")

        request = httpx_mock.get_request()
        assert request is not None
        payload = json.loads(request.content)
        assert "role_filter" not in payload


class TestAsyncSearchRoleFilter:
    """Tests for role_filter in async search methods."""

    @pytest.mark.asyncio
    async def test_async_search_with_role_filter(self, httpx_mock: HTTPXMock):
        """Test async hybrid search with role filter."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/search",
            json=SEARCH_RESPONSE,
        )

        async with AsyncHyperX(api_key="hx_sk_test", base_url="http://localhost:8080") as client:
            results = await client.search(
                "state management",
                role_filter={"subject": "e:react"},
            )

        assert len(results.entities) == 1

        request = httpx_mock.get_request()
        assert request is not None
        payload = json.loads(request.content)
        assert payload["role_filter"] == {"subject": "e:react"}

    @pytest.mark.asyncio
    async def test_async_vector_search_with_role_filter(self, httpx_mock: HTTPXMock):
        """Test async vector search with role filter."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/search/vector",
            json=SEARCH_RESPONSE,
        )

        async with AsyncHyperX(api_key="hx_sk_test", base_url="http://localhost:8080") as client:
            embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
            results = await client.search.vector(
                embedding=embedding,
                role_filter={"object_type": "concept"},
            )

        assert len(results.entities) == 1

        request = httpx_mock.get_request()
        assert request is not None
        payload = json.loads(request.content)
        assert payload["role_filter"] == {"object_type": "concept"}

    @pytest.mark.asyncio
    async def test_async_text_search_with_role_filter(self, httpx_mock: HTTPXMock):
        """Test async text search with role filter."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/search/text",
            json=SEARCH_RESPONSE,
        )

        async with AsyncHyperX(api_key="hx_sk_test", base_url="http://localhost:8080") as client:
            results = await client.search.text(
                "provides",
                role_filter={"subject": "e:react", "object": "e:state-mgmt"},
            )

        assert len(results.hyperedges) == 1

        request = httpx_mock.get_request()
        assert request is not None
        payload = json.loads(request.content)
        assert payload["role_filter"]["subject"] == "e:react"
        assert payload["role_filter"]["object"] == "e:state-mgmt"

    @pytest.mark.asyncio
    async def test_async_search_without_role_filter(self, httpx_mock: HTTPXMock):
        """Test async search without role filter doesn't include it in payload."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/search",
            json=SEARCH_RESPONSE,
        )

        async with AsyncHyperX(api_key="hx_sk_test", base_url="http://localhost:8080") as client:
            await client.search("state management")

        request = httpx_mock.get_request()
        assert request is not None
        payload = json.loads(request.content)
        assert "role_filter" not in payload
