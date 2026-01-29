"""Tests for Triggers API."""

import pytest
from pytest_httpx import HTTPXMock

from hyperx import HyperX, NotFoundError


def test_create_trigger_with_webhook_action(client: HyperX, httpx_mock: HTTPXMock):
    """Test trigger creation with webhook action."""
    httpx_mock.add_response(
        method="POST",
        url="http://localhost:8080/v1/triggers",
        json={
            "id": "tr:test-uuid",
            "name": "high_confidence_path",
            "condition": "path.cost < 0.5 AND path.hops <= 2",
            "event_types": ["path.discovered"],
            "action": "webhook",
            "webhook_id": "wh:123",
            "active": True,
            "created_at": "2026-01-17T00:00:00Z",
            "updated_at": "2026-01-17T00:00:00Z",
        },
    )

    trigger = client.triggers.create(
        name="high_confidence_path",
        condition="path.cost < 0.5 AND path.hops <= 2",
        event_types=["path.discovered"],
        action="webhook",
        webhook_id="wh:123",
    )

    assert trigger.id == "tr:test-uuid"
    assert trigger.name == "high_confidence_path"
    assert trigger.condition == "path.cost < 0.5 AND path.hops <= 2"
    assert trigger.event_types == ["path.discovered"]
    assert trigger.action == "webhook"
    assert trigger.webhook_id == "wh:123"
    assert trigger.active is True


def test_create_trigger_with_notification_action(client: HyperX, httpx_mock: HTTPXMock):
    """Test trigger creation with notification action."""
    httpx_mock.add_response(
        method="POST",
        url="http://localhost:8080/v1/triggers",
        json={
            "id": "tr:test-uuid-2",
            "name": "entity_created_alert",
            "condition": "entity.type == 'critical'",
            "event_types": ["entity.created"],
            "action": "notification",
            "webhook_id": None,
            "active": True,
            "created_at": "2026-01-17T00:00:00Z",
            "updated_at": "2026-01-17T00:00:00Z",
        },
    )

    trigger = client.triggers.create(
        name="entity_created_alert",
        condition="entity.type == 'critical'",
        event_types=["entity.created"],
        action="notification",
    )

    assert trigger.id == "tr:test-uuid-2"
    assert trigger.name == "entity_created_alert"
    assert trigger.action == "notification"
    assert trigger.webhook_id is None


def test_get_trigger(client: HyperX, httpx_mock: HTTPXMock):
    """Test trigger retrieval by ID."""
    httpx_mock.add_response(
        method="GET",
        url="http://localhost:8080/v1/triggers/tr:test-uuid",
        json={
            "id": "tr:test-uuid",
            "name": "high_confidence_path",
            "condition": "path.cost < 0.5",
            "event_types": ["path.discovered"],
            "action": "webhook",
            "webhook_id": "wh:123",
            "active": True,
            "created_at": "2026-01-17T00:00:00Z",
            "updated_at": "2026-01-17T00:00:00Z",
        },
    )

    trigger = client.triggers.get("tr:test-uuid")

    assert trigger.id == "tr:test-uuid"
    assert trigger.name == "high_confidence_path"


def test_list_triggers(client: HyperX, httpx_mock: HTTPXMock):
    """Test listing all triggers."""
    httpx_mock.add_response(
        method="GET",
        url="http://localhost:8080/v1/triggers",
        json=[
            {
                "id": "tr:uuid-1",
                "name": "trigger_one",
                "condition": "path.cost < 0.5",
                "event_types": ["path.discovered"],
                "action": "webhook",
                "webhook_id": "wh:123",
                "active": True,
                "created_at": "2026-01-17T00:00:00Z",
                "updated_at": "2026-01-17T00:00:00Z",
            },
            {
                "id": "tr:uuid-2",
                "name": "trigger_two",
                "condition": "entity.type == 'important'",
                "event_types": ["entity.created", "entity.updated"],
                "action": "notification",
                "webhook_id": None,
                "active": False,
                "created_at": "2026-01-17T00:00:00Z",
                "updated_at": "2026-01-17T00:00:00Z",
            },
        ],
    )

    triggers = client.triggers.list()

    assert len(triggers) == 2
    assert triggers[0].id == "tr:uuid-1"
    assert triggers[0].name == "trigger_one"
    assert triggers[0].active is True
    assert triggers[1].id == "tr:uuid-2"
    assert triggers[1].name == "trigger_two"
    assert triggers[1].active is False


def test_update_trigger(client: HyperX, httpx_mock: HTTPXMock):
    """Test trigger update."""
    httpx_mock.add_response(
        method="PUT",
        url="http://localhost:8080/v1/triggers/tr:test-uuid",
        json={
            "id": "tr:test-uuid",
            "name": "updated_trigger",
            "condition": "path.cost < 0.3 AND path.hops <= 3",
            "event_types": ["path.discovered", "path.updated"],
            "action": "webhook",
            "webhook_id": "wh:123",
            "active": False,
            "created_at": "2026-01-17T00:00:00Z",
            "updated_at": "2026-01-17T01:00:00Z",
        },
    )

    trigger = client.triggers.update(
        "tr:test-uuid",
        name="updated_trigger",
        condition="path.cost < 0.3 AND path.hops <= 3",
        event_types=["path.discovered", "path.updated"],
        active=False,
    )

    assert trigger.name == "updated_trigger"
    assert trigger.condition == "path.cost < 0.3 AND path.hops <= 3"
    assert trigger.event_types == ["path.discovered", "path.updated"]
    assert trigger.active is False


def test_delete_trigger(client: HyperX, httpx_mock: HTTPXMock):
    """Test trigger deletion."""
    httpx_mock.add_response(
        method="DELETE",
        url="http://localhost:8080/v1/triggers/tr:test-uuid",
        json={"deleted": True},
    )

    result = client.triggers.delete("tr:test-uuid")

    assert result is True


def test_get_trigger_not_found(client: HyperX, httpx_mock: HTTPXMock):
    """Test 404 handling when trigger is not found."""
    httpx_mock.add_response(
        method="GET",
        url="http://localhost:8080/v1/triggers/tr:nonexistent",
        status_code=404,
        json={"message": "Trigger not found"},
    )

    with pytest.raises(NotFoundError) as exc_info:
        client.triggers.get("tr:nonexistent")

    assert exc_info.value.status_code == 404
    assert "Trigger not found" in str(exc_info.value)


def test_test_trigger_matched(client: HyperX, httpx_mock: HTTPXMock):
    """Test testing a trigger against sample event data - matched case."""
    httpx_mock.add_response(
        method="POST",
        url="http://localhost:8080/v1/triggers/tr:test-uuid/test",
        json={
            "matched": True,
            "evaluation": "path.cost (0.3) < 0.5 AND path.hops (2) <= 2 -> True",
        },
    )

    result = client.triggers.test(
        "tr:test-uuid",
        event_data={
            "path": {
                "cost": 0.3,
                "hops": 2,
            },
        },
    )

    assert result["matched"] is True
    assert "True" in result["evaluation"]


def test_test_trigger_not_matched(client: HyperX, httpx_mock: HTTPXMock):
    """Test testing a trigger against sample event data - not matched case."""
    httpx_mock.add_response(
        method="POST",
        url="http://localhost:8080/v1/triggers/tr:test-uuid/test",
        json={
            "matched": False,
            "evaluation": "path.cost (0.8) < 0.5 -> False",
        },
    )

    result = client.triggers.test(
        "tr:test-uuid",
        event_data={
            "path": {
                "cost": 0.8,
                "hops": 1,
            },
        },
    )

    assert result["matched"] is False
    assert "False" in result["evaluation"]


def test_create_trigger_with_multiple_event_types(client: HyperX, httpx_mock: HTTPXMock):
    """Test trigger creation with multiple event types."""
    httpx_mock.add_response(
        method="POST",
        url="http://localhost:8080/v1/triggers",
        json={
            "id": "tr:multi-event",
            "name": "multi_event_trigger",
            "condition": "entity.type != 'internal'",
            "event_types": ["entity.created", "entity.updated", "entity.deleted"],
            "action": "notification",
            "webhook_id": None,
            "active": True,
            "created_at": "2026-01-17T00:00:00Z",
            "updated_at": "2026-01-17T00:00:00Z",
        },
    )

    trigger = client.triggers.create(
        name="multi_event_trigger",
        condition="entity.type != 'internal'",
        event_types=["entity.created", "entity.updated", "entity.deleted"],
        action="notification",
    )

    assert trigger.id == "tr:multi-event"
    assert len(trigger.event_types) == 3
    assert "entity.created" in trigger.event_types
    assert "entity.updated" in trigger.event_types
    assert "entity.deleted" in trigger.event_types
