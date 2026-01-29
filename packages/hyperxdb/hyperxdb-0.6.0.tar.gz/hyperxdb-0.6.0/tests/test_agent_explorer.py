"""Tests for explorer tools (ExplorerTool, ExplainTool, RelationshipsTool)."""

import pytest
from pytest_httpx import HTTPXMock

from hyperx import HyperX
from hyperx.agents import (
    BaseTool,
    ExplainTool,
    ExplorerTool,
    QualitySignals,
    RelationshipsTool,
    ToolResult,
)


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


def make_search_response(
    entities: list[dict] | None = None,
    hyperedges: list[dict] | None = None,
) -> dict:
    """Helper to create mock search response."""
    return {
        "entities": entities or [],
        "hyperedges": hyperedges or [],
    }


# =============================================================================
# ExplorerTool Tests
# =============================================================================


class TestExplorerToolCreation:
    """Tests for ExplorerTool initialization."""

    def test_creation_with_defaults(self, client: HyperX):
        """Test ExplorerTool creation with default parameters."""
        explorer = ExplorerTool(client)

        assert explorer.name == "hyperx_explore"
        assert "neighbors" in explorer.description.lower()
        assert "2" in explorer.description  # default max_hops

    def test_creation_with_custom_max_hops(self, client: HyperX):
        """Test ExplorerTool creation with custom default_max_hops."""
        explorer = ExplorerTool(client, default_max_hops=5)
        assert "5" in explorer.description

    def test_implements_base_tool_protocol(self, client: HyperX):
        """Test ExplorerTool implements BaseTool Protocol."""
        explorer = ExplorerTool(client)
        assert isinstance(explorer, BaseTool)


class TestExplorerToolRun:
    """Tests for ExplorerTool.run() method."""

    def test_run_returns_tool_result(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test run() returns ToolResult with neighbors."""
        # Mock entity lookup
        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/entities/e:react",
            json=make_entity(id="e:react", name="React", entity_type="framework"),
        )
        # Mock search
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/search",
            json=make_search_response(
                entities=[
                    make_entity(id="e:hooks", name="Hooks", entity_type="concept"),
                    make_entity(id="e:state", name="State", entity_type="concept"),
                ],
                hyperedges=[
                    make_hyperedge(
                        id="h:react-hooks",
                        description="React provides Hooks",
                        members=[
                            {"entity_id": "e:react", "role": "subject"},
                            {"entity_id": "e:hooks", "role": "object"},
                        ],
                    ),
                ],
            ),
        )
        # Mock paths.find calls for multi-hop exploration (may be called multiple times)
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/paths",
            json={"paths": []},
        )
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/paths",
            json={"paths": []},
        )

        explorer = ExplorerTool(client)
        result = explorer.run(entity_id="e:react")

        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.data is not None
        assert "entity" in result.data
        assert "neighbors" in result.data
        assert result.data["entity"]["name"] == "React"

    def test_run_returns_quality_signals(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test run() returns quality signals."""
        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/entities/e:react",
            json=make_entity(id="e:react", name="React"),
        )
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/search",
            json=make_search_response(
                entities=[make_entity(id="e:hooks", name="Hooks")],
            ),
        )
        # Mock paths.find call
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/paths",
            json={"paths": []},
        )

        explorer = ExplorerTool(client)
        result = explorer.run(entity_id="e:react")

        assert isinstance(result.quality, QualitySignals)
        assert result.quality.confidence >= 0
        assert isinstance(result.quality.relevance_scores, list)

    def test_run_with_custom_max_hops(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test run() respects custom max_hops parameter."""
        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/entities/e:react",
            json=make_entity(id="e:react", name="React"),
        )
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/search",
            json=make_search_response(
                entities=[make_entity(id="e:hooks", name="Hooks")],
            ),
        )
        # Mock paths.find call
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/paths",
            json={"paths": []},
        )

        explorer = ExplorerTool(client, default_max_hops=2)
        result = explorer.run(entity_id="e:react", max_hops=3)

        assert result.success is True
        # max_hops is mentioned in explanation
        assert "3" in result.explanation

    def test_run_with_entity_type_filter(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test run() filters by entity_types."""
        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/entities/e:react",
            json=make_entity(id="e:react", name="React", entity_type="framework"),
        )
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/search",
            json=make_search_response(
                entities=[
                    make_entity(id="e:hooks", name="Hooks", entity_type="concept"),
                    make_entity(id="e:vue", name="Vue", entity_type="framework"),
                ],
            ),
        )
        # Mock paths.find calls
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/paths",
            json={"paths": []},
        )
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/paths",
            json={"paths": []},
        )

        explorer = ExplorerTool(client)
        result = explorer.run(entity_id="e:react", entity_types=["concept"])

        assert result.success is True
        # Only concept types should be in neighbors
        for neighbor in result.data["neighbors"]:
            assert neighbor["entity_type"] == "concept"

    def test_run_empty_neighbors(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test run() handles no neighbors gracefully."""
        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/entities/e:isolated",
            json=make_entity(id="e:isolated", name="Isolated"),
        )
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/search",
            json=make_search_response(),
        )

        explorer = ExplorerTool(client)
        result = explorer.run(entity_id="e:isolated")

        assert result.success is True
        assert result.data["neighbors"] == []
        assert "No neighbors found" in result.explanation
        assert result.quality.should_retrieve_more is True


class TestExplorerToolExceptionHandling:
    """Tests for exception handling."""

    def test_not_found_returns_failed_tool_result(
        self, client: HyperX, httpx_mock: HTTPXMock
    ):
        """Test entity not found returns failed ToolResult."""
        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/entities/e:nonexistent",
            status_code=404,
            json={"error": "Entity not found"},
        )

        explorer = ExplorerTool(client)
        result = explorer.run(entity_id="e:nonexistent")

        assert result.success is False
        assert result.data is None
        assert "not found" in result.explanation.lower()

    def test_api_error_returns_failed_tool_result(
        self, client: HyperX, httpx_mock: HTTPXMock
    ):
        """Test API error returns failed ToolResult."""
        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/entities/e:test",
            status_code=500,
            json={"error": "Internal server error"},
        )

        explorer = ExplorerTool(client)
        result = explorer.run(entity_id="e:test")

        assert result.success is False
        assert "failed" in result.explanation.lower()


class TestExplorerToolOpenAISchema:
    """Tests for to_openai_schema() method."""

    def test_to_openai_schema_returns_valid_schema(self, client: HyperX):
        """Test to_openai_schema() returns valid OpenAI function schema."""
        explorer = ExplorerTool(client)
        schema = explorer.to_openai_schema()

        # Required top-level structure
        assert schema["type"] == "function"
        assert "function" in schema

        func = schema["function"]
        assert func["name"] == "hyperx_explore"
        assert "description" in func
        assert "parameters" in func

        # Parameters structure
        params = func["parameters"]
        assert params["type"] == "object"
        assert "properties" in params
        assert "required" in params
        assert "entity_id" in params["required"]

        # entity_id property
        assert "entity_id" in params["properties"]
        assert params["properties"]["entity_id"]["type"] == "string"

        # max_hops property
        assert "max_hops" in params["properties"]
        assert params["properties"]["max_hops"]["type"] == "integer"

        # entity_types property
        assert "entity_types" in params["properties"]
        assert params["properties"]["entity_types"]["type"] == "array"


class TestExplorerToolAsync:
    """Tests for async arun() method."""

    @pytest.mark.asyncio
    async def test_arun_returns_tool_result(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test arun() returns ToolResult."""
        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/entities/e:test",
            json=make_entity(id="e:test"),
        )
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/search",
            json=make_search_response(),
        )

        explorer = ExplorerTool(client)
        result = await explorer.arun(entity_id="e:test")

        assert isinstance(result, ToolResult)


# =============================================================================
# ExplainTool Tests
# =============================================================================


class TestExplainToolCreation:
    """Tests for ExplainTool initialization."""

    def test_creation(self, client: HyperX):
        """Test ExplainTool creation."""
        explain = ExplainTool(client)

        assert explain.name == "hyperx_explain"
        assert "explanation" in explain.description.lower() or "explain" in explain.description.lower()

    def test_implements_base_tool_protocol(self, client: HyperX):
        """Test ExplainTool implements BaseTool Protocol."""
        explain = ExplainTool(client)
        assert isinstance(explain, BaseTool)


class TestExplainToolRun:
    """Tests for ExplainTool.run() method."""

    def test_run_returns_tool_result(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test run() returns ToolResult with narrative."""
        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/hyperedges/h:react-hooks",
            json=make_hyperedge(
                id="h:react-hooks",
                description="React provides Hooks",
                members=[
                    {"entity_id": "e:react", "role": "subject"},
                    {"entity_id": "e:hooks", "role": "object"},
                ],
            ),
        )

        explain = ExplainTool(client)
        result = explain.run(ids=["h:react-hooks"])

        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.data is not None
        assert "hyperedges" in result.data
        assert "narrative" in result.data
        assert "React provides Hooks" in result.data["narrative"]

    def test_run_with_multiple_ids(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test run() handles multiple hyperedge IDs."""
        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/hyperedges/h:react-hooks",
            json=make_hyperedge(id="h:react-hooks", description="React provides Hooks"),
        )
        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/hyperedges/h:hooks-state",
            json=make_hyperedge(id="h:hooks-state", description="Hooks manage State"),
        )

        explain = ExplainTool(client)
        result = explain.run(ids=["h:react-hooks", "h:hooks-state"])

        assert result.success is True
        assert len(result.data["hyperedges"]) == 2
        assert "React provides Hooks" in result.data["narrative"]
        assert "hooks manage state" in result.data["narrative"].lower()

    def test_run_with_entity_id(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test run() handles entity IDs."""
        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/entities/e:react",
            json=make_entity(id="e:react", name="React", entity_type="framework"),
        )

        explain = ExplainTool(client)
        result = explain.run(ids=["e:react"])

        assert result.success is True
        assert len(result.data["hyperedges"]) == 1
        assert "React" in result.data["narrative"]

    def test_run_with_empty_ids(self, client: HyperX):
        """Test run() with empty IDs list."""
        explain = ExplainTool(client)
        result = explain.run(ids=[])

        assert result.success is False
        assert "No IDs provided" in result.explanation

    def test_run_returns_quality_signals(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test run() returns quality signals."""
        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/hyperedges/h:test",
            json=make_hyperedge(id="h:test"),
        )

        explain = ExplainTool(client)
        result = explain.run(ids=["h:test"])

        assert isinstance(result.quality, QualitySignals)
        assert result.quality.confidence >= 0

    def test_run_with_some_ids_not_found(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test run() handles partial failures gracefully."""
        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/hyperedges/h:found",
            json=make_hyperedge(id="h:found", description="Found relationship"),
        )
        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/hyperedges/h:missing",
            status_code=404,
            json={"error": "Not found"},
        )

        explain = ExplainTool(client)
        result = explain.run(ids=["h:found", "h:missing"])

        assert result.success is True
        assert len(result.data["hyperedges"]) == 1
        assert "h:missing" in result.data["failed_ids"]
        assert result.quality.should_retrieve_more is True


class TestExplainToolExceptionHandling:
    """Tests for exception handling."""

    def test_all_ids_not_found_returns_failed(
        self, client: HyperX, httpx_mock: HTTPXMock
    ):
        """Test all IDs not found returns failed ToolResult."""
        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/hyperedges/h:missing",
            status_code=404,
            json={"error": "Not found"},
        )

        explain = ExplainTool(client)
        result = explain.run(ids=["h:missing"])

        assert result.success is False
        # The explanation mentions the IDs were not found
        assert "found" in result.explanation.lower()


class TestExplainToolOpenAISchema:
    """Tests for to_openai_schema() method."""

    def test_to_openai_schema_returns_valid_schema(self, client: HyperX):
        """Test to_openai_schema() returns valid OpenAI function schema."""
        explain = ExplainTool(client)
        schema = explain.to_openai_schema()

        # Required top-level structure
        assert schema["type"] == "function"
        assert "function" in schema

        func = schema["function"]
        assert func["name"] == "hyperx_explain"
        assert "description" in func
        assert "parameters" in func

        # Parameters structure
        params = func["parameters"]
        assert params["type"] == "object"
        assert "properties" in params
        assert "required" in params
        assert "ids" in params["required"]

        # ids property
        assert "ids" in params["properties"]
        assert params["properties"]["ids"]["type"] == "array"


class TestExplainToolAsync:
    """Tests for async arun() method."""

    @pytest.mark.asyncio
    async def test_arun_returns_tool_result(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test arun() returns ToolResult."""
        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/hyperedges/h:test",
            json=make_hyperedge(id="h:test"),
        )

        explain = ExplainTool(client)
        result = await explain.arun(ids=["h:test"])

        assert isinstance(result, ToolResult)
        assert result.success is True


# =============================================================================
# RelationshipsTool Tests
# =============================================================================


class TestRelationshipsToolCreation:
    """Tests for RelationshipsTool initialization."""

    def test_creation(self, client: HyperX):
        """Test RelationshipsTool creation."""
        relationships = RelationshipsTool(client)

        assert relationships.name == "hyperx_relationships"
        assert "relationship" in relationships.description.lower()
        assert "role" in relationships.description.lower()

    def test_implements_base_tool_protocol(self, client: HyperX):
        """Test RelationshipsTool implements BaseTool Protocol."""
        relationships = RelationshipsTool(client)
        assert isinstance(relationships, BaseTool)


class TestRelationshipsToolRun:
    """Tests for RelationshipsTool.run() method."""

    def test_run_returns_tool_result(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test run() returns ToolResult with relationships."""
        # Mock entity lookup
        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/entities/e:react",
            json=make_entity(id="e:react", name="React", entity_type="framework"),
        )
        # Mock search
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/search",
            json=make_search_response(
                hyperedges=[
                    make_hyperedge(
                        id="h:react-hooks",
                        description="React provides Hooks",
                        members=[
                            {"entity_id": "e:react", "role": "subject"},
                            {"entity_id": "e:hooks", "role": "object"},
                        ],
                    ),
                ],
            ),
        )

        relationships = RelationshipsTool(client)
        result = relationships.run(entity_id="e:react")

        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.data is not None
        assert "entity" in result.data
        assert "relationships" in result.data
        assert result.data["entity"]["name"] == "React"
        assert len(result.data["relationships"]) >= 1

    def test_run_returns_quality_signals(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test run() returns quality signals."""
        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/entities/e:react",
            json=make_entity(id="e:react", name="React"),
        )
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/search",
            json=make_search_response(
                hyperedges=[
                    make_hyperedge(
                        members=[{"entity_id": "e:react", "role": "subject"}],
                    ),
                ],
            ),
        )

        relationships = RelationshipsTool(client)
        result = relationships.run(entity_id="e:react")

        assert isinstance(result.quality, QualitySignals)
        assert result.quality.confidence >= 0

    def test_run_with_role_filter(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test run() respects role filter."""
        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/entities/e:react",
            json=make_entity(id="e:react", name="React"),
        )
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/search",
            json=make_search_response(
                hyperedges=[
                    make_hyperedge(
                        id="h:react-subject",
                        description="React is subject",
                        members=[{"entity_id": "e:react", "role": "subject"}],
                    ),
                    make_hyperedge(
                        id="h:react-object",
                        description="React is object",
                        members=[{"entity_id": "e:react", "role": "object"}],
                    ),
                ],
            ),
        )

        relationships = RelationshipsTool(client)
        result = relationships.run(entity_id="e:react", role="subject")

        assert result.success is True
        # Only relationships where entity is subject should be returned
        for rel in result.data["relationships"]:
            assert rel["entity_role"] == "subject"

    def test_run_empty_relationships(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test run() handles no relationships gracefully."""
        import re

        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/entities/e:isolated",
            json=make_entity(id="e:isolated", name="Isolated"),
        )
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/search",
            json=make_search_response(),
        )
        # Match the hyperedges list endpoint with query params
        httpx_mock.add_response(
            method="GET",
            url=re.compile(rf"{TEST_BASE_URL}/v1/hyperedges\?.*"),
            json=[],
        )

        relationships = RelationshipsTool(client)
        result = relationships.run(entity_id="e:isolated")

        assert result.success is True
        assert result.data["relationships"] == []
        assert "No relationships found" in result.explanation


class TestRelationshipsToolExceptionHandling:
    """Tests for exception handling."""

    def test_not_found_returns_failed_tool_result(
        self, client: HyperX, httpx_mock: HTTPXMock
    ):
        """Test entity not found returns failed ToolResult."""
        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/entities/e:nonexistent",
            status_code=404,
            json={"error": "Entity not found"},
        )

        relationships = RelationshipsTool(client)
        result = relationships.run(entity_id="e:nonexistent")

        assert result.success is False
        assert result.data is None
        assert "not found" in result.explanation.lower()

    def test_api_error_returns_failed_tool_result(
        self, client: HyperX, httpx_mock: HTTPXMock
    ):
        """Test API error returns failed ToolResult."""
        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/entities/e:test",
            status_code=500,
            json={"error": "Internal server error"},
        )

        relationships = RelationshipsTool(client)
        result = relationships.run(entity_id="e:test")

        assert result.success is False
        assert "failed" in result.explanation.lower()


class TestRelationshipsToolOpenAISchema:
    """Tests for to_openai_schema() method."""

    def test_to_openai_schema_returns_valid_schema(self, client: HyperX):
        """Test to_openai_schema() returns valid OpenAI function schema."""
        relationships = RelationshipsTool(client)
        schema = relationships.to_openai_schema()

        # Required top-level structure
        assert schema["type"] == "function"
        assert "function" in schema

        func = schema["function"]
        assert func["name"] == "hyperx_relationships"
        assert "description" in func
        assert "parameters" in func

        # Parameters structure
        params = func["parameters"]
        assert params["type"] == "object"
        assert "properties" in params
        assert "required" in params
        assert "entity_id" in params["required"]

        # entity_id property
        assert "entity_id" in params["properties"]
        assert params["properties"]["entity_id"]["type"] == "string"

        # role property (optional)
        assert "role" in params["properties"]
        assert params["properties"]["role"]["type"] == "string"
        assert "role" not in params["required"]


class TestRelationshipsToolAsync:
    """Tests for async arun() method."""

    @pytest.mark.asyncio
    async def test_arun_returns_tool_result(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test arun() returns ToolResult."""
        import re

        httpx_mock.add_response(
            method="GET",
            url=f"{TEST_BASE_URL}/v1/entities/e:test",
            json=make_entity(id="e:test"),
        )
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/search",
            json=make_search_response(),
        )
        # Match the hyperedges list endpoint with query params
        httpx_mock.add_response(
            method="GET",
            url=re.compile(rf"{TEST_BASE_URL}/v1/hyperedges\?.*"),
            json=[],
        )

        relationships = RelationshipsTool(client)
        result = await relationships.arun(entity_id="e:test")

        assert isinstance(result, ToolResult)


# =============================================================================
# Module Export Tests
# =============================================================================


class TestExplorerToolExports:
    """Tests for module exports."""

    def test_explorertool_importable_from_agents(self):
        """Test ExplorerTool is importable from hyperx.agents."""
        from hyperx.agents import ExplorerTool

        assert ExplorerTool is not None

    def test_explorertool_importable_from_agents_tools(self):
        """Test ExplorerTool is importable from hyperx.agents.tools."""
        from hyperx.agents.tools import ExplorerTool

        assert ExplorerTool is not None

    def test_explorertool_in_agents_all(self):
        """Test ExplorerTool is in hyperx.agents.__all__."""
        from hyperx import agents

        assert "ExplorerTool" in agents.__all__


class TestExplainToolExports:
    """Tests for module exports."""

    def test_explaintool_importable_from_agents(self):
        """Test ExplainTool is importable from hyperx.agents."""
        from hyperx.agents import ExplainTool

        assert ExplainTool is not None

    def test_explaintool_importable_from_agents_tools(self):
        """Test ExplainTool is importable from hyperx.agents.tools."""
        from hyperx.agents.tools import ExplainTool

        assert ExplainTool is not None

    def test_explaintool_in_agents_all(self):
        """Test ExplainTool is in hyperx.agents.__all__."""
        from hyperx import agents

        assert "ExplainTool" in agents.__all__


class TestRelationshipsToolExports:
    """Tests for module exports."""

    def test_relationshipstool_importable_from_agents(self):
        """Test RelationshipsTool is importable from hyperx.agents."""
        from hyperx.agents import RelationshipsTool

        assert RelationshipsTool is not None

    def test_relationshipstool_importable_from_agents_tools(self):
        """Test RelationshipsTool is importable from hyperx.agents.tools."""
        from hyperx.agents.tools import RelationshipsTool

        assert RelationshipsTool is not None

    def test_relationshipstool_in_agents_all(self):
        """Test RelationshipsTool is in hyperx.agents.__all__."""
        from hyperx import agents

        assert "RelationshipsTool" in agents.__all__
