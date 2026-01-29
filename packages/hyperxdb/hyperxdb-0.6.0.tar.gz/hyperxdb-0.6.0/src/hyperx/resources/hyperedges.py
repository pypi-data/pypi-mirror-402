"""Hyperedges API resource."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from hyperx.http import HTTPClient
from hyperx.models import Hyperedge


class MemberInput:
    """Helper for creating hyperedge members.

    Example:
        >>> member = MemberInput("e:react", "subject")
        >>> member.to_dict()
        {'entity_id': 'e:react', 'role': 'subject'}
    """

    def __init__(self, entity_id: str, role: str):
        self.entity_id = entity_id
        self.role = role

    def to_dict(self) -> dict[str, str]:
        return {"entity_id": self.entity_id, "role": self.role}


class HyperedgesAPI:
    """API for managing hyperedges in HyperX.

    Hyperedges are n-ary relationships that connect multiple entities
    with semantic roles.

    Example:
        >>> db = HyperX(api_key="hx_sk_...")
        >>> edge = db.hyperedges.create(
        ...     description="React provides Hooks",
        ...     members=[
        ...         {"entity_id": "e:react", "role": "subject"},
        ...         {"entity_id": "e:hooks", "role": "object"},
        ...     ]
        ... )
    """

    def __init__(self, http: HTTPClient):
        self._http = http

    def create(
        self,
        description: str,
        members: list[dict[str, str] | MemberInput],
        attributes: dict[str, Any] | None = None,
        *,
        valid_from: datetime | None = None,
        valid_until: datetime | None = None,
    ) -> Hyperedge:
        """Create a new hyperedge.

        Args:
            description: Human-readable description of the relationship
            members: List of entity members with roles (min 2)
            attributes: Optional key-value attributes
            valid_from: When relationship becomes valid (default: now)
            valid_until: When relationship stops being valid (default: forever)

        Returns:
            The created hyperedge
        """
        member_dicts = [
            m.to_dict() if isinstance(m, MemberInput) else m for m in members
        ]

        payload: dict[str, Any] = {
            "description": description,
            "members": member_dicts,
        }
        if attributes:
            payload["attributes"] = attributes
        if valid_from:
            payload["valid_from"] = valid_from.isoformat()
        if valid_until:
            payload["valid_until"] = valid_until.isoformat()

        data = self._http.post("/v1/hyperedges", json=payload)
        return Hyperedge.model_validate(data)

    def get(self, hyperedge_id: str) -> Hyperedge:
        """Get a hyperedge by ID.

        Args:
            hyperedge_id: The hyperedge ID (e.g., "h:uuid...")

        Returns:
            The hyperedge

        Raises:
            NotFoundError: If hyperedge doesn't exist
        """
        data = self._http.get(f"/v1/hyperedges/{hyperedge_id}")
        return Hyperedge.model_validate(data)

    def delete(self, hyperedge_id: str) -> bool:
        """Delete a hyperedge.

        Args:
            hyperedge_id: The hyperedge ID to delete

        Returns:
            True if deleted

        Raises:
            NotFoundError: If hyperedge doesn't exist
        """
        self._http.delete(f"/v1/hyperedges/{hyperedge_id}")
        return True

    def list(
        self,
        limit: int = 100,
        offset: int = 0,
        *,
        as_of: datetime | None = None,
        include_deprecated: bool = False,
        include_history: bool = False,
    ) -> list[Hyperedge]:
        """List hyperedges with pagination and temporal filters.

        Args:
            limit: Maximum number to return (default: 100)
            offset: Number to skip (default: 0)
            as_of: Filter to hyperedges valid at this time
            include_deprecated: Include deprecated hyperedges
            include_history: Include superseded hyperedges

        Returns:
            List of hyperedges
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if as_of:
            params["as_of"] = as_of.isoformat()
        if include_deprecated:
            params["include_deprecated"] = "true"
        if include_history:
            params["include_history"] = "true"

        data = self._http.get("/v1/hyperedges", params=params)
        return [Hyperedge.model_validate(h) for h in data]

    def update(
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

        data = self._http.put(f"/v1/hyperedges/{hyperedge_id}", json=payload)
        return Hyperedge.model_validate(data)

    def deprecate(self, hyperedge_id: str, reason: str) -> Hyperedge:
        """Deprecate a hyperedge.

        Args:
            hyperedge_id: The hyperedge ID to deprecate
            reason: Reason for deprecation

        Returns:
            The deprecated hyperedge
        """
        data = self._http.post(
            f"/v1/hyperedges/{hyperedge_id}/deprecate",
            json={"reason": reason},
        )
        return Hyperedge.model_validate(data)

    def supersede(
        self,
        hyperedge_id: str,
        description: str,
        members: list[dict[str, str] | MemberInput],
        attributes: dict[str, Any] | None = None,
    ) -> Hyperedge:
        """Supersede a hyperedge with a new version.

        Args:
            hyperedge_id: The hyperedge ID to supersede
            description: Description for the new version
            members: Members for the new version
            attributes: Attributes for the new version

        Returns:
            The new hyperedge version
        """
        member_dicts = [
            m.to_dict() if isinstance(m, MemberInput) else m for m in members
        ]
        payload: dict[str, Any] = {
            "description": description,
            "members": member_dicts,
        }
        if attributes:
            payload["attributes"] = attributes

        data = self._http.post(
            f"/v1/hyperedges/{hyperedge_id}/supersede",
            json=payload,
        )
        return Hyperedge.model_validate(data)

    def retire(self, hyperedge_id: str) -> Hyperedge:
        """Retire a hyperedge.

        Args:
            hyperedge_id: The hyperedge ID to retire

        Returns:
            The retired hyperedge
        """
        data = self._http.post(f"/v1/hyperedges/{hyperedge_id}/retire")
        return Hyperedge.model_validate(data)

    def reactivate(self, hyperedge_id: str) -> Hyperedge:
        """Reactivate a deprecated hyperedge.

        Args:
            hyperedge_id: The hyperedge ID to reactivate

        Returns:
            The reactivated hyperedge
        """
        data = self._http.post(f"/v1/hyperedges/{hyperedge_id}/reactivate")
        return Hyperedge.model_validate(data)

    def history(self, hyperedge_id: str) -> list[Hyperedge]:
        """Get version history for a hyperedge.

        Args:
            hyperedge_id: The hyperedge ID

        Returns:
            List of all versions, ordered by version number
        """
        data = self._http.get(f"/v1/hyperedges/{hyperedge_id}/history")
        return [Hyperedge.model_validate(h) for h in data]

    def create_many(
        self,
        hyperedges: list[dict[str, Any]],
        *,
        atomic: bool = True,
    ) -> list[Hyperedge]:
        """Create multiple hyperedges in a single request.

        Args:
            hyperedges: List of hyperedge dicts with keys:
                - description (required): Relationship description
                - members (required): List of member dicts with entity_id and role
                - attributes (optional): Key-value attributes
                - valid_from (optional): datetime
                - valid_until (optional): datetime
            atomic: If True (default), all succeed or all fail

        Returns:
            List of created Hyperedge objects

        Raises:
            HyperXError: If atomic=True and any hyperedge fails validation
        """
        payload = {"hyperedges": hyperedges, "atomic": atomic}
        data = self._http.post("/v1/hyperedges/batch", json=payload)
        return [Hyperedge.model_validate(h) for h in data["hyperedges"]]

    def delete_many(
        self,
        hyperedge_ids: list[str],
        *,
        atomic: bool = True,
    ) -> int:
        """Delete multiple hyperedges.

        Args:
            hyperedge_ids: List of hyperedge IDs to delete
            atomic: If True (default), all succeed or all fail

        Returns:
            Number of hyperedges deleted
        """
        payload = {"ids": hyperedge_ids, "atomic": atomic}
        data = self._http.post("/v1/hyperedges/batch/delete", json=payload)
        return data["deleted"]
