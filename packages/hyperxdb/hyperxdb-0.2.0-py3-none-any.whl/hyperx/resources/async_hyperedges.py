"""Async Hyperedges API resource."""

from typing import Any

from hyperx.http import AsyncHTTPClient
from hyperx.models import Hyperedge
from hyperx.resources.hyperedges import MemberInput


class AsyncHyperedgesAPI:
    """Async API for managing hyperedges in HyperX.

    Hyperedges are n-ary relationships that connect multiple entities
    with semantic roles.

    Example:
        >>> async with AsyncHyperX(api_key="hx_sk_...") as db:
        ...     edge = await db.hyperedges.create(
        ...         description="React provides Hooks",
        ...         members=[
        ...             {"entity_id": "e:react", "role": "subject"},
        ...             {"entity_id": "e:hooks", "role": "object"},
        ...         ]
        ...     )
    """

    def __init__(self, http: AsyncHTTPClient):
        self._http = http

    async def create(
        self,
        description: str,
        members: list[dict[str, str] | MemberInput],
        attributes: dict[str, Any] | None = None,
    ) -> Hyperedge:
        """Create a new hyperedge.

        Args:
            description: Human-readable description of the relationship
            members: List of entity members with roles (min 2)
            attributes: Optional key-value attributes

        Returns:
            The created hyperedge
        """
        member_dicts = [m.to_dict() if isinstance(m, MemberInput) else m for m in members]
        payload: dict[str, Any] = {"description": description, "members": member_dicts}
        if attributes:
            payload["attributes"] = attributes

        data = await self._http.post("/v1/hyperedges", json=payload)
        return Hyperedge.model_validate(data)

    async def get(self, hyperedge_id: str) -> Hyperedge:
        """Get a hyperedge by ID.

        Args:
            hyperedge_id: The hyperedge ID (e.g., "h:uuid...")

        Returns:
            The hyperedge

        Raises:
            NotFoundError: If hyperedge doesn't exist
        """
        data = await self._http.get(f"/v1/hyperedges/{hyperedge_id}")
        return Hyperedge.model_validate(data)

    async def delete(self, hyperedge_id: str) -> bool:
        """Delete a hyperedge.

        Args:
            hyperedge_id: The hyperedge ID to delete

        Returns:
            True if deleted

        Raises:
            NotFoundError: If hyperedge doesn't exist
        """
        await self._http.delete(f"/v1/hyperedges/{hyperedge_id}")
        return True

    async def update(
        self,
        hyperedge_id: str,
        description: str | None = None,
        members: list[dict[str, str] | MemberInput] | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> Hyperedge:
        """Update a hyperedge.

        Args:
            hyperedge_id: The hyperedge ID to update
            description: New description (optional)
            members: New members list (optional)
            attributes: New attributes (optional)

        Returns:
            The updated hyperedge
        """
        payload: dict[str, Any] = {}
        if description is not None:
            payload["description"] = description
        if members is not None:
            payload["members"] = [
                m.to_dict() if isinstance(m, MemberInput) else m for m in members
            ]
        if attributes is not None:
            payload["attributes"] = attributes

        data = await self._http.put(f"/v1/hyperedges/{hyperedge_id}", json=payload)
        return Hyperedge.model_validate(data)

    async def list(self, limit: int = 100, offset: int = 0) -> list[Hyperedge]:
        """List hyperedges with pagination.

        Args:
            limit: Maximum number to return (default: 100)
            offset: Number to skip (default: 0)

        Returns:
            List of hyperedges
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        data = await self._http.get("/v1/hyperedges", params=params)
        return [Hyperedge.model_validate(h) for h in data]
