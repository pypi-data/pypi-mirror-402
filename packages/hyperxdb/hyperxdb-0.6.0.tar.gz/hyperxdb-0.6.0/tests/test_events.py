"""Tests for event system and @db.on() decorator."""

from datetime import datetime
from unittest.mock import Mock

import pytest

from hyperx import HyperX
from hyperx.events import Event, EventHandler, EventRegistry, EventType


# Test constants
TEST_API_KEY = "hx_sk_test_12345678"
TEST_BASE_URL = "http://localhost:8080"


class TestEvent:
    """Tests for Event model."""

    def test_create_event_minimal(self):
        """Event can be created with required fields only."""
        event = Event(
            type="entity.created",
            data={"id": "e:123", "name": "Test"},
            timestamp=datetime.now(),
        )
        assert event.type == "entity.created"
        assert event.data["id"] == "e:123"
        assert event.metadata == {}

    def test_create_event_with_metadata(self):
        """Event can be created with optional metadata."""
        event = Event(
            type="hyperedge.created",
            data={"id": "he:456"},
            timestamp=datetime.now(),
            metadata={"source": "webhook", "version": 1},
        )
        assert event.metadata["source"] == "webhook"
        assert event.metadata["version"] == 1


class TestEventHandler:
    """Tests for EventHandler model."""

    def test_handler_exact_match(self):
        """Handler matches exact event types."""
        handler = EventHandler(
            pattern="entity.created",
            callback=lambda e: None,
        )
        assert handler.matches("entity.created") is True
        assert handler.matches("entity.updated") is False

    def test_handler_wildcard_match(self):
        """Handler matches wildcards in patterns."""
        handler = EventHandler(
            pattern="entity.*",
            callback=lambda e: None,
        )
        assert handler.matches("entity.created") is True
        assert handler.matches("entity.updated") is True
        assert handler.matches("entity.deleted") is True
        assert handler.matches("hyperedge.created") is False

    def test_handler_global_wildcard(self):
        """Handler with '*' matches all events."""
        handler = EventHandler(
            pattern="*",
            callback=lambda e: None,
        )
        assert handler.matches("entity.created") is True
        assert handler.matches("hyperedge.deleted") is True
        assert handler.matches("path.discovered") is True

    def test_handler_with_filter(self):
        """Handler can have optional filter."""
        handler = EventHandler(
            pattern="hyperedge.created",
            callback=lambda e: None,
            filter={"role": "author"},
        )
        assert handler.filter == {"role": "author"}


class TestEventRegistry:
    """Tests for EventRegistry."""

    def test_register_handler(self):
        """Registry can register handlers."""
        registry = EventRegistry()
        callback = Mock()

        handler = registry.register("entity.created", callback)

        assert handler in registry.handlers
        assert handler.pattern == "entity.created"
        assert handler.callback is callback

    def test_register_handler_with_filter(self):
        """Registry can register handlers with filters."""
        registry = EventRegistry()
        callback = Mock()

        handler = registry.register(
            "hyperedge.created",
            callback,
            filter={"role": "author"},
        )

        assert handler.filter == {"role": "author"}

    def test_unregister_handler(self):
        """Registry can unregister handlers."""
        registry = EventRegistry()
        callback = Mock()
        handler = registry.register("entity.created", callback)

        result = registry.unregister(handler)

        assert result is True
        assert handler not in registry.handlers

    def test_unregister_nonexistent_handler(self):
        """Unregistering nonexistent handler returns False."""
        registry = EventRegistry()
        handler = EventHandler(pattern="test", callback=lambda e: None)

        result = registry.unregister(handler)

        assert result is False

    def test_dispatch_calls_matching_handlers(self):
        """Dispatch calls handlers with matching patterns."""
        registry = EventRegistry()
        callback1 = Mock()
        callback2 = Mock()

        registry.register("entity.created", callback1)
        registry.register("entity.*", callback2)

        event = Event(
            type="entity.created",
            data={"id": "e:123"},
            timestamp=datetime.now(),
        )

        count = registry.dispatch(event)

        assert count == 2
        callback1.assert_called_once_with(event)
        callback2.assert_called_once_with(event)

    def test_dispatch_skips_non_matching_handlers(self):
        """Dispatch does not call non-matching handlers."""
        registry = EventRegistry()
        callback = Mock()

        registry.register("entity.created", callback)

        event = Event(
            type="hyperedge.created",
            data={"id": "he:123"},
            timestamp=datetime.now(),
        )

        count = registry.dispatch(event)

        assert count == 0
        callback.assert_not_called()

    def test_dispatch_with_role_filter_match(self):
        """Dispatch calls handler when role filter matches."""
        registry = EventRegistry()
        callback = Mock()

        registry.register(
            "hyperedge.created",
            callback,
            filter={"role": "author"},
        )

        event = Event(
            type="hyperedge.created",
            data={
                "id": "he:123",
                "members": [
                    {"entity_id": "e:1", "role": "author"},
                    {"entity_id": "e:2", "role": "book"},
                ],
            },
            timestamp=datetime.now(),
        )

        count = registry.dispatch(event)

        assert count == 1
        callback.assert_called_once_with(event)

    def test_dispatch_with_role_filter_no_match(self):
        """Dispatch skips handler when role filter doesn't match."""
        registry = EventRegistry()
        callback = Mock()

        registry.register(
            "hyperedge.created",
            callback,
            filter={"role": "author"},
        )

        event = Event(
            type="hyperedge.created",
            data={
                "id": "he:123",
                "members": [
                    {"entity_id": "e:1", "role": "subject"},
                    {"entity_id": "e:2", "role": "object"},
                ],
            },
            timestamp=datetime.now(),
        )

        count = registry.dispatch(event)

        assert count == 0
        callback.assert_not_called()

    def test_dispatch_with_data_field_filter(self):
        """Dispatch filters by data field values."""
        registry = EventRegistry()
        callback = Mock()

        registry.register(
            "entity.created",
            callback,
            filter={"entity_type": "person"},
        )

        # Should match
        event1 = Event(
            type="entity.created",
            data={"id": "e:1", "entity_type": "person"},
            timestamp=datetime.now(),
        )
        # Should not match
        event2 = Event(
            type="entity.created",
            data={"id": "e:2", "entity_type": "concept"},
            timestamp=datetime.now(),
        )

        count1 = registry.dispatch(event1)
        count2 = registry.dispatch(event2)

        assert count1 == 1
        assert count2 == 0
        callback.assert_called_once_with(event1)


class TestClientEventIntegration:
    """Tests for @db.on() decorator integration."""

    def test_client_has_event_registry(self):
        """Client initializes with event registry."""
        client = HyperX(api_key=TEST_API_KEY, base_url=TEST_BASE_URL)

        assert hasattr(client, "_event_registry")
        assert isinstance(client._event_registry, EventRegistry)

        client.close()

    def test_on_decorator_registers_handler(self):
        """@db.on() decorator registers handler."""
        client = HyperX(api_key=TEST_API_KEY, base_url=TEST_BASE_URL)

        @client.on("entity.created")
        def handle_entity(event: Event):
            pass

        assert len(client._event_registry.handlers) == 1
        assert client._event_registry.handlers[0].pattern == "entity.created"

        client.close()

    def test_on_decorator_with_filter(self):
        """@db.on() decorator accepts filter parameter."""
        client = HyperX(api_key=TEST_API_KEY, base_url=TEST_BASE_URL)

        @client.on("hyperedge.created", filter={"role": "author"})
        def handle_authorship(event: Event):
            pass

        handler = client._event_registry.handlers[0]
        assert handler.filter == {"role": "author"}

        client.close()

    def test_on_decorator_preserves_function(self):
        """@db.on() decorator returns original function."""
        client = HyperX(api_key=TEST_API_KEY, base_url=TEST_BASE_URL)

        @client.on("entity.created")
        def handle_entity(event: Event):
            return "original"

        # Function should still be callable
        assert handle_entity(Mock()) == "original"

        client.close()

    def test_emit_dispatches_to_handlers(self):
        """db.emit() dispatches events to registered handlers."""
        client = HyperX(api_key=TEST_API_KEY, base_url=TEST_BASE_URL)
        callback = Mock()

        @client.on("entity.created")
        def handle_entity(event: Event):
            callback(event)

        event = Event(
            type="entity.created",
            data={"id": "e:123"},
            timestamp=datetime.now(),
        )

        count = client.emit(event)

        assert count == 1
        callback.assert_called_once_with(event)

        client.close()

    def test_emit_returns_handler_count(self):
        """db.emit() returns number of handlers called."""
        client = HyperX(api_key=TEST_API_KEY, base_url=TEST_BASE_URL)

        @client.on("entity.*")
        def handle_all_entities(event: Event):
            pass

        @client.on("entity.created")
        def handle_created(event: Event):
            pass

        event = Event(
            type="entity.created",
            data={"id": "e:123"},
            timestamp=datetime.now(),
        )

        count = client.emit(event)

        assert count == 2

        client.close()

    def test_multiple_handlers_same_event(self):
        """Multiple handlers can be registered for same event."""
        client = HyperX(api_key=TEST_API_KEY, base_url=TEST_BASE_URL)
        results = []

        @client.on("entity.created")
        def handler1(event: Event):
            results.append("handler1")

        @client.on("entity.created")
        def handler2(event: Event):
            results.append("handler2")

        event = Event(
            type="entity.created",
            data={"id": "e:123"},
            timestamp=datetime.now(),
        )

        client.emit(event)

        assert "handler1" in results
        assert "handler2" in results

        client.close()


class TestAsyncClientEventIntegration:
    """Tests for async client event integration."""

    @pytest.mark.asyncio
    async def test_async_client_has_event_registry(self):
        """Async client initializes with event registry."""
        from hyperx import AsyncHyperX

        client = AsyncHyperX(api_key=TEST_API_KEY, base_url=TEST_BASE_URL)

        assert hasattr(client, "_event_registry")
        assert isinstance(client._event_registry, EventRegistry)

        await client.close()

    @pytest.mark.asyncio
    async def test_async_on_decorator(self):
        """@db.on() works with async client."""
        from hyperx import AsyncHyperX

        client = AsyncHyperX(api_key=TEST_API_KEY, base_url=TEST_BASE_URL)

        @client.on("entity.created")
        def handle_entity(event: Event):
            pass

        assert len(client._event_registry.handlers) == 1

        await client.close()

    @pytest.mark.asyncio
    async def test_async_emit(self):
        """Async client emit() works correctly."""
        from hyperx import AsyncHyperX

        client = AsyncHyperX(api_key=TEST_API_KEY, base_url=TEST_BASE_URL)
        callback = Mock()

        @client.on("entity.created")
        def handle_entity(event: Event):
            callback(event)

        event = Event(
            type="entity.created",
            data={"id": "e:123"},
            timestamp=datetime.now(),
        )

        count = client.emit(event)

        assert count == 1
        callback.assert_called_once()

        await client.close()


class TestEventTypes:
    """Tests for EventType literal."""

    def test_event_types_defined(self):
        """All expected event types are defined."""
        from typing import get_args

        event_types = get_args(EventType)

        assert "entity.created" in event_types
        assert "entity.updated" in event_types
        assert "entity.deleted" in event_types
        assert "hyperedge.created" in event_types
        assert "hyperedge.updated" in event_types
        assert "hyperedge.deleted" in event_types
        assert "path.discovered" in event_types
        assert "search.threshold_match" in event_types
