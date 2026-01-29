"""Entities API resource."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from hyperx.http import HTTPClient
from hyperx.models import Entity


class EntitiesAPI:
    """API for managing entities in HyperX.

    Example:
        >>> db = HyperX(api_key="hx_sk_...")
        >>> entity = db.entities.create(name="React", entity_type="concept")
        >>> entity = db.entities.get(entity.id)
        >>> db.entities.delete(entity.id)
    """

    def __init__(self, http: HTTPClient):
        self._http = http

    def create(
        self,
        name: str,
        entity_type: str,
        attributes: dict[str, Any] | None = None,
        embedding: list[float] | None = None,
        *,
        valid_from: datetime | None = None,
        valid_until: datetime | None = None,
    ) -> Entity:
        """Create a new entity.

        Args:
            name: Human-readable name for the entity
            entity_type: Type classification (e.g., "concept", "person", "document")
            attributes: Optional key-value attributes
            embedding: Optional vector embedding
            valid_from: When entity becomes valid (default: now)
            valid_until: When entity stops being valid (default: forever)

        Returns:
            The created entity
        """
        payload: dict[str, Any] = {
            "name": name,
            "entity_type": entity_type,
        }
        if attributes:
            payload["attributes"] = attributes
        if embedding:
            payload["embedding"] = embedding
        if valid_from:
            payload["valid_from"] = valid_from.isoformat()
        if valid_until:
            payload["valid_until"] = valid_until.isoformat()

        data = self._http.post("/v1/entities", json=payload)
        return Entity.model_validate(data)

    def get(self, entity_id: str) -> Entity:
        """Get an entity by ID.

        Args:
            entity_id: The entity ID (e.g., "e:uuid...")

        Returns:
            The entity

        Raises:
            NotFoundError: If entity doesn't exist
        """
        data = self._http.get(f"/v1/entities/{entity_id}")
        return Entity.model_validate(data)

    def delete(self, entity_id: str) -> bool:
        """Delete an entity.

        Args:
            entity_id: The entity ID to delete

        Returns:
            True if deleted

        Raises:
            NotFoundError: If entity doesn't exist
        """
        self._http.delete(f"/v1/entities/{entity_id}")
        return True

    def update(
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

        data = self._http.put(f"/v1/entities/{entity_id}", json=payload)
        return Entity.model_validate(data)

    def list(
        self,
        limit: int = 100,
        offset: int = 0,
        *,
        as_of: datetime | None = None,
        include_deprecated: bool = False,
        include_history: bool = False,
    ) -> list[Entity]:
        """List entities with pagination and temporal filters.

        Args:
            limit: Maximum number of entities to return (default: 100)
            offset: Number of entities to skip (default: 0)
            as_of: Filter to entities valid at this time
            include_deprecated: Include deprecated entities
            include_history: Include superseded entities

        Returns:
            List of entities
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if as_of:
            params["as_of"] = as_of.isoformat()
        if include_deprecated:
            params["include_deprecated"] = "true"
        if include_history:
            params["include_history"] = "true"

        data = self._http.get("/v1/entities", params=params)
        return [Entity.model_validate(e) for e in data]

    def deprecate(self, entity_id: str, reason: str) -> Entity:
        """Deprecate an entity.

        Args:
            entity_id: The entity ID to deprecate
            reason: Reason for deprecation

        Returns:
            The deprecated entity
        """
        data = self._http.post(
            f"/v1/entities/{entity_id}/deprecate",
            json={"reason": reason},
        )
        return Entity.model_validate(data)

    def supersede(
        self,
        entity_id: str,
        name: str,
        entity_type: str,
        attributes: dict[str, Any] | None = None,
    ) -> Entity:
        """Supersede an entity with a new version.

        Args:
            entity_id: The entity ID to supersede
            name: Name for the new version
            entity_type: Entity type for the new version
            attributes: Attributes for the new version

        Returns:
            The new entity version
        """
        payload: dict[str, Any] = {
            "name": name,
            "entity_type": entity_type,
        }
        if attributes:
            payload["attributes"] = attributes

        data = self._http.post(
            f"/v1/entities/{entity_id}/supersede",
            json=payload,
        )
        return Entity.model_validate(data)

    def retire(self, entity_id: str) -> Entity:
        """Retire an entity.

        Args:
            entity_id: The entity ID to retire

        Returns:
            The retired entity
        """
        data = self._http.post(f"/v1/entities/{entity_id}/retire")
        return Entity.model_validate(data)

    def reactivate(self, entity_id: str) -> Entity:
        """Reactivate a deprecated entity.

        Args:
            entity_id: The entity ID to reactivate

        Returns:
            The reactivated entity
        """
        data = self._http.post(f"/v1/entities/{entity_id}/reactivate")
        return Entity.model_validate(data)

    def history(self, entity_id: str) -> list[Entity]:
        """Get version history for an entity.

        Args:
            entity_id: The entity ID

        Returns:
            List of all versions, ordered by version number
        """
        data = self._http.get(f"/v1/entities/{entity_id}/history")
        return [Entity.model_validate(e) for e in data]

    def create_many(
        self,
        entities: list[dict[str, Any]],
        *,
        atomic: bool = True,
    ) -> list[Entity]:
        """Create multiple entities in a single request.

        Args:
            entities: List of entity dicts with keys:
                - name (required): Entity name
                - entity_type (required): Entity type
                - attributes (optional): Key-value attributes
                - embedding (optional): Vector embedding
                - valid_from (optional): datetime
                - valid_until (optional): datetime
            atomic: If True (default), all succeed or all fail

        Returns:
            List of created Entity objects

        Raises:
            HyperXError: If atomic=True and any entity fails validation
        """
        payload = {"entities": entities, "atomic": atomic}
        data = self._http.post("/v1/entities/batch", json=payload)
        return [Entity.model_validate(e) for e in data["entities"]]

    def delete_many(
        self,
        entity_ids: list[str],
        *,
        atomic: bool = True,
    ) -> int:
        """Delete multiple entities.

        Args:
            entity_ids: List of entity IDs to delete
            atomic: If True (default), all succeed or all fail

        Returns:
            Number of entities deleted
        """
        payload = {"ids": entity_ids, "atomic": atomic}
        data = self._http.post("/v1/entities/batch/delete", json=payload)
        return data["deleted"]
