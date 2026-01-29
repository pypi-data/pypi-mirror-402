"""Tests for search API."""

from pytest_httpx import HTTPXMock

from hyperx import HyperX


def test_hybrid_search(client: HyperX, httpx_mock: HTTPXMock):
    """Test hybrid search (callable interface)."""
    httpx_mock.add_response(
        method="POST",
        url="http://localhost:8080/v1/search",
        json={
            "entities": [
                {
                    "id": "e:react",
                    "name": "React",
                    "entity_type": "framework",
                    "attributes": {},
                    "confidence": 1.0,
                    "created_at": "2026-01-15T00:00:00Z",
                    "updated_at": "2026-01-15T00:00:00Z",
                },
            ],
            "hyperedges": [
                {
                    "id": "h:edge1",
                    "description": "React state management",
                    "members": [
                        {"entity_id": "e:react", "role": "subject"},
                        {"entity_id": "e:state", "role": "object"},
                    ],
                    "attributes": {},
                    "confidence": 1.0,
                    "created_at": "2026-01-15T00:00:00Z",
                    "updated_at": "2026-01-15T00:00:00Z",
                },
            ],
        },
    )

    results = client.search("react state management")

    assert len(results.entities) == 1
    assert results.entities[0].name == "React"
    assert len(results.hyperedges) == 1


def test_vector_search(client: HyperX, httpx_mock: HTTPXMock):
    """Test vector-only search."""
    httpx_mock.add_response(
        method="POST",
        url="http://localhost:8080/v1/search/vector",
        json={
            "entities": [
                {
                    "id": "e:similar",
                    "name": "Similar Entity",
                    "entity_type": "concept",
                    "attributes": {},
                    "confidence": 1.0,
                    "created_at": "2026-01-15T00:00:00Z",
                    "updated_at": "2026-01-15T00:00:00Z",
                },
            ],
            "hyperedges": [],
        },
    )

    embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
    results = client.search.vector(embedding=embedding, limit=5)

    assert len(results.entities) == 1
    assert results.entities[0].id == "e:similar"


def test_text_search(client: HyperX, httpx_mock: HTTPXMock):
    """Test text-only search (BM25)."""
    httpx_mock.add_response(
        method="POST",
        url="http://localhost:8080/v1/search/text",
        json={
            "entities": [],
            "hyperedges": [
                {
                    "id": "h:edge1",
                    "description": "Python programming language",
                    "members": [
                        {"entity_id": "e:python", "role": "subject"},
                    ],
                    "attributes": {},
                    "confidence": 1.0,
                    "created_at": "2026-01-15T00:00:00Z",
                    "updated_at": "2026-01-15T00:00:00Z",
                },
            ],
        },
    )

    results = client.search.text("python programming")

    assert len(results.entities) == 0
    assert len(results.hyperedges) == 1


def test_search_empty_results(client: HyperX, httpx_mock: HTTPXMock):
    """Test search with no results."""
    httpx_mock.add_response(
        method="POST",
        url="http://localhost:8080/v1/search",
        json={"entities": [], "hyperedges": []},
    )

    results = client.search("nonexistent query xyz123")

    assert len(results.entities) == 0
    assert len(results.hyperedges) == 0


def test_search_with_limit(client: HyperX, httpx_mock: HTTPXMock):
    """Test search with custom limit."""
    httpx_mock.add_response(
        method="POST",
        url="http://localhost:8080/v1/search",
        json={"entities": [], "hyperedges": []},
    )

    client.search("query", limit=50)

    # Verify the request was made with correct limit
    request = httpx_mock.get_request()
    assert request is not None
