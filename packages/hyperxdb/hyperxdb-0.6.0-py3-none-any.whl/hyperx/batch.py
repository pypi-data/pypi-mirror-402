"""Batch operation models for bulk data ingestion."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class EntityCreate:
    """Request model for creating an entity in a batch operation.

    Attributes:
        name: The name of the entity.
        entity_type: The type/category of the entity.
        attributes: Optional key-value attributes for the entity.
        embedding: Optional vector embedding for semantic search.
        valid_from: Optional start of validity period (bi-temporal).
        valid_until: Optional end of validity period (bi-temporal).
    """

    name: str
    entity_type: str
    attributes: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API serialization.

        Returns:
            Dictionary with operation type, resource, and entity data.
        """
        data: dict[str, Any] = {
            "name": self.name,
            "entity_type": self.entity_type,
            "attributes": self.attributes,
        }

        if self.embedding is not None:
            data["embedding"] = self.embedding
        if self.valid_from is not None:
            data["valid_from"] = self.valid_from.isoformat()
        if self.valid_until is not None:
            data["valid_until"] = self.valid_until.isoformat()

        return {
            "operation": "create",
            "resource": "entity",
            "data": data,
        }


@dataclass
class HyperedgeCreate:
    """Request model for creating a hyperedge in a batch operation.

    Attributes:
        description: Description of the relationship.
        members: List of member dictionaries with entity_id and role.
        attributes: Optional key-value attributes for the hyperedge.
        valid_from: Optional start of validity period (bi-temporal).
        valid_until: Optional end of validity period (bi-temporal).
    """

    description: str
    members: list[dict[str, str]]
    attributes: dict[str, Any] = field(default_factory=dict)
    valid_from: datetime | None = None
    valid_until: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API serialization.

        Returns:
            Dictionary with operation type, resource, and hyperedge data.
        """
        data: dict[str, Any] = {
            "description": self.description,
            "members": self.members,
            "attributes": self.attributes,
        }

        if self.valid_from is not None:
            data["valid_from"] = self.valid_from.isoformat()
        if self.valid_until is not None:
            data["valid_until"] = self.valid_until.isoformat()

        return {
            "operation": "create",
            "resource": "hyperedge",
            "data": data,
        }


@dataclass
class EntityDelete:
    """Request model for deleting an entity in a batch operation.

    Attributes:
        entity_id: The ID of the entity to delete.
    """

    entity_id: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API serialization.

        Returns:
            Dictionary with operation type, resource, and entity ID.
        """
        return {
            "operation": "delete",
            "resource": "entity",
            "id": self.entity_id,
        }


@dataclass
class HyperedgeDelete:
    """Request model for deleting a hyperedge in a batch operation.

    Attributes:
        hyperedge_id: The ID of the hyperedge to delete.
    """

    hyperedge_id: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API serialization.

        Returns:
            Dictionary with operation type, resource, and hyperedge ID.
        """
        return {
            "operation": "delete",
            "resource": "hyperedge",
            "id": self.hyperedge_id,
        }


@dataclass
class BatchItemResult:
    """Result for a single item in a batch operation.

    Attributes:
        success: Whether this individual operation succeeded.
        index: The index of this item in the original batch request.
        item: The original item that was processed (optional).
        error: Error message if the operation failed (optional).
    """

    success: bool
    index: int
    item: EntityCreate | HyperedgeCreate | EntityDelete | HyperedgeDelete | None = None
    error: str | None = None


@dataclass
class BatchResult:
    """Result of a batch operation.

    Attributes:
        success: Whether the overall batch succeeded (no failures).
        total: Total number of items in the batch.
        succeeded: Number of items that succeeded.
        failed: Number of items that failed.
        results: List of individual item results.
    """

    success: bool
    total: int
    succeeded: int
    failed: int
    results: list[BatchItemResult] = field(default_factory=list)

    @property
    def all_succeeded(self) -> bool:
        """Check if all items in the batch succeeded.

        Returns:
            True if no items failed, False otherwise.
        """
        return self.failed == 0

    @property
    def successful_items(self) -> list[BatchItemResult]:
        """Get all successful item results.

        Returns:
            List of BatchItemResult where success is True.
        """
        return [r for r in self.results if r.success]

    @property
    def failed_items(self) -> list[BatchItemResult]:
        """Get all failed item results.

        Returns:
            List of BatchItemResult where success is False.
        """
        return [r for r in self.results if not r.success]
