"""Tests for Webhooks API."""

import pytest
from pytest_httpx import HTTPXMock

from hyperx import HyperX, NotFoundError


def test_create_webhook(client: HyperX, httpx_mock: HTTPXMock):
    """Test webhook creation with events."""
    httpx_mock.add_response(
        method="POST",
        url="http://localhost:8080/v1/webhooks",
        json={
            "id": "wh:test-uuid",
            "url": "https://myapp.com/hooks",
            "events": ["entity.created", "hyperedge.created"],
            "secret": None,
            "active": True,
            "created_at": "2026-01-17T00:00:00Z",
            "updated_at": "2026-01-17T00:00:00Z",
        },
    )

    webhook = client.webhooks.create(
        url="https://myapp.com/hooks",
        events=["entity.created", "hyperedge.created"],
    )

    assert webhook.id == "wh:test-uuid"
    assert webhook.url == "https://myapp.com/hooks"
    assert webhook.events == ["entity.created", "hyperedge.created"]
    assert webhook.active is True
    assert webhook.secret is None


def test_create_webhook_with_secret(client: HyperX, httpx_mock: HTTPXMock):
    """Test webhook creation with HMAC secret."""
    httpx_mock.add_response(
        method="POST",
        url="http://localhost:8080/v1/webhooks",
        json={
            "id": "wh:test-uuid",
            "url": "https://myapp.com/hooks",
            "events": ["entity.*"],
            "secret": "whsec_abc123",
            "active": True,
            "created_at": "2026-01-17T00:00:00Z",
            "updated_at": "2026-01-17T00:00:00Z",
        },
    )

    webhook = client.webhooks.create(
        url="https://myapp.com/hooks",
        events=["entity.*"],
        secret="whsec_abc123",
    )

    assert webhook.id == "wh:test-uuid"
    assert webhook.secret == "whsec_abc123"


def test_get_webhook(client: HyperX, httpx_mock: HTTPXMock):
    """Test webhook retrieval by ID."""
    httpx_mock.add_response(
        method="GET",
        url="http://localhost:8080/v1/webhooks/wh:test-uuid",
        json={
            "id": "wh:test-uuid",
            "url": "https://myapp.com/hooks",
            "events": ["*"],
            "secret": None,
            "active": True,
            "created_at": "2026-01-17T00:00:00Z",
            "updated_at": "2026-01-17T00:00:00Z",
        },
    )

    webhook = client.webhooks.get("wh:test-uuid")

    assert webhook.id == "wh:test-uuid"
    assert webhook.url == "https://myapp.com/hooks"


def test_list_webhooks(client: HyperX, httpx_mock: HTTPXMock):
    """Test listing all webhooks."""
    httpx_mock.add_response(
        method="GET",
        url="http://localhost:8080/v1/webhooks",
        json=[
            {
                "id": "wh:uuid-1",
                "url": "https://app1.com/hooks",
                "events": ["entity.created"],
                "secret": None,
                "active": True,
                "created_at": "2026-01-17T00:00:00Z",
                "updated_at": "2026-01-17T00:00:00Z",
            },
            {
                "id": "wh:uuid-2",
                "url": "https://app2.com/hooks",
                "events": ["hyperedge.*"],
                "secret": "whsec_xyz",
                "active": False,
                "created_at": "2026-01-17T00:00:00Z",
                "updated_at": "2026-01-17T00:00:00Z",
            },
        ],
    )

    webhooks = client.webhooks.list()

    assert len(webhooks) == 2
    assert webhooks[0].id == "wh:uuid-1"
    assert webhooks[0].active is True
    assert webhooks[1].id == "wh:uuid-2"
    assert webhooks[1].active is False


def test_update_webhook(client: HyperX, httpx_mock: HTTPXMock):
    """Test webhook update."""
    httpx_mock.add_response(
        method="PUT",
        url="http://localhost:8080/v1/webhooks/wh:test-uuid",
        json={
            "id": "wh:test-uuid",
            "url": "https://newurl.com/hooks",
            "events": ["entity.updated", "entity.deleted"],
            "secret": None,
            "active": False,
            "created_at": "2026-01-17T00:00:00Z",
            "updated_at": "2026-01-17T01:00:00Z",
        },
    )

    webhook = client.webhooks.update(
        "wh:test-uuid",
        url="https://newurl.com/hooks",
        events=["entity.updated", "entity.deleted"],
        active=False,
    )

    assert webhook.url == "https://newurl.com/hooks"
    assert webhook.events == ["entity.updated", "entity.deleted"]
    assert webhook.active is False


def test_delete_webhook(client: HyperX, httpx_mock: HTTPXMock):
    """Test webhook deletion."""
    httpx_mock.add_response(
        method="DELETE",
        url="http://localhost:8080/v1/webhooks/wh:test-uuid",
        json={"deleted": True},
    )

    result = client.webhooks.delete("wh:test-uuid")

    assert result is True


def test_get_webhook_not_found(client: HyperX, httpx_mock: HTTPXMock):
    """Test 404 handling when webhook is not found."""
    httpx_mock.add_response(
        method="GET",
        url="http://localhost:8080/v1/webhooks/wh:nonexistent",
        status_code=404,
        json={"message": "Webhook not found"},
    )

    with pytest.raises(NotFoundError) as exc_info:
        client.webhooks.get("wh:nonexistent")

    assert exc_info.value.status_code == 404
    assert "Webhook not found" in str(exc_info.value)


def test_get_deliveries(client: HyperX, httpx_mock: HTTPXMock):
    """Test getting webhook delivery history."""
    httpx_mock.add_response(
        method="GET",
        url="http://localhost:8080/v1/webhooks/wh:test-uuid/deliveries?limit=100",
        json=[
            {
                "id": "del:uuid-1",
                "webhook_id": "wh:test-uuid",
                "event_type": "entity.created",
                "payload": {"entity_id": "e:123", "name": "Test"},
                "status_code": 200,
                "response_body": '{"ok": true}',
                "delivered_at": "2026-01-17T00:00:00Z",
                "attempts": 1,
                "success": True,
            },
            {
                "id": "del:uuid-2",
                "webhook_id": "wh:test-uuid",
                "event_type": "entity.updated",
                "payload": {"entity_id": "e:123", "name": "Updated"},
                "status_code": 500,
                "response_body": "Internal Server Error",
                "delivered_at": None,
                "attempts": 3,
                "success": False,
            },
        ],
    )

    deliveries = client.webhooks.deliveries("wh:test-uuid")

    assert len(deliveries) == 2
    assert deliveries[0].id == "del:uuid-1"
    assert deliveries[0].success is True
    assert deliveries[0].status_code == 200
    assert deliveries[1].success is False
    assert deliveries[1].attempts == 3


def test_get_deliveries_with_limit(client: HyperX, httpx_mock: HTTPXMock):
    """Test getting webhook deliveries with custom limit."""
    httpx_mock.add_response(
        method="GET",
        url="http://localhost:8080/v1/webhooks/wh:test-uuid/deliveries?limit=10",
        json=[],
    )

    deliveries = client.webhooks.deliveries("wh:test-uuid", limit=10)

    assert deliveries == []


def test_test_webhook(client: HyperX, httpx_mock: HTTPXMock):
    """Test sending a test delivery to a webhook."""
    httpx_mock.add_response(
        method="POST",
        url="http://localhost:8080/v1/webhooks/wh:test-uuid/test",
        json={
            "id": "del:test-uuid",
            "webhook_id": "wh:test-uuid",
            "event_type": "test",
            "payload": {"message": "This is a test webhook delivery"},
            "status_code": 200,
            "response_body": '{"received": true}',
            "delivered_at": "2026-01-17T00:00:00Z",
            "attempts": 1,
            "success": True,
        },
    )

    delivery = client.webhooks.test("wh:test-uuid")

    assert delivery.id == "del:test-uuid"
    assert delivery.event_type == "test"
    assert delivery.success is True
