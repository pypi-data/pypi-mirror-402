"""Async Entities API resource."""

from typing import Any

from hyperx.http import AsyncHTTPClient
from hyperx.models import Entity


class AsyncEntitiesAPI:
    """Async API for managing entities in HyperX.

    Example:
        >>> async with AsyncHyperX(api_key="hx_sk_...") as db:
        ...     entity = await db.entities.create(name="React", entity_type="concept")
        ...     entity = await db.entities.get(entity.id)
        ...     await db.entities.delete(entity.id)
    """

    def __init__(self, http: AsyncHTTPClient):
        self._http = http

    async def create(
        self,
        name: str,
        entity_type: str,
        attributes: dict[str, Any] | None = None,
        embedding: list[float] | None = None,
    ) -> Entity:
        """Create a new entity.

        Args:
            name: Human-readable name for the entity
            entity_type: Type classification (e.g., "concept", "person", "document")
            attributes: Optional key-value attributes
            embedding: Optional vector embedding

        Returns:
            The created entity
        """
        payload: dict[str, Any] = {"name": name, "entity_type": entity_type}
        if attributes:
            payload["attributes"] = attributes
        if embedding:
            payload["embedding"] = embedding

        data = await self._http.post("/v1/entities", json=payload)
        return Entity.model_validate(data)

    async def get(self, entity_id: str) -> Entity:
        """Get an entity by ID.

        Args:
            entity_id: The entity ID (e.g., "e:uuid...")

        Returns:
            The entity

        Raises:
            NotFoundError: If entity doesn't exist
        """
        data = await self._http.get(f"/v1/entities/{entity_id}")
        return Entity.model_validate(data)

    async def delete(self, entity_id: str) -> bool:
        """Delete an entity.

        Args:
            entity_id: The entity ID to delete

        Returns:
            True if deleted

        Raises:
            NotFoundError: If entity doesn't exist
        """
        await self._http.delete(f"/v1/entities/{entity_id}")
        return True

    async def list(self, limit: int = 100, offset: int = 0) -> list[Entity]:
        """List entities with pagination.

        Args:
            limit: Maximum number of entities to return (default: 100)
            offset: Number of entities to skip (default: 0)

        Returns:
            List of entities
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        data = await self._http.get("/v1/entities", params=params)
        return [Entity.model_validate(e) for e in data]

    async def update(
        self,
        entity_id: str,
        name: str | None = None,
        entity_type: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> Entity:
        """Update an entity.

        Args:
            entity_id: The entity ID to update
            name: New name (optional)
            entity_type: New type (optional)
            attributes: New attributes (optional)

        Returns:
            The updated entity
        """
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if entity_type is not None:
            payload["entity_type"] = entity_type
        if attributes is not None:
            payload["attributes"] = attributes

        data = await self._http.put(f"/v1/entities/{entity_id}", json=payload)
        return Entity.model_validate(data)
