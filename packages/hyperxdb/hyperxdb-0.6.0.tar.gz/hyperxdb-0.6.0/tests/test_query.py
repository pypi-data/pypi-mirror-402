"""Tests for fluent query builder."""

from datetime import datetime, timezone

import pytest
from pytest_httpx import HTTPXMock

from hyperx import HyperX
from hyperx.query import Query, QueryExecutor, AsyncQueryExecutor, RoleFilter


class TestRoleFilter:
    """Tests for RoleFilter dataclass."""

    def test_role_filter_basic(self):
        """Test basic RoleFilter creation."""
        rf = RoleFilter(role="subject")
        assert rf.role == "subject"
        assert rf.entity is None
        assert rf.entity_type is None

    def test_role_filter_with_entity(self):
        """Test RoleFilter with entity ID."""
        rf = RoleFilter(role="subject", entity="e:react")
        assert rf.role == "subject"
        assert rf.entity == "e:react"
        assert rf.entity_type is None

    def test_role_filter_with_entity_type(self):
        """Test RoleFilter with entity type."""
        rf = RoleFilter(role="author", entity_type="person")
        assert rf.role == "author"
        assert rf.entity is None
        assert rf.entity_type == "person"

    def test_role_filter_full(self):
        """Test RoleFilter with all fields."""
        rf = RoleFilter(role="subject", entity="e:react", entity_type="framework")
        assert rf.role == "subject"
        assert rf.entity == "e:react"
        assert rf.entity_type == "framework"


class TestQueryBuilder:
    """Tests for Query builder."""

    def test_query_default_values(self):
        """Test Query with default values."""
        q = Query()
        d = q.to_dict()
        assert d["limit"] == 100
        assert d["offset"] == 0
        assert "where" not in d
        assert "or_where" not in d
        assert "max_hops" not in d
        assert "as_of" not in d
        assert "text" not in d

    def test_where_basic(self):
        """Test basic where() filter."""
        q = Query().where(role="subject")
        d = q.to_dict()
        assert "where" in d
        assert len(d["where"]) == 1
        assert d["where"][0] == {"role": "subject"}

    def test_where_with_entity(self):
        """Test where() with entity ID."""
        q = Query().where(role="subject", entity="e:react")
        d = q.to_dict()
        assert d["where"][0] == {"role": "subject", "entity": "e:react"}

    def test_where_with_entity_type(self):
        """Test where() with entity type."""
        q = Query().where(role="author", entity_type="person")
        d = q.to_dict()
        assert d["where"][0] == {"role": "author", "entity_type": "person"}

    def test_multiple_where_filters(self):
        """Test multiple where() filters (AND logic)."""
        q = (
            Query()
            .where(role="subject", entity="e:react")
            .where(role="object", entity_type="concept")
        )
        d = q.to_dict()
        assert len(d["where"]) == 2
        assert d["where"][0] == {"role": "subject", "entity": "e:react"}
        assert d["where"][1] == {"role": "object", "entity_type": "concept"}

    def test_or_where_basic(self):
        """Test basic or_where() filter."""
        q = Query().or_where(role="subject", entity="e:vue")
        d = q.to_dict()
        assert "or_where" in d
        assert len(d["or_where"]) == 1
        assert d["or_where"][0] == {"role": "subject", "entity": "e:vue"}

    def test_combined_where_and_or_where(self):
        """Test combining where() and or_where()."""
        q = (
            Query()
            .where(role="subject", entity="e:react")
            .or_where(role="subject", entity="e:vue")
        )
        d = q.to_dict()
        assert len(d["where"]) == 1
        assert len(d["or_where"]) == 1
        assert d["where"][0] == {"role": "subject", "entity": "e:react"}
        assert d["or_where"][0] == {"role": "subject", "entity": "e:vue"}

    def test_with_hops(self):
        """Test with_hops() for graph expansion."""
        q = Query().with_hops(max=2)
        d = q.to_dict()
        assert d["max_hops"] == 2

    def test_limit(self):
        """Test limit() setting."""
        q = Query().limit(50)
        d = q.to_dict()
        assert d["limit"] == 50

    def test_offset(self):
        """Test offset() for pagination."""
        q = Query().offset(20)
        d = q.to_dict()
        assert d["offset"] == 20

    def test_limit_and_offset(self):
        """Test limit() and offset() together for pagination."""
        q = Query().limit(10).offset(30)
        d = q.to_dict()
        assert d["limit"] == 10
        assert d["offset"] == 30

    def test_temporal_with_datetime(self):
        """Test temporal() with datetime object."""
        dt = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        q = Query().temporal(as_of=dt)
        d = q.to_dict()
        assert d["as_of"] == "2026-01-15T12:00:00+00:00"

    def test_temporal_with_string(self):
        """Test temporal() with ISO string."""
        q = Query().temporal(as_of="2026-01-15T12:00:00+00:00")
        d = q.to_dict()
        assert d["as_of"] == "2026-01-15T12:00:00+00:00"

    def test_text_query(self):
        """Test text() for text search."""
        q = Query().text("react state management")
        d = q.to_dict()
        assert d["text"] == "react state management"

    def test_fluent_chaining(self):
        """Test full fluent chaining."""
        q = (
            Query()
            .where(role="subject", entity="e:react")
            .or_where(role="subject", entity="e:vue")
            .with_hops(max=2)
            .text("framework comparison")
            .limit(20)
            .offset(10)
        )
        d = q.to_dict()

        assert d["limit"] == 20
        assert d["offset"] == 10
        assert d["max_hops"] == 2
        assert d["text"] == "framework comparison"
        assert len(d["where"]) == 1
        assert len(d["or_where"]) == 1

    def test_chaining_returns_self(self):
        """Test that all methods return self for chaining."""
        q = Query()
        assert q.where(role="subject") is q
        assert q.or_where(role="object") is q
        assert q.with_hops(max=1) is q
        assert q.limit(10) is q
        assert q.offset(5) is q
        assert q.temporal(as_of="2026-01-01T00:00:00Z") is q
        assert q.text("query") is q


class TestQueryExecutor:
    """Tests for QueryExecutor."""

    def test_executor_execute(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test QueryExecutor.execute() returns SearchResult."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/query",
            json={
                "entities": [
                    {
                        "id": "e:react",
                        "name": "React",
                        "entity_type": "framework",
                        "attributes": {},
                        "confidence": 1.0,
                        "created_at": "2026-01-15T00:00:00Z",
                        "updated_at": "2026-01-15T00:00:00Z",
                    },
                ],
                "hyperedges": [
                    {
                        "id": "h:edge1",
                        "description": "React provides Hooks",
                        "members": [
                            {"entity_id": "e:react", "role": "subject"},
                            {"entity_id": "e:hooks", "role": "object"},
                        ],
                        "attributes": {},
                        "confidence": 1.0,
                        "created_at": "2026-01-15T00:00:00Z",
                        "updated_at": "2026-01-15T00:00:00Z",
                    },
                ],
            },
        )

        query = Query().where(role="subject", entity="e:react").limit(10)
        result = client.query(query).execute()

        assert len(result.entities) == 1
        assert result.entities[0].name == "React"
        assert len(result.hyperedges) == 1
        assert result.hyperedges[0].description == "React provides Hooks"

    def test_executor_sends_correct_payload(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test that QueryExecutor sends correct JSON payload."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/query",
            json={"entities": [], "hyperedges": []},
        )

        query = (
            Query()
            .where(role="subject", entity="e:react")
            .or_where(role="subject", entity="e:vue")
            .with_hops(max=2)
            .limit(20)
            .offset(5)
        )
        client.query(query).execute()

        request = httpx_mock.get_request()
        assert request is not None

        import json
        body = json.loads(request.content)

        assert body["limit"] == 20
        assert body["offset"] == 5
        assert body["max_hops"] == 2
        assert body["where"] == [{"role": "subject", "entity": "e:react"}]
        assert body["or_where"] == [{"role": "subject", "entity": "e:vue"}]


class TestAsyncQueryExecutor:
    """Tests for AsyncQueryExecutor."""

    @pytest.mark.asyncio
    async def test_async_executor_execute(self, httpx_mock: HTTPXMock):
        """Test AsyncQueryExecutor.execute() returns SearchResult."""
        from hyperx import AsyncHyperX

        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/v1/query",
            json={
                "entities": [
                    {
                        "id": "e:vue",
                        "name": "Vue",
                        "entity_type": "framework",
                        "attributes": {},
                        "confidence": 1.0,
                        "created_at": "2026-01-15T00:00:00Z",
                        "updated_at": "2026-01-15T00:00:00Z",
                    },
                ],
                "hyperedges": [],
            },
        )

        async with AsyncHyperX(api_key="hx_sk_test_12345678", base_url="http://localhost:8080") as db:
            query = Query().where(role="subject", entity="e:vue").limit(5)
            result = await db.query(query).execute()

            assert len(result.entities) == 1
            assert result.entities[0].name == "Vue"


class TestClientIntegration:
    """Test client.query() method integration."""

    def test_client_has_query_method(self, client: HyperX):
        """Test that HyperX client has query() method."""
        assert hasattr(client, "query")
        assert callable(client.query)

    def test_query_returns_executor(self, client: HyperX):
        """Test that query() returns a QueryExecutor."""
        q = Query().where(role="subject")
        executor = client.query(q)
        assert isinstance(executor, QueryExecutor)

    @pytest.mark.asyncio
    async def test_async_client_has_query_method(self):
        """Test that AsyncHyperX client has query() method."""
        from hyperx import AsyncHyperX

        async with AsyncHyperX(api_key="hx_sk_test_12345678", base_url="http://localhost:8080") as db:
            assert hasattr(db, "query")
            assert callable(db.query)

    @pytest.mark.asyncio
    async def test_async_query_returns_executor(self):
        """Test that async query() returns an AsyncQueryExecutor."""
        from hyperx import AsyncHyperX

        async with AsyncHyperX(api_key="hx_sk_test_12345678", base_url="http://localhost:8080") as db:
            q = Query().where(role="subject")
            executor = db.query(q)
            assert isinstance(executor, AsyncQueryExecutor)
