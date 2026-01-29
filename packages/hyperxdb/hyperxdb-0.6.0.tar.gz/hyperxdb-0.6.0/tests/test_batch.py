"""Tests for batch operation models."""

from __future__ import annotations

from datetime import datetime

import pytest

from hyperx.batch import (
    BatchItemResult,
    BatchResult,
    EntityCreate,
    EntityDelete,
    HyperedgeCreate,
    HyperedgeDelete,
)


class TestEntityCreate:
    """Tests for EntityCreate dataclass."""

    def test_minimal_entity_create(self):
        """Test EntityCreate with only required fields."""
        entity = EntityCreate(name="Test Entity", entity_type="concept")

        assert entity.name == "Test Entity"
        assert entity.entity_type == "concept"
        assert entity.attributes == {}
        assert entity.embedding is None
        assert entity.valid_from is None
        assert entity.valid_until is None

    def test_entity_create_with_all_fields(self):
        """Test EntityCreate with all fields populated."""
        valid_from = datetime(2026, 1, 1, 0, 0, 0)
        valid_until = datetime(2026, 12, 31, 23, 59, 59)
        embedding = [0.1, 0.2, 0.3]

        entity = EntityCreate(
            name="Full Entity",
            entity_type="person",
            attributes={"age": 30, "role": "developer"},
            embedding=embedding,
            valid_from=valid_from,
            valid_until=valid_until,
        )

        assert entity.name == "Full Entity"
        assert entity.entity_type == "person"
        assert entity.attributes == {"age": 30, "role": "developer"}
        assert entity.embedding == [0.1, 0.2, 0.3]
        assert entity.valid_from == valid_from
        assert entity.valid_until == valid_until

    def test_entity_create_to_dict_minimal(self):
        """Test to_dict() with minimal fields."""
        entity = EntityCreate(name="Test", entity_type="concept")
        result = entity.to_dict()

        assert result == {
            "operation": "create",
            "resource": "entity",
            "data": {
                "name": "Test",
                "entity_type": "concept",
                "attributes": {},
            },
        }

    def test_entity_create_to_dict_with_optional_fields(self):
        """Test to_dict() includes optional fields when set."""
        valid_from = datetime(2026, 1, 1, 0, 0, 0)
        embedding = [0.1, 0.2]

        entity = EntityCreate(
            name="Test",
            entity_type="concept",
            attributes={"key": "value"},
            embedding=embedding,
            valid_from=valid_from,
        )
        result = entity.to_dict()

        assert result["operation"] == "create"
        assert result["resource"] == "entity"
        assert result["data"]["name"] == "Test"
        assert result["data"]["entity_type"] == "concept"
        assert result["data"]["attributes"] == {"key": "value"}
        assert result["data"]["embedding"] == [0.1, 0.2]
        assert result["data"]["valid_from"] == valid_from.isoformat()

    def test_entity_create_attributes_default_is_empty_dict(self):
        """Test that default attributes is an empty dict, not shared."""
        entity1 = EntityCreate(name="E1", entity_type="concept")
        entity2 = EntityCreate(name="E2", entity_type="concept")

        entity1.attributes["key"] = "value"

        assert entity2.attributes == {}


class TestHyperedgeCreate:
    """Tests for HyperedgeCreate dataclass."""

    def test_minimal_hyperedge_create(self):
        """Test HyperedgeCreate with only required fields."""
        members = [
            {"entity_id": "e:1", "role": "subject"},
            {"entity_id": "e:2", "role": "object"},
        ]
        hyperedge = HyperedgeCreate(description="relates to", members=members)

        assert hyperedge.description == "relates to"
        assert hyperedge.members == members
        assert hyperedge.attributes == {}
        assert hyperedge.valid_from is None
        assert hyperedge.valid_until is None

    def test_hyperedge_create_with_all_fields(self):
        """Test HyperedgeCreate with all fields populated."""
        valid_from = datetime(2026, 1, 1)
        valid_until = datetime(2026, 12, 31)
        members = [{"entity_id": "e:1", "role": "actor"}]

        hyperedge = HyperedgeCreate(
            description="performs action",
            members=members,
            attributes={"action_type": "create"},
            valid_from=valid_from,
            valid_until=valid_until,
        )

        assert hyperedge.description == "performs action"
        assert hyperedge.members == members
        assert hyperedge.attributes == {"action_type": "create"}
        assert hyperedge.valid_from == valid_from
        assert hyperedge.valid_until == valid_until

    def test_hyperedge_create_to_dict_minimal(self):
        """Test to_dict() with minimal fields."""
        members = [{"entity_id": "e:1", "role": "subject"}]
        hyperedge = HyperedgeCreate(description="test", members=members)
        result = hyperedge.to_dict()

        assert result == {
            "operation": "create",
            "resource": "hyperedge",
            "data": {
                "description": "test",
                "members": members,
                "attributes": {},
            },
        }

    def test_hyperedge_create_to_dict_with_optional_fields(self):
        """Test to_dict() includes optional fields when set."""
        valid_from = datetime(2026, 6, 15)
        members = [{"entity_id": "e:1", "role": "node"}]

        hyperedge = HyperedgeCreate(
            description="test",
            members=members,
            attributes={"weight": 0.5},
            valid_from=valid_from,
        )
        result = hyperedge.to_dict()

        assert result["operation"] == "create"
        assert result["resource"] == "hyperedge"
        assert result["data"]["description"] == "test"
        assert result["data"]["members"] == members
        assert result["data"]["attributes"] == {"weight": 0.5}
        assert result["data"]["valid_from"] == valid_from.isoformat()

    def test_hyperedge_create_members_default_is_independent(self):
        """Test that default members list is not shared between instances."""
        members1 = [{"entity_id": "e:1", "role": "a"}]
        members2 = [{"entity_id": "e:2", "role": "b"}]

        h1 = HyperedgeCreate(description="h1", members=members1)
        h2 = HyperedgeCreate(description="h2", members=members2)

        assert h1.members != h2.members


class TestEntityDelete:
    """Tests for EntityDelete dataclass."""

    def test_entity_delete(self):
        """Test EntityDelete creation."""
        delete = EntityDelete(entity_id="e:test-uuid")

        assert delete.entity_id == "e:test-uuid"

    def test_entity_delete_to_dict(self):
        """Test to_dict() returns correct format."""
        delete = EntityDelete(entity_id="e:12345")
        result = delete.to_dict()

        assert result == {
            "operation": "delete",
            "resource": "entity",
            "id": "e:12345",
        }


class TestHyperedgeDelete:
    """Tests for HyperedgeDelete dataclass."""

    def test_hyperedge_delete(self):
        """Test HyperedgeDelete creation."""
        delete = HyperedgeDelete(hyperedge_id="h:test-uuid")

        assert delete.hyperedge_id == "h:test-uuid"

    def test_hyperedge_delete_to_dict(self):
        """Test to_dict() returns correct format."""
        delete = HyperedgeDelete(hyperedge_id="h:67890")
        result = delete.to_dict()

        assert result == {
            "operation": "delete",
            "resource": "hyperedge",
            "id": "h:67890",
        }


class TestBatchItemResult:
    """Tests for BatchItemResult dataclass."""

    def test_successful_item_result(self):
        """Test BatchItemResult for a successful operation."""
        item = EntityCreate(name="Test", entity_type="concept")
        result = BatchItemResult(success=True, index=0, item=item)

        assert result.success is True
        assert result.index == 0
        assert result.item == item
        assert result.error is None

    def test_failed_item_result(self):
        """Test BatchItemResult for a failed operation."""
        result = BatchItemResult(
            success=False,
            index=2,
            error="Validation failed: name is required",
        )

        assert result.success is False
        assert result.index == 2
        assert result.item is None
        assert result.error == "Validation failed: name is required"

    def test_item_result_with_both_item_and_error(self):
        """Test BatchItemResult can have both item and error (for partial failures)."""
        item = EntityCreate(name="Test", entity_type="concept")
        result = BatchItemResult(
            success=False,
            index=1,
            item=item,
            error="Duplicate entity name",
        )

        assert result.success is False
        assert result.item == item
        assert result.error == "Duplicate entity name"


class TestBatchResult:
    """Tests for BatchResult dataclass."""

    def test_all_successful_batch(self):
        """Test BatchResult when all operations succeed."""
        results = [
            BatchItemResult(success=True, index=0),
            BatchItemResult(success=True, index=1),
            BatchItemResult(success=True, index=2),
        ]
        batch = BatchResult(
            success=True,
            total=3,
            succeeded=3,
            failed=0,
            results=results,
        )

        assert batch.success is True
        assert batch.total == 3
        assert batch.succeeded == 3
        assert batch.failed == 0
        assert len(batch.results) == 3

    def test_partial_failure_batch(self):
        """Test BatchResult when some operations fail."""
        results = [
            BatchItemResult(success=True, index=0),
            BatchItemResult(success=False, index=1, error="Invalid type"),
            BatchItemResult(success=True, index=2),
        ]
        batch = BatchResult(
            success=False,
            total=3,
            succeeded=2,
            failed=1,
            results=results,
        )

        assert batch.success is False
        assert batch.total == 3
        assert batch.succeeded == 2
        assert batch.failed == 1

    def test_all_failed_batch(self):
        """Test BatchResult when all operations fail."""
        results = [
            BatchItemResult(success=False, index=0, error="Error 1"),
            BatchItemResult(success=False, index=1, error="Error 2"),
        ]
        batch = BatchResult(
            success=False,
            total=2,
            succeeded=0,
            failed=2,
            results=results,
        )

        assert batch.success is False
        assert batch.succeeded == 0
        assert batch.failed == 2

    def test_all_succeeded_property_true(self):
        """Test all_succeeded property returns True when no failures."""
        batch = BatchResult(
            success=True,
            total=5,
            succeeded=5,
            failed=0,
            results=[],
        )

        assert batch.all_succeeded is True

    def test_all_succeeded_property_false(self):
        """Test all_succeeded property returns False when there are failures."""
        batch = BatchResult(
            success=False,
            total=5,
            succeeded=3,
            failed=2,
            results=[],
        )

        assert batch.all_succeeded is False

    def test_successful_items_property(self):
        """Test successful_items property filters correctly."""
        results = [
            BatchItemResult(success=True, index=0),
            BatchItemResult(success=False, index=1, error="Error"),
            BatchItemResult(success=True, index=2),
            BatchItemResult(success=False, index=3, error="Error"),
        ]
        batch = BatchResult(
            success=False,
            total=4,
            succeeded=2,
            failed=2,
            results=results,
        )

        successful = batch.successful_items

        assert len(successful) == 2
        assert all(item.success for item in successful)
        assert [item.index for item in successful] == [0, 2]

    def test_failed_items_property(self):
        """Test failed_items property filters correctly."""
        results = [
            BatchItemResult(success=True, index=0),
            BatchItemResult(success=False, index=1, error="Error 1"),
            BatchItemResult(success=True, index=2),
            BatchItemResult(success=False, index=3, error="Error 2"),
        ]
        batch = BatchResult(
            success=False,
            total=4,
            succeeded=2,
            failed=2,
            results=results,
        )

        failed = batch.failed_items

        assert len(failed) == 2
        assert all(not item.success for item in failed)
        assert [item.index for item in failed] == [1, 3]

    def test_empty_batch(self):
        """Test BatchResult with no items."""
        batch = BatchResult(
            success=True,
            total=0,
            succeeded=0,
            failed=0,
            results=[],
        )

        assert batch.all_succeeded is True
        assert batch.successful_items == []
        assert batch.failed_items == []

    def test_results_default_is_empty_list(self):
        """Test that default results is an empty list, not shared."""
        batch1 = BatchResult(success=True, total=0, succeeded=0, failed=0)
        batch2 = BatchResult(success=True, total=0, succeeded=0, failed=0)

        batch1.results.append(BatchItemResult(success=True, index=0))

        assert len(batch2.results) == 0
