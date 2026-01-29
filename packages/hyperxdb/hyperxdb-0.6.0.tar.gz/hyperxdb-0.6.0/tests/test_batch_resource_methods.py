"""Tests for batch methods on entity and hyperedge resources."""

from __future__ import annotations

import json

import pytest
from pytest_httpx import HTTPXMock

from hyperx import HyperX


class TestEntitiesCreateMany:
    """Tests for EntitiesAPI.create_many method."""

    def test_create_many_basic(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test creating multiple entities in a single request."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/entities/batch",
            json={
                "entities": [
                    {
                        "id": "e:uuid-1",
                        "name": "React",
                        "entity_type": "library",
                        "attributes": {},
                        "confidence": 1.0,
                        "created_at": "2026-01-17T00:00:00Z",
                        "updated_at": "2026-01-17T00:00:00Z",
                    },
                    {
                        "id": "e:uuid-2",
                        "name": "Vue",
                        "entity_type": "library",
                        "attributes": {},
                        "confidence": 1.0,
                        "created_at": "2026-01-17T00:00:00Z",
                        "updated_at": "2026-01-17T00:00:00Z",
                    },
                    {
                        "id": "e:uuid-3",
                        "name": "Angular",
                        "entity_type": "library",
                        "attributes": {},
                        "confidence": 1.0,
                        "created_at": "2026-01-17T00:00:00Z",
                        "updated_at": "2026-01-17T00:00:00Z",
                    },
                ]
            },
        )

        entities = client.entities.create_many([
            {"name": "React", "entity_type": "library"},
            {"name": "Vue", "entity_type": "library"},
            {"name": "Angular", "entity_type": "library"},
        ])

        assert len(entities) == 3
        assert entities[0].name == "React"
        assert entities[1].name == "Vue"
        assert entities[2].name == "Angular"

    def test_create_many_with_attributes(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test create_many with entity attributes."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/entities/batch",
            json={
                "entities": [
                    {
                        "id": "e:uuid-1",
                        "name": "React",
                        "entity_type": "library",
                        "attributes": {"version": "18.2", "language": "JavaScript"},
                        "confidence": 1.0,
                        "created_at": "2026-01-17T00:00:00Z",
                        "updated_at": "2026-01-17T00:00:00Z",
                    },
                ]
            },
        )

        entities = client.entities.create_many([
            {
                "name": "React",
                "entity_type": "library",
                "attributes": {"version": "18.2", "language": "JavaScript"},
            },
        ])

        assert len(entities) == 1
        assert entities[0].attributes == {"version": "18.2", "language": "JavaScript"}

    def test_create_many_atomic_default(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test that atomic=True by default."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/entities/batch",
            json={"entities": []},
        )

        client.entities.create_many([{"name": "Test", "entity_type": "concept"}])

        request = httpx_mock.get_request()
        assert request is not None
        body = json.loads(request.content)
        assert body["atomic"] is True

    def test_create_many_atomic_explicit_true(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test explicitly setting atomic=True."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/entities/batch",
            json={"entities": []},
        )

        client.entities.create_many(
            [{"name": "Test", "entity_type": "concept"}],
            atomic=True,
        )

        request = httpx_mock.get_request()
        assert request is not None
        body = json.loads(request.content)
        assert body["atomic"] is True

    def test_create_many_atomic_false_best_effort(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test atomic=False for best-effort mode."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/entities/batch",
            json={
                "entities": [
                    {
                        "id": "e:uuid-1",
                        "name": "Valid",
                        "entity_type": "concept",
                        "attributes": {},
                        "confidence": 1.0,
                        "created_at": "2026-01-17T00:00:00Z",
                        "updated_at": "2026-01-17T00:00:00Z",
                    },
                ]
            },
        )

        entities = client.entities.create_many(
            [
                {"name": "Valid", "entity_type": "concept"},
                {"name": "Invalid", "entity_type": "bad_type"},
            ],
            atomic=False,
        )

        request = httpx_mock.get_request()
        assert request is not None
        body = json.loads(request.content)
        assert body["atomic"] is False

    def test_create_many_with_embedding(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test create_many with embeddings."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/entities/batch",
            json={
                "entities": [
                    {
                        "id": "e:uuid-1",
                        "name": "Test",
                        "entity_type": "concept",
                        "attributes": {},
                        "confidence": 1.0,
                        "created_at": "2026-01-17T00:00:00Z",
                        "updated_at": "2026-01-17T00:00:00Z",
                    },
                ]
            },
        )

        embedding = [0.1, 0.2, 0.3, 0.4]
        client.entities.create_many([
            {"name": "Test", "entity_type": "concept", "embedding": embedding},
        ])

        request = httpx_mock.get_request()
        assert request is not None
        body = json.loads(request.content)
        assert body["entities"][0]["embedding"] == embedding


class TestEntitiesDeleteMany:
    """Tests for EntitiesAPI.delete_many method."""

    def test_delete_many_basic(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test deleting multiple entities."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/entities/batch/delete",
            json={"deleted": 3},
        )

        deleted_count = client.entities.delete_many([
            "e:uuid-1",
            "e:uuid-2",
            "e:uuid-3",
        ])

        assert deleted_count == 3

    def test_delete_many_atomic_default(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test that delete_many uses atomic=True by default."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/entities/batch/delete",
            json={"deleted": 1},
        )

        client.entities.delete_many(["e:uuid-1"])

        request = httpx_mock.get_request()
        assert request is not None
        body = json.loads(request.content)
        assert body["atomic"] is True
        assert body["ids"] == ["e:uuid-1"]

    def test_delete_many_atomic_false(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test delete_many with atomic=False."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/entities/batch/delete",
            json={"deleted": 2},
        )

        deleted_count = client.entities.delete_many(
            ["e:uuid-1", "e:uuid-2", "e:nonexistent"],
            atomic=False,
        )

        request = httpx_mock.get_request()
        assert request is not None
        body = json.loads(request.content)
        assert body["atomic"] is False
        assert deleted_count == 2


class TestHyperedgesCreateMany:
    """Tests for HyperedgesAPI.create_many method."""

    def test_create_many_basic(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test creating multiple hyperedges in a single request."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/hyperedges/batch",
            json={
                "hyperedges": [
                    {
                        "id": "h:uuid-1",
                        "description": "React uses Hooks",
                        "members": [
                            {"entity_id": "e:react", "role": "subject"},
                            {"entity_id": "e:hooks", "role": "object"},
                        ],
                        "attributes": {},
                        "confidence": 1.0,
                        "created_at": "2026-01-17T00:00:00Z",
                        "updated_at": "2026-01-17T00:00:00Z",
                    },
                    {
                        "id": "h:uuid-2",
                        "description": "Vue uses Composition API",
                        "members": [
                            {"entity_id": "e:vue", "role": "subject"},
                            {"entity_id": "e:composition-api", "role": "object"},
                        ],
                        "attributes": {},
                        "confidence": 1.0,
                        "created_at": "2026-01-17T00:00:00Z",
                        "updated_at": "2026-01-17T00:00:00Z",
                    },
                ]
            },
        )

        hyperedges = client.hyperedges.create_many([
            {
                "description": "React uses Hooks",
                "members": [
                    {"entity_id": "e:react", "role": "subject"},
                    {"entity_id": "e:hooks", "role": "object"},
                ],
            },
            {
                "description": "Vue uses Composition API",
                "members": [
                    {"entity_id": "e:vue", "role": "subject"},
                    {"entity_id": "e:composition-api", "role": "object"},
                ],
            },
        ])

        assert len(hyperedges) == 2
        assert hyperedges[0].description == "React uses Hooks"
        assert hyperedges[1].description == "Vue uses Composition API"

    def test_create_many_with_attributes(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test create_many with hyperedge attributes."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/hyperedges/batch",
            json={
                "hyperedges": [
                    {
                        "id": "h:uuid-1",
                        "description": "React uses Hooks",
                        "members": [
                            {"entity_id": "e:react", "role": "subject"},
                            {"entity_id": "e:hooks", "role": "object"},
                        ],
                        "attributes": {"since": "16.8", "type": "feature"},
                        "confidence": 1.0,
                        "created_at": "2026-01-17T00:00:00Z",
                        "updated_at": "2026-01-17T00:00:00Z",
                    },
                ]
            },
        )

        hyperedges = client.hyperedges.create_many([
            {
                "description": "React uses Hooks",
                "members": [
                    {"entity_id": "e:react", "role": "subject"},
                    {"entity_id": "e:hooks", "role": "object"},
                ],
                "attributes": {"since": "16.8", "type": "feature"},
            },
        ])

        assert len(hyperedges) == 1
        assert hyperedges[0].attributes == {"since": "16.8", "type": "feature"}

    def test_create_many_atomic_default(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test that atomic=True by default."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/hyperedges/batch",
            json={"hyperedges": []},
        )

        client.hyperedges.create_many([
            {
                "description": "Test relation",
                "members": [
                    {"entity_id": "e:a", "role": "subject"},
                    {"entity_id": "e:b", "role": "object"},
                ],
            },
        ])

        request = httpx_mock.get_request()
        assert request is not None
        body = json.loads(request.content)
        assert body["atomic"] is True

    def test_create_many_atomic_false(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test atomic=False for best-effort mode."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/hyperedges/batch",
            json={"hyperedges": []},
        )

        client.hyperedges.create_many(
            [
                {
                    "description": "Test relation",
                    "members": [
                        {"entity_id": "e:a", "role": "subject"},
                        {"entity_id": "e:b", "role": "object"},
                    ],
                },
            ],
            atomic=False,
        )

        request = httpx_mock.get_request()
        assert request is not None
        body = json.loads(request.content)
        assert body["atomic"] is False


class TestHyperedgesDeleteMany:
    """Tests for HyperedgesAPI.delete_many method."""

    def test_delete_many_basic(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test deleting multiple hyperedges."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/hyperedges/batch/delete",
            json={"deleted": 2},
        )

        deleted_count = client.hyperedges.delete_many([
            "h:uuid-1",
            "h:uuid-2",
        ])

        assert deleted_count == 2

    def test_delete_many_atomic_default(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test that delete_many uses atomic=True by default."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/hyperedges/batch/delete",
            json={"deleted": 1},
        )

        client.hyperedges.delete_many(["h:uuid-1"])

        request = httpx_mock.get_request()
        assert request is not None
        body = json.loads(request.content)
        assert body["atomic"] is True
        assert body["ids"] == ["h:uuid-1"]

    def test_delete_many_atomic_false(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test delete_many with atomic=False."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/hyperedges/batch/delete",
            json={"deleted": 1},
        )

        deleted_count = client.hyperedges.delete_many(
            ["h:uuid-1", "h:nonexistent"],
            atomic=False,
        )

        request = httpx_mock.get_request()
        assert request is not None
        body = json.loads(request.content)
        assert body["atomic"] is False
        assert deleted_count == 1


class TestAsyncEntitiesCreateMany:
    """Tests for AsyncEntitiesAPI.create_many method."""

    @pytest.mark.asyncio
    async def test_create_many_basic(self, httpx_mock: HTTPXMock):
        """Test async create_many for entities."""
        from hyperx import AsyncHyperX

        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/entities/batch",
            json={
                "entities": [
                    {
                        "id": "e:uuid-1",
                        "name": "React",
                        "entity_type": "library",
                        "attributes": {},
                        "confidence": 1.0,
                        "created_at": "2026-01-17T00:00:00Z",
                        "updated_at": "2026-01-17T00:00:00Z",
                    },
                    {
                        "id": "e:uuid-2",
                        "name": "Vue",
                        "entity_type": "library",
                        "attributes": {},
                        "confidence": 1.0,
                        "created_at": "2026-01-17T00:00:00Z",
                        "updated_at": "2026-01-17T00:00:00Z",
                    },
                ]
            },
        )

        async with AsyncHyperX(
            api_key="hx_sk_test_12345678",
            base_url="http://localhost:8080",
        ) as client:
            entities = await client.entities.create_many([
                {"name": "React", "entity_type": "library"},
                {"name": "Vue", "entity_type": "library"},
            ])

        assert len(entities) == 2
        assert entities[0].name == "React"
        assert entities[1].name == "Vue"


class TestAsyncEntitiesDeleteMany:
    """Tests for AsyncEntitiesAPI.delete_many method."""

    @pytest.mark.asyncio
    async def test_delete_many_basic(self, httpx_mock: HTTPXMock):
        """Test async delete_many for entities."""
        from hyperx import AsyncHyperX

        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/entities/batch/delete",
            json={"deleted": 2},
        )

        async with AsyncHyperX(
            api_key="hx_sk_test_12345678",
            base_url="http://localhost:8080",
        ) as client:
            deleted_count = await client.entities.delete_many([
                "e:uuid-1",
                "e:uuid-2",
            ])

        assert deleted_count == 2


class TestAsyncHyperedgesCreateMany:
    """Tests for AsyncHyperedgesAPI.create_many method."""

    @pytest.mark.asyncio
    async def test_create_many_basic(self, httpx_mock: HTTPXMock):
        """Test async create_many for hyperedges."""
        from hyperx import AsyncHyperX

        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/hyperedges/batch",
            json={
                "hyperedges": [
                    {
                        "id": "h:uuid-1",
                        "description": "React uses Hooks",
                        "members": [
                            {"entity_id": "e:react", "role": "subject"},
                            {"entity_id": "e:hooks", "role": "object"},
                        ],
                        "attributes": {},
                        "confidence": 1.0,
                        "created_at": "2026-01-17T00:00:00Z",
                        "updated_at": "2026-01-17T00:00:00Z",
                    },
                ]
            },
        )

        async with AsyncHyperX(
            api_key="hx_sk_test_12345678",
            base_url="http://localhost:8080",
        ) as client:
            hyperedges = await client.hyperedges.create_many([
                {
                    "description": "React uses Hooks",
                    "members": [
                        {"entity_id": "e:react", "role": "subject"},
                        {"entity_id": "e:hooks", "role": "object"},
                    ],
                },
            ])

        assert len(hyperedges) == 1
        assert hyperedges[0].description == "React uses Hooks"


class TestAsyncHyperedgesDeleteMany:
    """Tests for AsyncHyperedgesAPI.delete_many method."""

    @pytest.mark.asyncio
    async def test_delete_many_basic(self, httpx_mock: HTTPXMock):
        """Test async delete_many for hyperedges."""
        from hyperx import AsyncHyperX

        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/hyperedges/batch/delete",
            json={"deleted": 2},
        )

        async with AsyncHyperX(
            api_key="hx_sk_test_12345678",
            base_url="http://localhost:8080",
        ) as client:
            deleted_count = await client.hyperedges.delete_many([
                "h:uuid-1",
                "h:uuid-2",
            ])

        assert deleted_count == 2
