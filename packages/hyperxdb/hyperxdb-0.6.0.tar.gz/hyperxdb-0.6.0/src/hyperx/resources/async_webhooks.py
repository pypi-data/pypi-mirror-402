"""Async Webhooks API resource."""

from __future__ import annotations

from hyperx.http import AsyncHTTPClient
from hyperx.models import Webhook, WebhookDelivery


class AsyncWebhooksAPI:
    """Async API for managing webhook subscriptions.

    Example:
        >>> async with AsyncHyperX(api_key="hx_sk_...") as db:
        ...     webhook = await db.webhooks.create(
        ...         url="https://myapp.com/hooks",
        ...         events=["entity.created", "hyperedge.created"],
        ...         secret="whsec_..."
        ...     )
        ...     webhooks = await db.webhooks.list()
        ...     await db.webhooks.delete(webhook.id)
    """

    def __init__(self, http: AsyncHTTPClient):
        self._http = http

    async def create(
        self,
        url: str,
        events: list[str],
        *,
        secret: str | None = None,
    ) -> Webhook:
        """Create a webhook subscription.

        Args:
            url: Webhook endpoint URL (must be HTTPS in production)
            events: List of event types to subscribe to
                - "entity.created", "entity.updated", "entity.deleted"
                - "hyperedge.created", "hyperedge.updated", "hyperedge.deleted"
                - "path.discovered"
                - Use wildcards: "entity.*", "*"
            secret: Optional secret for HMAC signature verification

        Returns:
            Created Webhook
        """
        payload: dict[str, object] = {
            "url": url,
            "events": events,
        }
        if secret:
            payload["secret"] = secret

        data = await self._http.post("/v1/webhooks", json=payload)
        return Webhook.model_validate(data)

    async def get(self, webhook_id: str) -> Webhook:
        """Get a webhook by ID.

        Args:
            webhook_id: The webhook ID

        Returns:
            The webhook

        Raises:
            NotFoundError: If webhook doesn't exist
        """
        data = await self._http.get(f"/v1/webhooks/{webhook_id}")
        return Webhook.model_validate(data)

    async def list(self) -> list[Webhook]:
        """List all webhooks.

        Returns:
            List of webhooks
        """
        data = await self._http.get("/v1/webhooks")
        return [Webhook.model_validate(w) for w in data]

    async def update(
        self,
        webhook_id: str,
        *,
        url: str | None = None,
        events: list[str] | None = None,
        active: bool | None = None,
    ) -> Webhook:
        """Update a webhook.

        Args:
            webhook_id: The webhook ID to update
            url: New URL (optional)
            events: New events list (optional)
            active: Active status (optional)

        Returns:
            The updated webhook
        """
        payload: dict[str, object] = {}
        if url is not None:
            payload["url"] = url
        if events is not None:
            payload["events"] = events
        if active is not None:
            payload["active"] = active

        data = await self._http.put(f"/v1/webhooks/{webhook_id}", json=payload)
        return Webhook.model_validate(data)

    async def delete(self, webhook_id: str) -> bool:
        """Delete a webhook.

        Args:
            webhook_id: The webhook ID to delete

        Returns:
            True if deleted

        Raises:
            NotFoundError: If webhook doesn't exist
        """
        await self._http.delete(f"/v1/webhooks/{webhook_id}")
        return True

    async def deliveries(
        self,
        webhook_id: str,
        *,
        limit: int = 100,
    ) -> list[WebhookDelivery]:
        """List recent delivery attempts for a webhook.

        Args:
            webhook_id: The webhook ID
            limit: Maximum number of deliveries to return (default: 100)

        Returns:
            List of webhook deliveries
        """
        data = await self._http.get(
            f"/v1/webhooks/{webhook_id}/deliveries",
            params={"limit": limit},
        )
        return [WebhookDelivery.model_validate(d) for d in data]

    async def test(self, webhook_id: str) -> WebhookDelivery:
        """Send a test delivery to a webhook.

        Args:
            webhook_id: The webhook ID to test

        Returns:
            The test delivery result
        """
        data = await self._http.post(f"/v1/webhooks/{webhook_id}/test")
        return WebhookDelivery.model_validate(data)
