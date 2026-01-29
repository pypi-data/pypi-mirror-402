"""Event system for local event handlers.

Provides event models and a decorator pattern for registering local handlers
that respond to HyperX events (e.g., entity.created, hyperedge.updated).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from fnmatch import fnmatch
from typing import Any, Literal

EventType = Literal[
    "entity.created",
    "entity.updated",
    "entity.deleted",
    "hyperedge.created",
    "hyperedge.updated",
    "hyperedge.deleted",
    "path.discovered",
    "search.threshold_match",
]


@dataclass
class Event:
    """An event from the HyperX system.

    Attributes:
        type: Event type (e.g., "entity.created")
        data: Event payload (entity, hyperedge, or path data)
        timestamp: When the event occurred
        metadata: Additional context (optional)
    """

    type: str
    data: dict[str, Any]
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EventHandler:
    """A registered event handler.

    Attributes:
        pattern: Event pattern with wildcards (e.g., "entity.*")
        callback: Function to call when event matches
        filter: Optional filter conditions
    """

    pattern: str  # Event pattern with wildcards (e.g., "entity.*")
    callback: Callable[[Event], None]
    filter: dict[str, Any] | None = None

    def matches(self, event_type: str) -> bool:
        """Check if event type matches this handler's pattern.

        Supports glob-style wildcards:
        - "entity.created" matches only "entity.created"
        - "entity.*" matches "entity.created", "entity.updated", etc.
        - "*" matches all events

        Args:
            event_type: The event type to check

        Returns:
            True if the event type matches the handler's pattern
        """
        return fnmatch(event_type, self.pattern)


class EventRegistry:
    """Registry for local event handlers.

    Used internally by the client to manage @db.on() handlers.

    Example:
        >>> registry = EventRegistry()
        >>> handler = registry.register("entity.created", my_callback)
        >>> registry.dispatch(Event(type="entity.created", data={...}, timestamp=now))
    """

    def __init__(self) -> None:
        """Initialize empty handler registry."""
        self._handlers: list[EventHandler] = []

    def register(
        self,
        pattern: str,
        callback: Callable[[Event], None],
        filter: dict[str, Any] | None = None,
    ) -> EventHandler:
        """Register an event handler.

        Args:
            pattern: Event pattern to match (supports wildcards)
            callback: Function to call when event matches
            filter: Optional filter conditions for additional matching

        Returns:
            The registered EventHandler instance
        """
        handler = EventHandler(pattern=pattern, callback=callback, filter=filter)
        self._handlers.append(handler)
        return handler

    def unregister(self, handler: EventHandler) -> bool:
        """Unregister an event handler.

        Args:
            handler: The handler to remove

        Returns:
            True if handler was found and removed, False otherwise
        """
        if handler in self._handlers:
            self._handlers.remove(handler)
            return True
        return False

    def dispatch(self, event: Event) -> int:
        """Dispatch event to matching handlers.

        Args:
            event: The event to dispatch

        Returns:
            Number of handlers that were called
        """
        called = 0
        for handler in self._handlers:
            if handler.matches(event.type):
                # Check filter if present - skip if filter doesn't match
                if handler.filter and not self._matches_filter(event, handler.filter):
                    continue
                handler.callback(event)
                called += 1
        return called

    def _matches_filter(self, event: Event, filter: dict[str, Any]) -> bool:
        """Check if event matches filter criteria.

        Supports special filter keys:
        - "role": Check if any member has this role (for hyperedge events)
        - Other keys: Check if event.data has matching value

        Args:
            event: The event to check
            filter: Filter conditions to match

        Returns:
            True if event matches all filter conditions
        """
        for key, value in filter.items():
            if key == "role":
                # Check if any member has this role
                members = event.data.get("members", [])
                if not any(m.get("role") == value for m in members):
                    return False
            elif key in event.data:
                if event.data[key] != value:
                    return False
            else:
                # Key not in data means no match
                return False
        return True

    @property
    def handlers(self) -> list[EventHandler]:
        """Get all registered handlers.

        Returns:
            List of all registered EventHandler instances
        """
        return list(self._handlers)
