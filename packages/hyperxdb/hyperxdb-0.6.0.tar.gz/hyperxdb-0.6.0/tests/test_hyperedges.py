"""Tests for hyperedges API."""

from pytest_httpx import HTTPXMock

from hyperx import HyperX, MemberInput


def test_create_hyperedge(client: HyperX, httpx_mock: HTTPXMock):
    """Test hyperedge creation."""
    httpx_mock.add_response(
        method="POST",
        url="http://localhost:8080/v1/hyperedges",
        json={
            "id": "h:test-uuid",
            "description": "React provides Hooks",
            "members": [
                {"entity_id": "e:react", "role": "subject"},
                {"entity_id": "e:hooks", "role": "object"},
            ],
            "attributes": {},
            "confidence": 1.0,
            "created_at": "2026-01-15T00:00:00Z",
            "updated_at": "2026-01-15T00:00:00Z",
        },
    )

    edge = client.hyperedges.create(
        description="React provides Hooks",
        members=[
            {"entity_id": "e:react", "role": "subject"},
            {"entity_id": "e:hooks", "role": "object"},
        ],
    )

    assert edge.id == "h:test-uuid"
    assert edge.description == "React provides Hooks"
    assert len(edge.members) == 2


def test_create_hyperedge_with_member_input(client: HyperX, httpx_mock: HTTPXMock):
    """Test hyperedge creation using MemberInput helper."""
    httpx_mock.add_response(
        method="POST",
        url="http://localhost:8080/v1/hyperedges",
        json={
            "id": "h:test-uuid",
            "description": "React provides Hooks",
            "members": [
                {"entity_id": "e:react", "role": "subject"},
                {"entity_id": "e:hooks", "role": "object"},
            ],
            "attributes": {},
            "confidence": 1.0,
            "created_at": "2026-01-15T00:00:00Z",
            "updated_at": "2026-01-15T00:00:00Z",
        },
    )

    edge = client.hyperedges.create(
        description="React provides Hooks",
        members=[
            MemberInput("e:react", "subject"),
            MemberInput("e:hooks", "object"),
        ],
    )

    assert edge.id == "h:test-uuid"


def test_get_hyperedge(client: HyperX, httpx_mock: HTTPXMock):
    """Test hyperedge retrieval."""
    httpx_mock.add_response(
        method="GET",
        url="http://localhost:8080/v1/hyperedges/h:test-uuid",
        json={
            "id": "h:test-uuid",
            "description": "React provides Hooks",
            "members": [
                {"entity_id": "e:react", "role": "subject"},
                {"entity_id": "e:hooks", "role": "object"},
            ],
            "attributes": {},
            "confidence": 1.0,
            "created_at": "2026-01-15T00:00:00Z",
            "updated_at": "2026-01-15T00:00:00Z",
        },
    )

    edge = client.hyperedges.get("h:test-uuid")

    assert edge.id == "h:test-uuid"
    assert edge.members[0].role == "subject"


def test_delete_hyperedge(client: HyperX, httpx_mock: HTTPXMock):
    """Test hyperedge deletion."""
    httpx_mock.add_response(
        method="DELETE",
        url="http://localhost:8080/v1/hyperedges/h:test-uuid",
        json={"deleted": True},
    )

    result = client.hyperedges.delete("h:test-uuid")

    assert result is True


def test_list_hyperedges(client: HyperX, httpx_mock: HTTPXMock):
    """Test listing hyperedges."""
    httpx_mock.add_response(
        method="GET",
        url="http://localhost:8080/v1/hyperedges?limit=100&offset=0",
        json=[
            {
                "id": "h:uuid-1",
                "description": "Edge 1",
                "members": [
                    {"entity_id": "e:a", "role": "subject"},
                    {"entity_id": "e:b", "role": "object"},
                ],
                "attributes": {},
                "confidence": 1.0,
                "created_at": "2026-01-15T00:00:00Z",
                "updated_at": "2026-01-15T00:00:00Z",
            },
        ],
    )

    edges = client.hyperedges.list()

    assert len(edges) == 1
    assert edges[0].description == "Edge 1"


def test_member_input_to_dict():
    """Test MemberInput helper class."""
    member = MemberInput("e:test", "subject")

    assert member.to_dict() == {"entity_id": "e:test", "role": "subject"}
