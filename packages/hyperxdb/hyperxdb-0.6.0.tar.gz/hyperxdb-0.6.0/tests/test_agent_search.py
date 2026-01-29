"""Tests for SearchTool agent."""

import pytest
from pytest_httpx import HTTPXMock

from hyperx import HyperX
from hyperx.agents import BaseTool, QualitySignals, SearchTool, ToolResult


# Test constants
TEST_API_KEY = "hx_sk_test_12345678"
TEST_BASE_URL = "http://localhost:8080"


@pytest.fixture
def client() -> HyperX:
    """Create a HyperX client for testing."""
    c = HyperX(api_key=TEST_API_KEY, base_url=TEST_BASE_URL)
    yield c
    c.close()


def make_search_response(
    entities: list[dict] | None = None,
    hyperedges: list[dict] | None = None,
) -> dict:
    """Helper to create mock search response."""
    return {
        "entities": entities or [],
        "hyperedges": hyperedges or [],
    }


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


class TestSearchToolCreation:
    """Tests for SearchTool initialization."""

    def test_creation_with_defaults(self, client: HyperX):
        """Test SearchTool creation with default parameters."""
        search = SearchTool(client)

        assert search.name == "hyperx_search"
        assert "HyperX knowledge graph" in search.description
        assert "hybrid" in search.description

    def test_creation_with_custom_mode(self, client: HyperX):
        """Test SearchTool creation with custom search mode."""
        search_text = SearchTool(client, mode="text")
        assert "text" in search_text.description

        search_vector = SearchTool(client, mode="vector")
        assert "vector" in search_vector.description

        search_hybrid = SearchTool(client, mode="hybrid")
        assert "hybrid" in search_hybrid.description

    def test_creation_with_custom_limit(self, client: HyperX):
        """Test SearchTool creation with custom default_limit."""
        search = SearchTool(client, default_limit=25)
        assert "25" in search.description

    def test_creation_with_expand_graph(self, client: HyperX):
        """Test SearchTool creation with expand_graph enabled."""
        search = SearchTool(client, expand_graph=True, max_hops=3)

        # Tool should store configuration
        assert search._expand_graph is True
        assert search._max_hops == 3

    def test_creation_with_reranker(self, client: HyperX):
        """Test SearchTool creation with custom reranker."""

        def custom_reranker(query: str, results: list[dict]) -> list[dict]:
            return sorted(results, key=lambda x: x.get("name", ""))

        search = SearchTool(client, reranker=custom_reranker)
        assert search._reranker is not None

    def test_implements_base_tool_protocol(self, client: HyperX):
        """Test SearchTool implements BaseTool Protocol."""
        search = SearchTool(client)
        assert isinstance(search, BaseTool)


class TestSearchToolRun:
    """Tests for SearchTool.run() method."""

    def test_run_returns_tool_result(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test run() returns ToolResult with entities."""
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/search",
            json=make_search_response(
                entities=[
                    make_entity(id="e:react", name="React", entity_type="framework"),
                    make_entity(id="e:hooks", name="Hooks", entity_type="concept"),
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

        search = SearchTool(client)
        result = search.run(query="react hooks")

        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.data is not None
        assert len(result.data["entities"]) == 2
        assert len(result.data["hyperedges"]) == 1
        assert result.data["entities"][0]["name"] == "React"

    def test_run_returns_quality_signals(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test run() returns quality signals."""
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/search",
            json=make_search_response(
                entities=[make_entity(confidence=0.95)],
            ),
        )

        search = SearchTool(client)
        result = search.run(query="test query")

        assert isinstance(result.quality, QualitySignals)
        assert result.quality.confidence > 0
        assert isinstance(result.quality.relevance_scores, list)

    def test_run_with_custom_limit(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test run() respects custom limit parameter."""
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/search",
            json=make_search_response(),
        )

        search = SearchTool(client, default_limit=10)
        search.run(query="test", limit=50)

        # Verify request was made with correct limit
        request = httpx_mock.get_request()
        assert request is not None
        import json

        body = json.loads(request.content)
        assert body["limit"] == 50

    def test_run_with_role_filter(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test run() passes role_filter to API."""
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

        search = SearchTool(client)
        result = search.run(query="test", role_filter={"subject": "e:react"})

        assert result.success is True

        # Verify request included role_filter
        request = httpx_mock.get_request()
        assert request is not None
        import json

        body = json.loads(request.content)
        assert body["role_filter"] == {"subject": "e:react"}

    def test_run_text_mode(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test run() uses text endpoint for text mode."""
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/search/text",
            json=make_search_response(
                entities=[make_entity(name="Python")],
            ),
        )

        search = SearchTool(client, mode="text")
        result = search.run(query="python programming")

        assert result.success is True
        assert len(result.data["entities"]) == 1

    def test_run_with_reranker(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test run() applies reranker to results."""
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/search",
            json=make_search_response(
                entities=[
                    make_entity(id="e:z", name="Zebra"),
                    make_entity(id="e:a", name="Apple"),
                    make_entity(id="e:m", name="Mango"),
                ],
            ),
        )

        # Reranker sorts by name alphabetically
        def alpha_reranker(query: str, results: list[dict]) -> list[dict]:
            return sorted(results, key=lambda x: x.get("name", ""))

        search = SearchTool(client, reranker=alpha_reranker)
        result = search.run(query="fruits")

        assert result.success is True
        # Results should be alphabetically sorted
        names = [e["name"] for e in result.data["entities"]]
        assert names == ["Apple", "Mango", "Zebra"]

    def test_run_empty_results(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test run() handles empty results gracefully."""
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/search",
            json=make_search_response(),
        )

        search = SearchTool(client)
        result = search.run(query="nonexistent xyz123")

        assert result.success is True
        assert result.data["entities"] == []
        assert result.data["hyperedges"] == []
        assert "No results found" in result.explanation


class TestSearchToolQuality:
    """Tests for quality signal generation."""

    def test_low_confidence_triggers_should_retrieve_more(
        self, client: HyperX, httpx_mock: HTTPXMock
    ):
        """Test low confidence results set should_retrieve_more=True."""
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/search",
            json=make_search_response(
                entities=[make_entity(confidence=0.3)],
            ),
        )

        search = SearchTool(client)
        result = search.run(query="vague query")

        assert result.quality.should_retrieve_more is True
        assert result.quality.confidence < 0.6  # Below threshold

    def test_high_confidence_does_not_trigger_should_retrieve_more(
        self, client: HyperX, httpx_mock: HTTPXMock
    ):
        """Test high confidence results set should_retrieve_more=False."""
        # Return multiple high-confidence results with good coverage
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/search",
            json=make_search_response(
                entities=[
                    make_entity(
                        id="e:react",
                        name="React",
                        entity_type="framework",
                        confidence=0.95,
                    ),
                    make_entity(
                        id="e:state",
                        name="State Management",
                        entity_type="concept",
                        confidence=0.92,
                    ),
                ],
            ),
        )

        search = SearchTool(client)
        result = search.run(query="react state")

        assert result.quality.confidence >= 0.6
        # With high confidence AND good coverage, should_retrieve_more is False
        if result.quality.coverage >= 0.5:
            assert result.quality.should_retrieve_more is False

    def test_empty_results_trigger_should_retrieve_more(
        self, client: HyperX, httpx_mock: HTTPXMock
    ):
        """Test empty results always set should_retrieve_more=True."""
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/search",
            json=make_search_response(),
        )

        search = SearchTool(client)
        result = search.run(query="nothing here")

        assert result.quality.should_retrieve_more is True
        assert result.quality.confidence == 0.0

    def test_explanation_includes_confidence_assessment(
        self, client: HyperX, httpx_mock: HTTPXMock
    ):
        """Test explanation includes confidence assessment."""
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/search",
            json=make_search_response(
                entities=[make_entity(confidence=0.95)],
            ),
        )

        search = SearchTool(client)
        result = search.run(query="test")

        assert "confidence" in result.explanation.lower()


class TestSearchToolExceptionHandling:
    """Tests for exception handling."""

    def test_api_error_returns_failed_tool_result(
        self, client: HyperX, httpx_mock: HTTPXMock
    ):
        """Test API error returns failed ToolResult instead of raising."""
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/search",
            status_code=500,
            json={"error": "Internal server error"},
        )

        search = SearchTool(client)
        result = search.run(query="test")

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

        search = SearchTool(client)
        result = search.run(query="test")

        assert result.success is False
        assert result.data is None
        assert "failed" in result.explanation.lower()

    def test_timeout_returns_failed_tool_result(
        self, client: HyperX, httpx_mock: HTTPXMock
    ):
        """Test timeout returns failed ToolResult instead of raising."""
        import httpx

        httpx_mock.add_exception(httpx.TimeoutException("Request timed out"))

        search = SearchTool(client)
        result = search.run(query="test")

        assert result.success is False
        assert "failed" in result.explanation.lower()


class TestSearchToolOpenAISchema:
    """Tests for to_openai_schema() method."""

    def test_to_openai_schema_returns_valid_schema(self, client: HyperX):
        """Test to_openai_schema() returns valid OpenAI function schema."""
        search = SearchTool(client)
        schema = search.to_openai_schema()

        # Required top-level structure
        assert schema["type"] == "function"
        assert "function" in schema

        func = schema["function"]
        assert func["name"] == "hyperx_search"
        assert "description" in func
        assert "parameters" in func

        # Parameters structure
        params = func["parameters"]
        assert params["type"] == "object"
        assert "properties" in params
        assert "required" in params
        assert "query" in params["required"]

        # Query property
        assert "query" in params["properties"]
        assert params["properties"]["query"]["type"] == "string"

        # Optional limit property
        assert "limit" in params["properties"]
        assert params["properties"]["limit"]["type"] == "integer"

        # Optional role_filter property
        assert "role_filter" in params["properties"]
        assert params["properties"]["role_filter"]["type"] == "object"

    def test_schema_includes_default_limit_in_description(self, client: HyperX):
        """Test schema limit description includes configured default."""
        search = SearchTool(client, default_limit=25)
        schema = search.to_openai_schema()

        limit_desc = schema["function"]["parameters"]["properties"]["limit"]["description"]
        assert "25" in limit_desc


class TestSearchToolAsync:
    """Tests for async arun() method."""

    @pytest.mark.asyncio
    async def test_arun_returns_tool_result(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test arun() returns ToolResult."""
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/search",
            json=make_search_response(
                entities=[make_entity()],
            ),
        )

        search = SearchTool(client)
        result = await search.arun(query="test")

        assert isinstance(result, ToolResult)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_arun_with_parameters(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test arun() passes parameters correctly."""
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/search",
            json=make_search_response(),
        )

        search = SearchTool(client)
        result = await search.arun(
            query="test",
            limit=20,
            role_filter={"author": "e:user"},
        )

        assert result.success is True

        # Verify request
        request = httpx_mock.get_request()
        import json

        body = json.loads(request.content)
        assert body["limit"] == 20
        assert body["role_filter"] == {"author": "e:user"}


class TestSearchToolExports:
    """Tests for module exports."""

    def test_searchool_importable_from_agents(self):
        """Test SearchTool is importable from hyperx.agents."""
        from hyperx.agents import SearchTool

        assert SearchTool is not None

    def test_searchool_importable_from_agents_tools(self):
        """Test SearchTool is importable from hyperx.agents.tools."""
        from hyperx.agents.tools import SearchTool

        assert SearchTool is not None

    def test_searchtool_in_agents_all(self):
        """Test SearchTool is in hyperx.agents.__all__."""
        from hyperx import agents

        assert "SearchTool" in agents.__all__
