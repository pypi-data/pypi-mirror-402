"""Triggers API resource."""

from __future__ import annotations

from typing import Any, Literal

from hyperx.http import HTTPClient
from hyperx.models import Trigger


class TriggersAPI:
    """API for managing custom event triggers.

    Triggers evaluate conditions against events and execute actions
    (webhooks, notifications) when conditions match.

    Example:
        >>> trigger = db.triggers.create(
        ...     name="high_confidence_path",
        ...     condition="path.cost < 0.5 AND path.hops <= 2",
        ...     event_types=["path.discovered"],
        ...     action="webhook",
        ...     webhook_id="wh:123",
        ... )
    """

    def __init__(self, http: HTTPClient):
        self._http = http

    def create(
        self,
        name: str,
        condition: str,
        event_types: list[str],
        action: Literal["webhook", "notification"],
        *,
        webhook_id: str | None = None,
    ) -> Trigger:
        """Create a custom trigger.

        Args:
            name: Human-readable trigger name
            condition: Expression to evaluate against events
                - Supports: <, >, <=, >=, ==, !=, AND, OR
                - Fields: event.data.*, path.cost, path.hops, entity.type
            event_types: Which events to evaluate
            action: What to do when condition matches
            webhook_id: Required if action == "webhook"

        Returns:
            Created Trigger
        """
        payload: dict[str, object] = {
            "name": name,
            "condition": condition,
            "event_types": event_types,
            "action": action,
        }
        if webhook_id:
            payload["webhook_id"] = webhook_id

        data = self._http.post("/v1/triggers", json=payload)
        return Trigger.model_validate(data)

    def get(self, trigger_id: str) -> Trigger:
        """Get a trigger by ID.

        Args:
            trigger_id: The trigger ID

        Returns:
            The trigger

        Raises:
            NotFoundError: If trigger doesn't exist
        """
        data = self._http.get(f"/v1/triggers/{trigger_id}")
        return Trigger.model_validate(data)

    def list(self) -> list[Trigger]:
        """List all triggers.

        Returns:
            List of triggers
        """
        data = self._http.get("/v1/triggers")
        return [Trigger.model_validate(t) for t in data]

    def update(
        self,
        trigger_id: str,
        *,
        name: str | None = None,
        condition: str | None = None,
        event_types: list[str] | None = None,
        active: bool | None = None,
    ) -> Trigger:
        """Update a trigger.

        Args:
            trigger_id: The trigger ID to update
            name: New name (optional)
            condition: New condition expression (optional)
            event_types: New event types list (optional)
            active: Active status (optional)

        Returns:
            The updated trigger
        """
        payload: dict[str, object] = {}
        if name is not None:
            payload["name"] = name
        if condition is not None:
            payload["condition"] = condition
        if event_types is not None:
            payload["event_types"] = event_types
        if active is not None:
            payload["active"] = active

        data = self._http.put(f"/v1/triggers/{trigger_id}", json=payload)
        return Trigger.model_validate(data)

    def delete(self, trigger_id: str) -> bool:
        """Delete a trigger.

        Args:
            trigger_id: The trigger ID to delete

        Returns:
            True if deleted

        Raises:
            NotFoundError: If trigger doesn't exist
        """
        self._http.delete(f"/v1/triggers/{trigger_id}")
        return True

    def test(
        self,
        trigger_id: str,
        event_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Test a trigger against sample event data.

        Args:
            trigger_id: The trigger ID to test
            event_data: Sample event data to evaluate the condition against

        Returns:
            {"matched": bool, "evaluation": str}
        """
        data = self._http.post(
            f"/v1/triggers/{trigger_id}/test",
            json={"event_data": event_data},
        )
        return data
