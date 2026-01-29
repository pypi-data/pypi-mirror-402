"""Tests for PathsTool agent."""

import pytest
from pytest_httpx import HTTPXMock

from hyperx import HyperX
from hyperx.agents import BaseTool, PathsTool, QualitySignals, ToolResult


# Test constants
TEST_API_KEY = "hx_sk_test_12345678"
TEST_BASE_URL = "http://localhost:8080"


@pytest.fixture
def client() -> HyperX:
    """Create a HyperX client for testing."""
    c = HyperX(api_key=TEST_API_KEY, base_url=TEST_BASE_URL)
    yield c
    c.close()


def make_paths_response(paths: list[dict] | None = None) -> dict:
    """Helper to create mock paths response."""
    return {"paths": paths or []}


def make_path(
    hyperedges: list[str] | None = None,
    bridges: list[list[str]] | None = None,
    cost: float = 0.5,
) -> dict:
    """Helper to create mock path result."""
    return {
        "hyperedges": hyperedges or ["h:1", "h:2"],
        "bridges": bridges or [["e:bridge1"]],
        "cost": cost,
    }


class TestPathsToolCreation:
    """Tests for PathsTool initialization."""

    def test_creation_with_defaults(self, client: HyperX):
        """Test PathsTool creation with default parameters."""
        paths_tool = PathsTool(client)

        assert paths_tool.name == "hyperx_find_paths"
        assert "multi-hop" in paths_tool.description.lower()
        assert "4" in paths_tool.description  # default max_hops
        assert "3" in paths_tool.description  # default k_paths

    def test_creation_with_custom_max_hops(self, client: HyperX):
        """Test PathsTool creation with custom default_max_hops."""
        paths_tool = PathsTool(client, default_max_hops=6)
        assert "6" in paths_tool.description

    def test_creation_with_custom_k_paths(self, client: HyperX):
        """Test PathsTool creation with custom default_k_paths."""
        paths_tool = PathsTool(client, default_k_paths=5)
        assert "5" in paths_tool.description

    def test_creation_with_all_custom_params(self, client: HyperX):
        """Test PathsTool creation with all custom parameters."""
        paths_tool = PathsTool(client, default_max_hops=8, default_k_paths=10)
        assert "8" in paths_tool.description
        assert "10" in paths_tool.description

    def test_implements_base_tool_protocol(self, client: HyperX):
        """Test PathsTool implements BaseTool Protocol."""
        paths_tool = PathsTool(client)
        assert isinstance(paths_tool, BaseTool)


class TestPathsToolRun:
    """Tests for PathsTool.run() method."""

    def test_run_returns_tool_result(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test run() returns ToolResult with paths."""
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/paths",
            json=make_paths_response(
                paths=[
                    make_path(
                        hyperedges=["h:react-hooks", "h:state-management"],
                        bridges=[["e:state"]],
                        cost=0.3,
                    ),
                    make_path(
                        hyperedges=["h:react-context", "h:redux-pattern"],
                        bridges=[["e:global-state"]],
                        cost=0.5,
                    ),
                ],
            ),
        )

        paths_tool = PathsTool(client)
        result = paths_tool.run(from_entity="e:useState", to_entity="e:redux")

        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.data is not None
        assert len(result.data["paths"]) == 2
        assert result.data["paths"][0]["cost"] == 0.3
        assert result.data["paths"][0]["hyperedges"] == ["h:react-hooks", "h:state-management"]

    def test_run_returns_quality_signals(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test run() returns quality signals."""
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/paths",
            json=make_paths_response(
                paths=[make_path(cost=0.2)],
            ),
        )

        paths_tool = PathsTool(client)
        result = paths_tool.run(from_entity="e:a", to_entity="e:b")

        assert isinstance(result.quality, QualitySignals)
        assert result.quality.confidence > 0
        assert isinstance(result.quality.relevance_scores, list)

    def test_run_with_custom_max_hops(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test run() respects custom max_hops parameter."""
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/paths",
            json=make_paths_response(),
        )

        paths_tool = PathsTool(client, default_max_hops=4)
        paths_tool.run(from_entity="e:a", to_entity="e:b", max_hops=8)

        # Verify request was made with correct max_hops
        request = httpx_mock.get_request()
        assert request is not None
        import json

        body = json.loads(request.content)
        assert body["constraints"]["max_hops"] == 8

    def test_run_with_custom_k_paths(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test run() respects custom k_paths parameter."""
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/paths",
            json=make_paths_response(),
        )

        paths_tool = PathsTool(client, default_k_paths=3)
        paths_tool.run(from_entity="e:a", to_entity="e:b", k_paths=10)

        # Verify request was made with correct k_paths
        request = httpx_mock.get_request()
        assert request is not None
        import json

        body = json.loads(request.content)
        assert body["constraints"]["k_paths"] == 10

    def test_run_uses_defaults_when_not_specified(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test run() uses default values when parameters not specified."""
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/paths",
            json=make_paths_response(),
        )

        paths_tool = PathsTool(client, default_max_hops=5, default_k_paths=7)
        paths_tool.run(from_entity="e:a", to_entity="e:b")

        # Verify request used defaults
        request = httpx_mock.get_request()
        assert request is not None
        import json

        body = json.loads(request.content)
        assert body["constraints"]["max_hops"] == 5
        assert body["constraints"]["k_paths"] == 7

    def test_run_empty_results(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test run() handles empty results gracefully."""
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/paths",
            json=make_paths_response(),
        )

        paths_tool = PathsTool(client)
        result = paths_tool.run(from_entity="e:unconnected1", to_entity="e:unconnected2")

        assert result.success is True
        assert result.data["paths"] == []
        assert "No paths found" in result.explanation


class TestPathsToolQuality:
    """Tests for quality signal generation."""

    def test_low_cost_paths_have_high_confidence(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test low-cost paths result in high confidence."""
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/paths",
            json=make_paths_response(
                paths=[
                    make_path(cost=0.1),
                    make_path(cost=0.15),
                    make_path(cost=0.2),
                ],
            ),
        )

        paths_tool = PathsTool(client)
        result = paths_tool.run(from_entity="e:a", to_entity="e:b")

        # Average cost is 0.15, so confidence should be 0.85
        assert result.quality.confidence >= 0.8
        # Low cost = high relevance
        assert all(score >= 0.8 for score in result.quality.relevance_scores)

    def test_high_cost_paths_have_low_confidence(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test high-cost paths result in low confidence."""
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/paths",
            json=make_paths_response(
                paths=[
                    make_path(cost=0.8),
                    make_path(cost=0.9),
                ],
            ),
        )

        paths_tool = PathsTool(client)
        result = paths_tool.run(from_entity="e:a", to_entity="e:b")

        # Average cost is 0.85, so confidence should be 0.15
        assert result.quality.confidence < 0.5
        # High cost = low relevance
        assert all(score < 0.3 for score in result.quality.relevance_scores)

    def test_no_paths_triggers_should_retrieve_more(
        self, client: HyperX, httpx_mock: HTTPXMock
    ):
        """Test empty results set should_retrieve_more=True."""
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/paths",
            json=make_paths_response(),
        )

        paths_tool = PathsTool(client)
        result = paths_tool.run(from_entity="e:a", to_entity="e:b")

        assert result.quality.should_retrieve_more is True
        assert result.quality.confidence == 0.0
        assert "max_hops" in str(result.quality.suggested_refinements)

    def test_low_confidence_triggers_should_retrieve_more(
        self, client: HyperX, httpx_mock: HTTPXMock
    ):
        """Test low confidence results set should_retrieve_more=True."""
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/paths",
            json=make_paths_response(
                paths=[make_path(cost=0.9)],  # Single high-cost path
            ),
        )

        paths_tool = PathsTool(client)
        result = paths_tool.run(from_entity="e:a", to_entity="e:b")

        assert result.quality.should_retrieve_more is True

    def test_high_confidence_does_not_trigger_should_retrieve_more(
        self, client: HyperX, httpx_mock: HTTPXMock
    ):
        """Test high confidence results with multiple paths set should_retrieve_more=False."""
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/paths",
            json=make_paths_response(
                paths=[
                    make_path(cost=0.1),
                    make_path(cost=0.15),
                    make_path(cost=0.2),
                ],
            ),
        )

        paths_tool = PathsTool(client)
        result = paths_tool.run(from_entity="e:a", to_entity="e:b")

        assert result.quality.should_retrieve_more is False

    def test_explanation_includes_confidence_assessment(
        self, client: HyperX, httpx_mock: HTTPXMock
    ):
        """Test explanation includes confidence assessment."""
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/paths",
            json=make_paths_response(
                paths=[make_path(cost=0.2)],
            ),
        )

        paths_tool = PathsTool(client)
        result = paths_tool.run(from_entity="e:a", to_entity="e:b")

        assert "confidence" in result.explanation.lower()


class TestPathsToolExceptionHandling:
    """Tests for exception handling."""

    def test_api_error_returns_failed_tool_result(
        self, client: HyperX, httpx_mock: HTTPXMock
    ):
        """Test API error returns failed ToolResult instead of raising."""
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/paths",
            status_code=500,
            json={"error": "Internal server error"},
        )

        paths_tool = PathsTool(client)
        result = paths_tool.run(from_entity="e:a", to_entity="e:b")

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

        paths_tool = PathsTool(client)
        result = paths_tool.run(from_entity="e:a", to_entity="e:b")

        assert result.success is False
        assert result.data is None
        assert "failed" in result.explanation.lower()

    def test_timeout_returns_failed_tool_result(
        self, client: HyperX, httpx_mock: HTTPXMock
    ):
        """Test timeout returns failed ToolResult instead of raising."""
        import httpx

        httpx_mock.add_exception(httpx.TimeoutException("Request timed out"))

        paths_tool = PathsTool(client)
        result = paths_tool.run(from_entity="e:a", to_entity="e:b")

        assert result.success is False
        assert "failed" in result.explanation.lower()

    def test_exception_includes_suggested_refinements(
        self, client: HyperX, httpx_mock: HTTPXMock
    ):
        """Test exception result includes helpful refinement suggestions."""
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/paths",
            status_code=404,
            json={"error": "Entity not found"},
        )

        paths_tool = PathsTool(client)
        result = paths_tool.run(from_entity="e:nonexistent", to_entity="e:b")

        assert result.success is False
        assert len(result.quality.suggested_refinements) > 0


class TestPathsToolOpenAISchema:
    """Tests for to_openai_schema() method."""

    def test_to_openai_schema_returns_valid_schema(self, client: HyperX):
        """Test to_openai_schema() returns valid OpenAI function schema."""
        paths_tool = PathsTool(client)
        schema = paths_tool.to_openai_schema()

        # Required top-level structure
        assert schema["type"] == "function"
        assert "function" in schema

        func = schema["function"]
        assert func["name"] == "hyperx_find_paths"
        assert "description" in func
        assert "parameters" in func

        # Parameters structure
        params = func["parameters"]
        assert params["type"] == "object"
        assert "properties" in params
        assert "required" in params

    def test_schema_has_from_entity_as_required(self, client: HyperX):
        """Test schema has from_entity as required parameter."""
        paths_tool = PathsTool(client)
        schema = paths_tool.to_openai_schema()

        params = schema["function"]["parameters"]
        assert "from_entity" in params["required"]
        assert "from_entity" in params["properties"]
        assert params["properties"]["from_entity"]["type"] == "string"

    def test_schema_has_to_entity_as_required(self, client: HyperX):
        """Test schema has to_entity as required parameter."""
        paths_tool = PathsTool(client)
        schema = paths_tool.to_openai_schema()

        params = schema["function"]["parameters"]
        assert "to_entity" in params["required"]
        assert "to_entity" in params["properties"]
        assert params["properties"]["to_entity"]["type"] == "string"

    def test_schema_has_optional_max_hops(self, client: HyperX):
        """Test schema has optional max_hops parameter."""
        paths_tool = PathsTool(client)
        schema = paths_tool.to_openai_schema()

        params = schema["function"]["parameters"]
        assert "max_hops" in params["properties"]
        assert "max_hops" not in params["required"]
        assert params["properties"]["max_hops"]["type"] == "integer"

    def test_schema_has_optional_k_paths(self, client: HyperX):
        """Test schema has optional k_paths parameter."""
        paths_tool = PathsTool(client)
        schema = paths_tool.to_openai_schema()

        params = schema["function"]["parameters"]
        assert "k_paths" in params["properties"]
        assert "k_paths" not in params["required"]
        assert params["properties"]["k_paths"]["type"] == "integer"

    def test_schema_includes_default_values_in_description(self, client: HyperX):
        """Test schema descriptions include configured defaults."""
        paths_tool = PathsTool(client, default_max_hops=6, default_k_paths=5)
        schema = paths_tool.to_openai_schema()

        max_hops_desc = schema["function"]["parameters"]["properties"]["max_hops"]["description"]
        assert "6" in max_hops_desc

        k_paths_desc = schema["function"]["parameters"]["properties"]["k_paths"]["description"]
        assert "5" in k_paths_desc


class TestPathsToolAsync:
    """Tests for async arun() method."""

    @pytest.mark.asyncio
    async def test_arun_returns_tool_result(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test arun() returns ToolResult."""
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/paths",
            json=make_paths_response(
                paths=[make_path()],
            ),
        )

        paths_tool = PathsTool(client)
        result = await paths_tool.arun(from_entity="e:a", to_entity="e:b")

        assert isinstance(result, ToolResult)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_arun_with_parameters(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test arun() passes parameters correctly."""
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/paths",
            json=make_paths_response(),
        )

        paths_tool = PathsTool(client)
        result = await paths_tool.arun(
            from_entity="e:useState",
            to_entity="e:redux",
            max_hops=6,
            k_paths=5,
        )

        assert result.success is True

        # Verify request
        request = httpx_mock.get_request()
        import json

        body = json.loads(request.content)
        assert body["from"] == "e:useState"
        assert body["to"] == "e:redux"
        assert body["constraints"]["max_hops"] == 6
        assert body["constraints"]["k_paths"] == 5


class TestPathsToolExports:
    """Tests for module exports."""

    def test_pathstool_importable_from_agents(self):
        """Test PathsTool is importable from hyperx.agents."""
        from hyperx.agents import PathsTool

        assert PathsTool is not None

    def test_pathstool_importable_from_agents_tools(self):
        """Test PathsTool is importable from hyperx.agents.tools."""
        from hyperx.agents.tools import PathsTool

        assert PathsTool is not None

    def test_pathstool_in_agents_all(self):
        """Test PathsTool is in hyperx.agents.__all__."""
        from hyperx import agents

        assert "PathsTool" in agents.__all__
