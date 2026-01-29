"""Tests for entities API."""

import pytest
from pytest_httpx import HTTPXMock

from hyperx import AuthenticationError, HyperX, NotFoundError, ValidationError


def test_create_entity(client: HyperX, httpx_mock: HTTPXMock):
    """Test entity creation."""
    httpx_mock.add_response(
        method="POST",
        url="http://localhost:8080/v1/entities",
        json={
            "id": "e:test-uuid",
            "name": "Test Entity",
            "entity_type": "concept",
            "attributes": {},
            "confidence": 1.0,
            "created_at": "2026-01-15T00:00:00Z",
            "updated_at": "2026-01-15T00:00:00Z",
        },
    )

    entity = client.entities.create(name="Test Entity", entity_type="concept")

    assert entity.id == "e:test-uuid"
    assert entity.name == "Test Entity"
    assert entity.entity_type == "concept"


def test_get_entity(client: HyperX, httpx_mock: HTTPXMock):
    """Test entity retrieval."""
    httpx_mock.add_response(
        method="GET",
        url="http://localhost:8080/v1/entities/e:test-uuid",
        json={
            "id": "e:test-uuid",
            "name": "Test Entity",
            "entity_type": "concept",
            "attributes": {},
            "confidence": 1.0,
            "created_at": "2026-01-15T00:00:00Z",
            "updated_at": "2026-01-15T00:00:00Z",
        },
    )

    entity = client.entities.get("e:test-uuid")

    assert entity.id == "e:test-uuid"


def test_delete_entity(client: HyperX, httpx_mock: HTTPXMock):
    """Test entity deletion."""
    httpx_mock.add_response(
        method="DELETE",
        url="http://localhost:8080/v1/entities/e:test-uuid",
        json={"deleted": True},
    )

    result = client.entities.delete("e:test-uuid")

    assert result is True


def test_update_entity(client: HyperX, httpx_mock: HTTPXMock):
    """Test entity update."""
    httpx_mock.add_response(
        method="PUT",
        url="http://localhost:8080/v1/entities/e:test-uuid",
        json={
            "id": "e:test-uuid",
            "name": "Updated Entity",
            "entity_type": "concept",
            "attributes": {"version": 2},
            "confidence": 1.0,
            "created_at": "2026-01-15T00:00:00Z",
            "updated_at": "2026-01-15T00:00:00Z",
        },
    )

    entity = client.entities.update(
        "e:test-uuid",
        name="Updated Entity",
        attributes={"version": 2},
    )

    assert entity.name == "Updated Entity"
    assert entity.attributes == {"version": 2}


def test_list_entities(client: HyperX, httpx_mock: HTTPXMock):
    """Test listing entities."""
    httpx_mock.add_response(
        method="GET",
        url="http://localhost:8080/v1/entities?limit=10&offset=0",
        json=[
            {
                "id": "e:uuid-1",
                "name": "Entity 1",
                "entity_type": "concept",
                "attributes": {},
                "confidence": 1.0,
                "created_at": "2026-01-15T00:00:00Z",
                "updated_at": "2026-01-15T00:00:00Z",
            },
            {
                "id": "e:uuid-2",
                "name": "Entity 2",
                "entity_type": "person",
                "attributes": {},
                "confidence": 1.0,
                "created_at": "2026-01-15T00:00:00Z",
                "updated_at": "2026-01-15T00:00:00Z",
            },
        ],
    )

    entities = client.entities.list(limit=10, offset=0)

    assert len(entities) == 2
    assert entities[0].name == "Entity 1"
    assert entities[1].entity_type == "person"


def test_create_entity_with_attributes(client: HyperX, httpx_mock: HTTPXMock):
    """Test entity creation with custom attributes."""
    httpx_mock.add_response(
        method="POST",
        url="http://localhost:8080/v1/entities",
        json={
            "id": "e:test-uuid",
            "name": "React",
            "entity_type": "framework",
            "attributes": {"language": "JavaScript", "version": "18.2"},
            "confidence": 1.0,
            "created_at": "2026-01-15T00:00:00Z",
            "updated_at": "2026-01-15T00:00:00Z",
        },
    )

    entity = client.entities.create(
        name="React",
        entity_type="framework",
        attributes={"language": "JavaScript", "version": "18.2"},
    )

    assert entity.attributes["language"] == "JavaScript"
    assert entity.attributes["version"] == "18.2"


# Error case tests


def test_get_entity_not_found(client: HyperX, httpx_mock: HTTPXMock):
    """Test 404 handling when entity is not found."""
    httpx_mock.add_response(
        method="GET",
        url="http://localhost:8080/v1/entities/e:nonexistent",
        status_code=404,
        json={"message": "Entity not found"},
    )

    with pytest.raises(NotFoundError) as exc_info:
        client.entities.get("e:nonexistent")

    assert exc_info.value.status_code == 404
    assert "Entity not found" in str(exc_info.value)


def test_create_entity_validation_error(client: HyperX, httpx_mock: HTTPXMock):
    """Test 400 handling when validation fails."""
    httpx_mock.add_response(
        method="POST",
        url="http://localhost:8080/v1/entities",
        status_code=400,
        json={"message": "Invalid entity_type: must be one of [concept, person, organization]"},
    )

    with pytest.raises(ValidationError) as exc_info:
        client.entities.create(name="Test", entity_type="invalid_type")

    assert exc_info.value.status_code == 400
    assert "Invalid entity_type" in str(exc_info.value)


def test_authentication_error(httpx_mock: HTTPXMock):
    """Test 401 handling when API key is invalid."""
    httpx_mock.add_response(
        method="GET",
        url="http://localhost:8080/v1/entities/e:test",
        status_code=401,
        json={"message": "Invalid API key"},
    )

    # Create a client with a test API key (it will be mocked anyway)
    client = HyperX(api_key="hx_sk_invalid_key", base_url="http://localhost:8080")
    try:
        with pytest.raises(AuthenticationError) as exc_info:
            client.entities.get("e:test")

        assert exc_info.value.status_code == 401
        assert "Invalid API key" in str(exc_info.value)
    finally:
        client.close()
