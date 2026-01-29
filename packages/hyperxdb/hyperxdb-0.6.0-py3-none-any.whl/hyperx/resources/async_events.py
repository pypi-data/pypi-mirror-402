"""Async Events API for real-time event streaming."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, AsyncGenerator

from hyperx.events import Event
from hyperx.http import AsyncHTTPClient


class AsyncEventsAPI:
    """Async API for real-time event streaming via SSE.

    Provides both real-time streaming and historical event retrieval
    using async/await patterns.

    Example:
        >>> async with AsyncHyperX(api_key="hx_sk_...") as db:
        ...     # Stream events asynchronously
        ...     async for event in db.events.stream(["entity.*"]):
        ...         print(f"{event.type}: {event.data}")
        ...         if should_stop:
        ...             break
        ...
        ...     # Get historical events
        ...     events = await db.events.history(limit=50)
    """

    def __init__(self, http: AsyncHTTPClient):
        """Initialize AsyncEventsAPI.

        Args:
            http: Async HTTP client for making API requests
        """
        self._http = http

    async def stream(
        self,
        event_types: list[str] | None = None,
        *,
        since: datetime | None = None,
    ) -> AsyncGenerator[Event, None]:
        """Stream events in real-time via Server-Sent Events.

        Opens a persistent connection to the server and yields events
        as they arrive. The connection remains open until the async
        generator is closed or an error occurs.

        Args:
            event_types: Event types to subscribe to (default: all)
                - "entity.created", "entity.updated", "entity.deleted"
                - "hyperedge.created", "hyperedge.updated", "hyperedge.deleted"
                - "path.discovered", "search.threshold_match"
                - Wildcards: "entity.*", "hyperedge.*", "*"
            since: Replay events since this timestamp (optional).
                   Useful for catching up after reconnection.

        Yields:
            Event objects as they arrive from the server

        Example:
            >>> async for event in db.events.stream(["entity.*"]):
            ...     print(f"Got event: {event.type}")
            ...     if event.type == "entity.deleted":
            ...         break  # Stop streaming
        """
        params: dict[str, Any] = {}
        if event_types:
            params["types"] = ",".join(event_types)
        if since:
            params["since"] = since.isoformat()

        # Use httpx async streaming for SSE
        async with self._http._client.stream(
            "GET",
            f"{self._http.base_url}/v1/events/stream",
            params=params,
            headers=self._http._headers(),
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    yield Event(
                        type=data["type"],
                        data=data["data"],
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                        metadata=data.get("metadata", {}),
                    )

    async def history(
        self,
        *,
        event_types: list[str] | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 100,
    ) -> list[Event]:
        """Get historical events (non-streaming).

        Retrieves past events from the server. Unlike stream(), this
        returns a finite list and does not maintain a persistent connection.

        Args:
            event_types: Filter by event types (same patterns as stream())
            since: Start time - only events after this timestamp
            until: End time - only events before this timestamp
            limit: Maximum number of events to return (default: 100)

        Returns:
            List of past events, ordered by timestamp (oldest first)

        Example:
            >>> from datetime import datetime, timedelta
            >>> yesterday = datetime.now() - timedelta(days=1)
            >>> events = await db.events.history(
            ...     event_types=["entity.created"],
            ...     since=yesterday,
            ...     limit=50
            ... )
        """
        params: dict[str, Any] = {"limit": limit}
        if event_types:
            params["types"] = ",".join(event_types)
        if since:
            params["since"] = since.isoformat()
        if until:
            params["until"] = until.isoformat()

        data = await self._http.get("/v1/events", params=params)
        return [
            Event(
                type=e["type"],
                data=e["data"],
                timestamp=datetime.fromisoformat(e["timestamp"]),
                metadata=e.get("metadata", {}),
            )
            for e in data
        ]
