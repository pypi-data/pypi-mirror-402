"""Tests for agent tool factory and ToolCollection."""

from unittest.mock import MagicMock

import pytest

from hyperx.agents import (
    LookupTool,
    SearchTool,
    ToolCollection,
    ToolResult,
    create_tools,
)


@pytest.fixture
def mock_client():
    """Create a mock HyperX client."""
    client = MagicMock()
    return client


class TestToolCollection:
    """Tests for ToolCollection class."""

    def test_iteration(self, mock_client):
        """ToolCollection supports iteration."""
        search = SearchTool(mock_client)
        lookup = LookupTool(mock_client)
        collection = ToolCollection([search, lookup])

        tools = list(collection)
        assert len(tools) == 2
        assert search in tools
        assert lookup in tools

    def test_len(self, mock_client):
        """ToolCollection supports len()."""
        search = SearchTool(mock_client)
        lookup = LookupTool(mock_client)
        collection = ToolCollection([search, lookup])

        assert len(collection) == 2

    def test_names_property(self, mock_client):
        """ToolCollection.names returns list of tool names."""
        search = SearchTool(mock_client)
        lookup = LookupTool(mock_client)
        collection = ToolCollection([search, lookup])

        names = collection.names
        assert "hyperx_search" in names
        assert "hyperx_lookup" in names
        assert len(names) == 2

    def test_schemas_property(self, mock_client):
        """ToolCollection.schemas returns list of OpenAI schemas."""
        search = SearchTool(mock_client)
        lookup = LookupTool(mock_client)
        collection = ToolCollection([search, lookup])

        schemas = collection.schemas
        assert len(schemas) == 2
        assert all(s["type"] == "function" for s in schemas)
        names = [s["function"]["name"] for s in schemas]
        assert "hyperx_search" in names
        assert "hyperx_lookup" in names

    def test_get_tool_by_name(self, mock_client):
        """ToolCollection.get() returns tool by name."""
        search = SearchTool(mock_client)
        lookup = LookupTool(mock_client)
        collection = ToolCollection([search, lookup])

        tool = collection.get("hyperx_search")
        assert tool is search

        tool = collection.get("hyperx_lookup")
        assert tool is lookup

    def test_get_raises_keyerror_for_unknown_tool(self, mock_client):
        """ToolCollection.get() raises KeyError for unknown tool."""
        search = SearchTool(mock_client)
        collection = ToolCollection([search])

        with pytest.raises(KeyError, match="unknown_tool"):
            collection.get("unknown_tool")

    def test_execute_calls_tool_run(self, mock_client):
        """ToolCollection.execute() calls the tool's run method."""
        # Setup mock search result
        mock_search_result = MagicMock()
        mock_search_result.entities = []
        mock_search_result.hyperedges = []
        mock_client.search.return_value = mock_search_result

        search = SearchTool(mock_client)
        collection = ToolCollection([search])

        result = collection.execute("hyperx_search", query="test query")

        assert isinstance(result, ToolResult)

    def test_execute_raises_keyerror_for_unknown_tool(self, mock_client):
        """ToolCollection.execute() raises KeyError for unknown tool."""
        search = SearchTool(mock_client)
        collection = ToolCollection([search])

        with pytest.raises(KeyError, match="unknown_tool"):
            collection.execute("unknown_tool", query="test")

    def test_contains(self, mock_client):
        """ToolCollection supports 'in' operator."""
        search = SearchTool(mock_client)
        collection = ToolCollection([search])

        assert "hyperx_search" in collection
        assert "unknown_tool" not in collection


class TestCreateToolsReadLevel:
    """Tests for create_tools() with read access level."""

    def test_read_level_returns_correct_tools(self, mock_client):
        """Read level returns SearchTool, PathsTool, LookupTool."""
        tools = create_tools(mock_client, level="read")

        names = tools.names
        assert "hyperx_search" in names
        assert "hyperx_find_paths" in names
        assert "hyperx_lookup" in names
        assert len(names) == 3

    def test_read_level_is_default(self, mock_client):
        """Read level is the default when no level specified."""
        tools = create_tools(mock_client)

        names = tools.names
        assert "hyperx_search" in names
        assert "hyperx_find_paths" in names
        assert "hyperx_lookup" in names
        assert len(names) == 3

    def test_read_level_excludes_explore_tools(self, mock_client):
        """Read level does not include explore-level tools."""
        tools = create_tools(mock_client, level="read")

        names = tools.names
        assert "hyperx_explore" not in names
        assert "hyperx_explain" not in names
        assert "hyperx_relationships" not in names

    def test_read_level_excludes_crud_tools(self, mock_client):
        """Read level does not include CRUD tools."""
        tools = create_tools(mock_client, level="read")

        names = tools.names
        assert "hyperx_entity" not in names
        assert "hyperx_hyperedge" not in names


class TestCreateToolsExploreLevel:
    """Tests for create_tools() with explore access level."""

    def test_explore_level_includes_read_tools(self, mock_client):
        """Explore level includes all read-level tools."""
        tools = create_tools(mock_client, level="explore")

        names = tools.names
        assert "hyperx_search" in names
        assert "hyperx_find_paths" in names
        assert "hyperx_lookup" in names

    def test_explore_level_includes_explore_tools(self, mock_client):
        """Explore level includes ExplorerTool, ExplainTool, RelationshipsTool."""
        tools = create_tools(mock_client, level="explore")

        names = tools.names
        assert "hyperx_explore" in names
        assert "hyperx_explain" in names
        assert "hyperx_relationships" in names
        assert len(names) == 6

    def test_explore_level_excludes_crud_tools(self, mock_client):
        """Explore level does not include CRUD tools."""
        tools = create_tools(mock_client, level="explore")

        names = tools.names
        assert "hyperx_entity" not in names
        assert "hyperx_hyperedge" not in names


class TestCreateToolsFullLevel:
    """Tests for create_tools() with full access level."""

    def test_full_level_includes_read_tools(self, mock_client):
        """Full level includes all read-level tools."""
        tools = create_tools(mock_client, level="full")

        names = tools.names
        assert "hyperx_search" in names
        assert "hyperx_find_paths" in names
        assert "hyperx_lookup" in names

    def test_full_level_includes_explore_tools(self, mock_client):
        """Full level includes all explore-level tools."""
        tools = create_tools(mock_client, level="full")

        names = tools.names
        assert "hyperx_explore" in names
        assert "hyperx_explain" in names
        assert "hyperx_relationships" in names

    def test_full_level_includes_crud_tools(self, mock_client):
        """Full level includes EntityCrudTool and HyperedgeCrudTool."""
        tools = create_tools(mock_client, level="full")

        names = tools.names
        assert "hyperx_entity" in names
        assert "hyperx_hyperedge" in names
        assert len(names) == 8


class TestCreateToolsInvalidLevel:
    """Tests for create_tools() with invalid access level."""

    def test_invalid_level_raises_valueerror(self, mock_client):
        """Invalid level raises ValueError."""
        with pytest.raises(ValueError, match="Invalid level"):
            create_tools(mock_client, level="invalid")

    def test_invalid_level_error_includes_valid_options(self, mock_client):
        """Error message includes valid level options."""
        with pytest.raises(ValueError, match="read|explore|full"):
            create_tools(mock_client, level="admin")


class TestCreateToolsKwargs:
    """Tests for create_tools() with tool_kwargs."""

    def test_search_mode_passed_to_search_tool(self, mock_client):
        """search_mode kwarg is passed to SearchTool."""
        tools = create_tools(mock_client, level="read", search_mode="vector")

        search_tool = tools.get("hyperx_search")
        # Verify mode was set (checking internal state)
        assert search_tool._mode == "vector"

    def test_default_limit_passed_to_search_tool(self, mock_client):
        """default_limit kwarg is passed to SearchTool."""
        tools = create_tools(mock_client, level="read", default_limit=20)

        search_tool = tools.get("hyperx_search")
        assert search_tool._default_limit == 20

    def test_reranker_passed_to_search_tool(self, mock_client):
        """reranker kwarg is passed to SearchTool."""

        def my_reranker(query, results):
            return results

        tools = create_tools(mock_client, level="read", reranker=my_reranker)

        search_tool = tools.get("hyperx_search")
        assert search_tool._reranker is my_reranker

    def test_default_max_hops_passed_to_paths_tool(self, mock_client):
        """default_max_hops kwarg is passed to PathsTool."""
        tools = create_tools(mock_client, level="read", default_max_hops=6)

        paths_tool = tools.get("hyperx_find_paths")
        assert paths_tool._default_max_hops == 6

    def test_default_k_paths_passed_to_paths_tool(self, mock_client):
        """default_k_paths kwarg is passed to PathsTool."""
        tools = create_tools(mock_client, level="read", default_k_paths=10)

        paths_tool = tools.get("hyperx_find_paths")
        assert paths_tool._default_k_paths == 10


class TestToolCollectionReturnType:
    """Tests for create_tools() return type."""

    def test_returns_tool_collection(self, mock_client):
        """create_tools() returns a ToolCollection instance."""
        tools = create_tools(mock_client)

        assert isinstance(tools, ToolCollection)

    def test_tool_collection_is_iterable(self, mock_client):
        """Returned ToolCollection is iterable."""
        tools = create_tools(mock_client)

        tool_list = list(tools)
        assert len(tool_list) == 3  # read level


class TestToolCollectionAsyncExecute:
    """Tests for ToolCollection async execute."""

    @pytest.mark.asyncio
    async def test_aexecute_calls_tool_arun(self, mock_client):
        """ToolCollection.aexecute() calls the tool's arun method."""
        # Setup mock search result
        mock_search_result = MagicMock()
        mock_search_result.entities = []
        mock_search_result.hyperedges = []
        mock_client.search.return_value = mock_search_result

        search = SearchTool(mock_client)
        collection = ToolCollection([search])

        result = await collection.aexecute("hyperx_search", query="test query")

        assert isinstance(result, ToolResult)

    @pytest.mark.asyncio
    async def test_aexecute_raises_keyerror_for_unknown_tool(self, mock_client):
        """ToolCollection.aexecute() raises KeyError for unknown tool."""
        search = SearchTool(mock_client)
        collection = ToolCollection([search])

        with pytest.raises(KeyError, match="unknown_tool"):
            await collection.aexecute("unknown_tool", query="test")
