"""Tests for BatchAPI resource."""

from __future__ import annotations

import pytest
from pytest_httpx import HTTPXMock

from hyperx import HyperX
from hyperx.batch import (
    BatchItemResult,
    BatchResult,
    EntityCreate,
    EntityDelete,
    HyperedgeCreate,
    HyperedgeDelete,
)


class TestBatchAPIExecute:
    """Tests for BatchAPI.execute method."""

    def test_execute_single_entity_create(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test executing a batch with a single entity create operation."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/batch",
            json={
                "success": True,
                "total": 1,
                "succeeded": 1,
                "failed": 0,
                "results": [
                    {"success": True, "index": 0}
                ],
            },
        )

        operations = [EntityCreate(name="React", entity_type="library")]
        result = client.batch.execute(operations)

        assert result.success is True
        assert result.total == 1
        assert result.succeeded == 1
        assert result.failed == 0
        assert len(result.results) == 1
        assert result.results[0].success is True

    def test_execute_multiple_entity_creates(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test executing a batch with multiple entity create operations."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/batch",
            json={
                "success": True,
                "total": 3,
                "succeeded": 3,
                "failed": 0,
                "results": [
                    {"success": True, "index": 0},
                    {"success": True, "index": 1},
                    {"success": True, "index": 2},
                ],
            },
        )

        operations = [
            EntityCreate(name="React", entity_type="library"),
            EntityCreate(name="Vue", entity_type="library"),
            EntityCreate(name="Angular", entity_type="library"),
        ]
        result = client.batch.execute(operations)

        assert result.success is True
        assert result.total == 3
        assert result.succeeded == 3
        assert result.failed == 0
        assert len(result.results) == 3

    def test_execute_mixed_operations(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test executing a batch with mixed operation types."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/batch",
            json={
                "success": True,
                "total": 4,
                "succeeded": 4,
                "failed": 0,
                "results": [
                    {"success": True, "index": 0},
                    {"success": True, "index": 1},
                    {"success": True, "index": 2},
                    {"success": True, "index": 3},
                ],
            },
        )

        operations = [
            EntityCreate(name="React", entity_type="library"),
            HyperedgeCreate(
                description="React uses hooks",
                members=[
                    {"entity_id": "e:react", "role": "subject"},
                    {"entity_id": "e:hooks", "role": "object"},
                ],
            ),
            EntityDelete(entity_id="e:old-lib"),
            HyperedgeDelete(hyperedge_id="h:old-relation"),
        ]
        result = client.batch.execute(operations)

        assert result.success is True
        assert result.total == 4
        assert result.succeeded == 4

    def test_execute_atomic_mode_default(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test that atomic mode is True by default."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/batch",
            json={
                "success": True,
                "total": 1,
                "succeeded": 1,
                "failed": 0,
                "results": [{"success": True, "index": 0}],
            },
        )

        operations = [EntityCreate(name="Test", entity_type="concept")]
        client.batch.execute(operations)

        # Verify the request was made with atomic=True
        request = httpx_mock.get_request()
        assert request is not None
        import json
        body = json.loads(request.content)
        assert body["atomic"] is True

    def test_execute_atomic_mode_explicit_true(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test explicitly setting atomic=True."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/batch",
            json={
                "success": True,
                "total": 1,
                "succeeded": 1,
                "failed": 0,
                "results": [{"success": True, "index": 0}],
            },
        )

        operations = [EntityCreate(name="Test", entity_type="concept")]
        client.batch.execute(operations, atomic=True)

        request = httpx_mock.get_request()
        assert request is not None
        import json
        body = json.loads(request.content)
        assert body["atomic"] is True

    def test_execute_best_effort_mode(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test executing with atomic=False (best-effort mode)."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/batch",
            json={
                "success": False,
                "total": 3,
                "succeeded": 2,
                "failed": 1,
                "results": [
                    {"success": True, "index": 0},
                    {"success": False, "index": 1, "error": "Duplicate entity"},
                    {"success": True, "index": 2},
                ],
            },
        )

        operations = [
            EntityCreate(name="Entity1", entity_type="concept"),
            EntityCreate(name="Duplicate", entity_type="concept"),
            EntityCreate(name="Entity3", entity_type="concept"),
        ]
        result = client.batch.execute(operations, atomic=False)

        # Verify the request was made with atomic=False
        request = httpx_mock.get_request()
        assert request is not None
        import json
        body = json.loads(request.content)
        assert body["atomic"] is False

        # Verify partial success result
        assert result.success is False
        assert result.total == 3
        assert result.succeeded == 2
        assert result.failed == 1
        assert result.results[1].success is False
        assert result.results[1].error == "Duplicate entity"

    def test_execute_partial_failure_with_errors(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test batch result includes error messages for failed operations."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/batch",
            json={
                "success": False,
                "total": 2,
                "succeeded": 1,
                "failed": 1,
                "results": [
                    {"success": True, "index": 0},
                    {"success": False, "index": 1, "error": "Invalid entity_type: must be one of [concept, person]"},
                ],
            },
        )

        operations = [
            EntityCreate(name="Valid", entity_type="concept"),
            EntityCreate(name="Invalid", entity_type="not_a_type"),
        ]
        result = client.batch.execute(operations, atomic=False)

        assert result.success is False
        assert result.failed == 1
        assert result.results[1].error == "Invalid entity_type: must be one of [concept, person]"

    def test_execute_empty_operations_list(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test executing an empty batch."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/batch",
            json={
                "success": True,
                "total": 0,
                "succeeded": 0,
                "failed": 0,
                "results": [],
            },
        )

        operations: list = []
        result = client.batch.execute(operations)

        assert result.success is True
        assert result.total == 0
        assert result.all_succeeded is True

    def test_execute_with_entity_attributes(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test batch operations serialize attributes correctly."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/batch",
            json={
                "success": True,
                "total": 1,
                "succeeded": 1,
                "failed": 0,
                "results": [{"success": True, "index": 0}],
            },
        )

        operations = [
            EntityCreate(
                name="React",
                entity_type="library",
                attributes={"version": "18.2", "language": "JavaScript"},
            )
        ]
        client.batch.execute(operations)

        request = httpx_mock.get_request()
        assert request is not None
        import json
        body = json.loads(request.content)
        assert len(body["operations"]) == 1
        assert body["operations"][0]["data"]["attributes"] == {
            "version": "18.2",
            "language": "JavaScript",
        }

    def test_execute_with_hyperedge_members(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test batch operations serialize hyperedge members correctly."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/batch",
            json={
                "success": True,
                "total": 1,
                "succeeded": 1,
                "failed": 0,
                "results": [{"success": True, "index": 0}],
            },
        )

        members = [
            {"entity_id": "e:react", "role": "subject"},
            {"entity_id": "e:hooks", "role": "object"},
            {"entity_id": "e:state", "role": "modifier"},
        ]
        operations = [
            HyperedgeCreate(description="React uses hooks for state", members=members)
        ]
        client.batch.execute(operations)

        request = httpx_mock.get_request()
        assert request is not None
        import json
        body = json.loads(request.content)
        assert body["operations"][0]["data"]["members"] == members


class TestBatchAPIIntegration:
    """Integration tests for BatchAPI with the main client."""

    def test_batch_api_accessible_from_client(self, client: HyperX):
        """Test that BatchAPI is accessible from the HyperX client."""
        assert hasattr(client, "batch")
        assert client.batch is not None

    def test_batch_api_has_execute_method(self, client: HyperX):
        """Test that BatchAPI has an execute method."""
        assert hasattr(client.batch, "execute")
        assert callable(client.batch.execute)


class TestBatchResultParsing:
    """Tests for parsing batch API responses into BatchResult."""

    def test_parse_all_successful(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test parsing a fully successful batch response."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/batch",
            json={
                "success": True,
                "total": 2,
                "succeeded": 2,
                "failed": 0,
                "results": [
                    {"success": True, "index": 0},
                    {"success": True, "index": 1},
                ],
            },
        )

        operations = [
            EntityCreate(name="E1", entity_type="concept"),
            EntityCreate(name="E2", entity_type="concept"),
        ]
        result = client.batch.execute(operations)

        assert isinstance(result, BatchResult)
        assert result.all_succeeded is True
        assert len(result.successful_items) == 2
        assert len(result.failed_items) == 0

    def test_parse_partial_failure(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test parsing a partial failure batch response."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/batch",
            json={
                "success": False,
                "total": 3,
                "succeeded": 1,
                "failed": 2,
                "results": [
                    {"success": True, "index": 0},
                    {"success": False, "index": 1, "error": "Error 1"},
                    {"success": False, "index": 2, "error": "Error 2"},
                ],
            },
        )

        operations = [
            EntityCreate(name="E1", entity_type="concept"),
            EntityCreate(name="E2", entity_type="concept"),
            EntityCreate(name="E3", entity_type="concept"),
        ]
        result = client.batch.execute(operations, atomic=False)

        assert isinstance(result, BatchResult)
        assert result.all_succeeded is False
        assert len(result.successful_items) == 1
        assert len(result.failed_items) == 2
        assert result.failed_items[0].error == "Error 1"
        assert result.failed_items[1].error == "Error 2"
