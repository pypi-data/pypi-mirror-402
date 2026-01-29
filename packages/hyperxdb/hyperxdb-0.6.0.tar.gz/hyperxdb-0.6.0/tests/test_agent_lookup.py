"""Tests for LookupTool agent."""

import pytest
from pytest_httpx import HTTPXMock

from hyperx import HyperX
from hyperx.agents import BaseTool, LookupTool, QualitySignals, ToolResult


# Test constants
TEST_API_KEY = "hx_sk_test_12345678"
TEST_BASE_URL = "http://localhost:8080"


@pytest.fixture
def client() -> HyperX:
    """Create a HyperX client for testing."""
    c = HyperX(api_key=TEST_API_KEY, base_url=TEST_BASE_URL)
    yield c
    c.close()


def make_entity(
    id: str = "e:test",
    name: str = "Test Entity",
    entity_type: str = "concept",
    confidence: float = 0.9,
) -> dict:
    """Helper to create mock entity."""
    return {
        "id": id,
        "name": name,
        "entity_type": entity_type,
        "attributes": {},
        "confidence": confidence,
        "created_at": "2026-01-15T00:00:00Z",
        "updated_at": "2026-01-15T00:00:00Z",
    }


def make_hyperedge(
    id: str = "h:test",
    description: str = "Test relationship",
    members: list[dict] | None = None,
    confidence: float = 0.85,
) -> dict:
    """Helper to create mock hyperedge."""
    return {
        "id": id,
        "description": description,
        "members": members or [{"entity_id": "e:test", "role": "subject"}],
        "attributes": {},
        "confidence": confidence,
        "created_at": "2026-01-15T00:00:00Z",
        "updated_at": "2026-01-15T00:00:00Z",
    }


class TestLookupToolCreation:
    """Tests for LookupTool initialization."""

    def test_creation(self, client: HyperX):
        """Test LookupTool creation."""
        lookup = LookupTool(client)

        assert lookup.name == "hyperx_lookup"
        assert "entity" in lookup.description.lower()
        assert "hyperedge" in lookup.description.lower()
        assert "ID" in lookup.description

    def test_description_mentions_prefix(self, client: HyperX):
        """Test description mentions the h: prefix for hyperedges."""
        lookup = LookupTool(client)
        assert "h:" in lookup.description

    def test_implements_base_tool_protocol(self, client: HyperX):
        """Test LookupTool implements BaseTool Protocol."""
        lookup = LookupTool(client)
        assert isinstance(lookup, BaseTool)


class TestLookupToolEntityRetrieval:
    """Tests for entity lookup."""

    def test_lookup_entity_by_id(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test lookup entity by ID (e:123)."""
        entity_data = make_entity(id="e:123", name="React", entity_type="framework")
        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/entities/e:123",
            json=entity_data,
        )

        lookup = LookupTool(client)
        result = lookup.run(id="e:123")

        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.data is not None
        assert result.data["id"] == "e:123"
        assert result.data["name"] == "React"
        assert result.data["entity_type"] == "framework"

    def test_lookup_entity_returns_model_dump(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test lookup returns entity as model_dump() dict."""
        entity_data = make_entity(
            id="e:test",
            name="Test",
            entity_type="concept",
        )
        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/entities/e:test",
            json=entity_data,
        )

        lookup = LookupTool(client)
        result = lookup.run(id="e:test")

        assert result.success is True
        assert isinstance(result.data, dict)
        # Check it has all expected keys from model_dump
        assert "id" in result.data
        assert "name" in result.data
        assert "entity_type" in result.data
        assert "attributes" in result.data

    def test_lookup_entity_quality_signals(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test lookup entity returns correct quality signals."""
        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/entities/e:123",
            json=make_entity(id="e:123"),
        )

        lookup = LookupTool(client)
        result = lookup.run(id="e:123")

        assert isinstance(result.quality, QualitySignals)
        # Direct lookup is always confident
        assert result.quality.confidence == 1.0
        # No need to retrieve more
        assert result.quality.should_retrieve_more is False
        # Relevance is perfect
        assert result.quality.relevance_scores == [1.0]


class TestLookupToolHyperedgeRetrieval:
    """Tests for hyperedge lookup."""

    def test_lookup_hyperedge_by_id(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test lookup hyperedge by ID (h:456)."""
        hyperedge_data = make_hyperedge(
            id="h:456",
            description="React provides Hooks",
            members=[
                {"entity_id": "e:react", "role": "subject"},
                {"entity_id": "e:hooks", "role": "object"},
            ],
        )
        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/hyperedges/h:456",
            json=hyperedge_data,
        )

        lookup = LookupTool(client)
        result = lookup.run(id="h:456")

        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.data is not None
        assert result.data["id"] == "h:456"
        assert result.data["description"] == "React provides Hooks"
        assert len(result.data["members"]) == 2

    def test_lookup_hyperedge_returns_model_dump(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test lookup returns hyperedge as model_dump() dict."""
        hyperedge_data = make_hyperedge(id="h:test")
        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/hyperedges/h:test",
            json=hyperedge_data,
        )

        lookup = LookupTool(client)
        result = lookup.run(id="h:test")

        assert result.success is True
        assert isinstance(result.data, dict)
        # Check it has all expected keys from model_dump
        assert "id" in result.data
        assert "description" in result.data
        assert "members" in result.data
        assert "attributes" in result.data

    def test_lookup_hyperedge_quality_signals(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test lookup hyperedge returns correct quality signals."""
        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/hyperedges/h:456",
            json=make_hyperedge(id="h:456"),
        )

        lookup = LookupTool(client)
        result = lookup.run(id="h:456")

        assert isinstance(result.quality, QualitySignals)
        # Direct lookup is always confident
        assert result.quality.confidence == 1.0
        # No need to retrieve more
        assert result.quality.should_retrieve_more is False


class TestLookupToolNotFound:
    """Tests for not found handling."""

    def test_not_found_entity_returns_failed_tool_result(
        self, client: HyperX, httpx_mock: HTTPXMock
    ):
        """Test not found entity returns failed ToolResult."""
        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/entities/e:nonexistent",
            status_code=404,
            json={"error": "Entity not found"},
        )

        lookup = LookupTool(client)
        result = lookup.run(id="e:nonexistent")

        assert result.success is False
        assert result.data is None
        assert "not found" in result.explanation.lower()

    def test_not_found_hyperedge_returns_failed_tool_result(
        self, client: HyperX, httpx_mock: HTTPXMock
    ):
        """Test not found hyperedge returns failed ToolResult."""
        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/hyperedges/h:nonexistent",
            status_code=404,
            json={"error": "Hyperedge not found"},
        )

        lookup = LookupTool(client)
        result = lookup.run(id="h:nonexistent")

        assert result.success is False
        assert result.data is None
        assert "not found" in result.explanation.lower()

    def test_not_found_quality_signals(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test not found returns appropriate quality signals."""
        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/entities/e:nonexistent",
            status_code=404,
            json={"error": "Entity not found"},
        )

        lookup = LookupTool(client)
        result = lookup.run(id="e:nonexistent")

        assert result.quality.confidence == 0.0
        assert result.quality.should_retrieve_more is True
        assert len(result.quality.missing_context_hints) > 0


class TestLookupToolExceptionHandling:
    """Tests for exception handling."""

    def test_api_error_returns_failed_tool_result(
        self, client: HyperX, httpx_mock: HTTPXMock
    ):
        """Test API error returns failed ToolResult instead of raising."""
        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/entities/e:test",
            status_code=500,
            json={"error": "Internal server error"},
        )

        lookup = LookupTool(client)
        result = lookup.run(id="e:test")

        assert result.success is False
        assert result.data is None
        assert "failed" in result.explanation.lower()
        assert result.quality.should_retrieve_more is True

    def test_network_error_returns_failed_tool_result(
        self, client: HyperX, httpx_mock: HTTPXMock
    ):
        """Test network error returns failed ToolResult instead of raising."""
        import httpx

        httpx_mock.add_exception(httpx.ConnectError("Connection refused"))

        lookup = LookupTool(client)
        result = lookup.run(id="e:test")

        assert result.success is False
        assert result.data is None
        assert "failed" in result.explanation.lower()

    def test_timeout_returns_failed_tool_result(
        self, client: HyperX, httpx_mock: HTTPXMock
    ):
        """Test timeout returns failed ToolResult instead of raising."""
        import httpx

        httpx_mock.add_exception(httpx.TimeoutException("Request timed out"))

        lookup = LookupTool(client)
        result = lookup.run(id="e:test")

        assert result.success is False
        assert "failed" in result.explanation.lower()


class TestLookupToolOpenAISchema:
    """Tests for to_openai_schema() method."""

    def test_to_openai_schema_returns_valid_schema(self, client: HyperX):
        """Test to_openai_schema() returns valid OpenAI function schema."""
        lookup = LookupTool(client)
        schema = lookup.to_openai_schema()

        # Required top-level structure
        assert schema["type"] == "function"
        assert "function" in schema

        func = schema["function"]
        assert func["name"] == "hyperx_lookup"
        assert "description" in func
        assert "parameters" in func

        # Parameters structure
        params = func["parameters"]
        assert params["type"] == "object"
        assert "properties" in params
        assert "required" in params

    def test_schema_has_id_as_required(self, client: HyperX):
        """Test to_openai_schema() has required 'id' parameter."""
        lookup = LookupTool(client)
        schema = lookup.to_openai_schema()

        params = schema["function"]["parameters"]
        assert "id" in params["required"]
        assert "id" in params["properties"]
        assert params["properties"]["id"]["type"] == "string"

    def test_schema_id_description_mentions_prefix(self, client: HyperX):
        """Test schema id description mentions the prefix convention."""
        lookup = LookupTool(client)
        schema = lookup.to_openai_schema()

        id_desc = schema["function"]["parameters"]["properties"]["id"]["description"]
        assert "h:" in id_desc
        assert "e:" in id_desc


class TestLookupToolAsync:
    """Tests for async arun() method."""

    @pytest.mark.asyncio
    async def test_arun_returns_tool_result(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test arun() returns ToolResult."""
        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/entities/e:test",
            json=make_entity(id="e:test"),
        )

        lookup = LookupTool(client)
        result = await lookup.arun(id="e:test")

        assert isinstance(result, ToolResult)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_arun_with_hyperedge(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test arun() works with hyperedge IDs."""
        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/hyperedges/h:test",
            json=make_hyperedge(id="h:test"),
        )

        lookup = LookupTool(client)
        result = await lookup.arun(id="h:test")

        assert result.success is True
        assert result.data["id"] == "h:test"


class TestLookupToolExports:
    """Tests for module exports."""

    def test_lookuptool_importable_from_agents(self):
        """Test LookupTool is importable from hyperx.agents."""
        from hyperx.agents import LookupTool

        assert LookupTool is not None

    def test_lookuptool_importable_from_agents_tools(self):
        """Test LookupTool is importable from hyperx.agents.tools."""
        from hyperx.agents.tools import LookupTool

        assert LookupTool is not None

    def test_lookuptool_in_agents_all(self):
        """Test LookupTool is in hyperx.agents.__all__."""
        from hyperx import agents

        assert "LookupTool" in agents.__all__
