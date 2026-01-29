"""Tests for LangChain tools integration.

Tests for HyperXToolkit, as_langchain_tools(), and LangChainToolWrapper
that provide LangChain-compatible wrappers for HyperX agent tools.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from hyperx import Entity, Hyperedge, HyperedgeMember, SearchResult
from hyperx.agents import (
    BaseTool,
    PathsTool,
    QualitySignals,
    SearchTool,
    ToolResult,
    create_tools,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_client():
    """Create a mock HyperX client."""
    client = MagicMock()
    now = datetime.now(timezone.utc)
    client.search.return_value = SearchResult(
        entities=[
            Entity(
                id="e:react",
                name="React",
                entity_type="technology",
                attributes={},
                created_at=now,
                updated_at=now,
            )
        ],
        hyperedges=[
            Hyperedge(
                id="h:1",
                description="React provides Hooks for state management",
                members=[
                    HyperedgeMember(entity_id="e:react", role="subject"),
                    HyperedgeMember(entity_id="e:hooks", role="object"),
                ],
                attributes={},
                created_at=now,
                updated_at=now,
            )
        ],
    )
    return client


@pytest.fixture
def mock_search_tool(mock_client):
    """Create a mock SearchTool."""
    return SearchTool(mock_client, mode="hybrid", default_limit=10)


@pytest.fixture
def mock_paths_tool(mock_client):
    """Create a mock PathsTool."""
    return PathsTool(mock_client)


# =============================================================================
# HyperXToolkit Tests
# =============================================================================


class TestHyperXToolkit:
    """Tests for HyperXToolkit class."""

    def test_toolkit_creation_default_level(self, mock_client):
        """Test toolkit creates with default read level."""
        from hyperx.agents.langchain import HyperXToolkit

        toolkit = HyperXToolkit(client=mock_client)
        tools = toolkit.get_tools()

        # Read level should have 3 tools
        assert len(tools) == 3
        tool_names = {t.name for t in tools}
        assert "hyperx_search" in tool_names
        assert "hyperx_find_paths" in tool_names
        assert "hyperx_lookup" in tool_names

    def test_toolkit_creation_explore_level(self, mock_client):
        """Test toolkit creates with explore level."""
        from hyperx.agents.langchain import HyperXToolkit

        toolkit = HyperXToolkit(client=mock_client, level="explore")
        tools = toolkit.get_tools()

        # Explore level should have 6 tools
        assert len(tools) == 6
        tool_names = {t.name for t in tools}
        assert "hyperx_explore" in tool_names
        assert "hyperx_explain" in tool_names
        assert "hyperx_relationships" in tool_names

    def test_toolkit_creation_full_level(self, mock_client):
        """Test toolkit creates with full level."""
        from hyperx.agents.langchain import HyperXToolkit

        toolkit = HyperXToolkit(client=mock_client, level="full")
        tools = toolkit.get_tools()

        # Full level should have 8 tools
        assert len(tools) == 8
        tool_names = {t.name for t in tools}
        # CRUD tools use shorter names (hyperx_entity, hyperx_hyperedge)
        assert "hyperx_entity" in tool_names
        assert "hyperx_hyperedge" in tool_names

    def test_toolkit_get_tool_by_name(self, mock_client):
        """Test getting a single tool by name."""
        from hyperx.agents.langchain import HyperXToolkit

        toolkit = HyperXToolkit(client=mock_client)
        tool = toolkit.get_tool("hyperx_search")

        assert tool is not None
        assert tool.name == "hyperx_search"

    def test_toolkit_get_tool_not_found(self, mock_client):
        """Test getting a non-existent tool raises KeyError."""
        from hyperx.agents.langchain import HyperXToolkit

        toolkit = HyperXToolkit(client=mock_client)

        with pytest.raises(KeyError, match="not_a_tool"):
            toolkit.get_tool("not_a_tool")

    def test_toolkit_tools_are_langchain_basetools(self, mock_client):
        """Test that returned tools are LangChain BaseTool instances."""
        from hyperx.agents.langchain import HyperXToolkit

        try:
            from langchain_core.tools import BaseTool as LangChainBaseTool
        except ImportError:
            pytest.skip("langchain-core not installed")

        toolkit = HyperXToolkit(client=mock_client)
        tools = toolkit.get_tools()

        for tool in tools:
            assert isinstance(tool, LangChainBaseTool)

    def test_toolkit_with_custom_kwargs(self, mock_client):
        """Test toolkit passes through custom kwargs to tools."""
        from hyperx.agents.langchain import HyperXToolkit

        toolkit = HyperXToolkit(
            client=mock_client,
            level="read",
            default_limit=20,
            search_mode="vector",
        )
        tools = toolkit.get_tools()

        # Find the search tool and verify configuration
        search_tool = next(t for t in tools if t.name == "hyperx_search")
        assert search_tool is not None


# =============================================================================
# as_langchain_tools() Tests
# =============================================================================


class TestAsLangchainTools:
    """Tests for as_langchain_tools() function."""

    def test_wrap_single_tool(self, mock_search_tool):
        """Test wrapping a single HyperX tool."""
        from hyperx.agents.langchain import as_langchain_tools

        lc_tools = as_langchain_tools([mock_search_tool])

        assert len(lc_tools) == 1
        assert lc_tools[0].name == "hyperx_search"

    def test_wrap_multiple_tools(self, mock_search_tool, mock_paths_tool):
        """Test wrapping multiple HyperX tools."""
        from hyperx.agents.langchain import as_langchain_tools

        lc_tools = as_langchain_tools([mock_search_tool, mock_paths_tool])

        assert len(lc_tools) == 2
        names = {t.name for t in lc_tools}
        assert "hyperx_search" in names
        assert "hyperx_find_paths" in names

    def test_wrapped_tools_have_descriptions(self, mock_search_tool):
        """Test wrapped tools have correct descriptions."""
        from hyperx.agents.langchain import as_langchain_tools

        lc_tools = as_langchain_tools([mock_search_tool])

        assert lc_tools[0].description is not None
        assert len(lc_tools[0].description) > 0
        assert "HyperX" in lc_tools[0].description or "search" in lc_tools[0].description.lower()

    def test_wrapped_tools_have_args_schema(self, mock_search_tool):
        """Test wrapped tools have Pydantic args_schema."""
        from hyperx.agents.langchain import as_langchain_tools

        try:
            from pydantic import BaseModel
        except ImportError:
            pytest.skip("pydantic not installed")

        lc_tools = as_langchain_tools([mock_search_tool])

        # args_schema should be a Pydantic model class
        assert lc_tools[0].args_schema is not None
        assert issubclass(lc_tools[0].args_schema, BaseModel)

    def test_empty_tool_list(self):
        """Test wrapping empty list returns empty list."""
        from hyperx.agents.langchain import as_langchain_tools

        lc_tools = as_langchain_tools([])
        assert lc_tools == []


# =============================================================================
# LangChainToolWrapper Tests
# =============================================================================


class TestLangChainToolWrapper:
    """Tests for LangChainToolWrapper class."""

    def test_wrapper_run_returns_json_string(self, mock_search_tool):
        """Test _run() returns JSON-formatted string."""
        from hyperx.agents.langchain import as_langchain_tools

        lc_tools = as_langchain_tools([mock_search_tool])
        tool = lc_tools[0]

        result = tool._run(query="React hooks")

        # Should be valid JSON
        parsed = json.loads(result)
        assert "success" in parsed
        assert "data" in parsed
        assert "explanation" in parsed

    def test_wrapper_run_success_format(self, mock_search_tool):
        """Test _run() formats successful results correctly."""
        from hyperx.agents.langchain import as_langchain_tools

        lc_tools = as_langchain_tools([mock_search_tool])
        tool = lc_tools[0]

        result = tool._run(query="React hooks")
        parsed = json.loads(result)

        assert parsed["success"] is True
        assert "entities" in parsed["data"]

    def test_wrapper_run_includes_quality_hints(self, mock_search_tool):
        """Test _run() includes quality hints when relevant."""
        from hyperx.agents.langchain import as_langchain_tools

        lc_tools = as_langchain_tools([mock_search_tool])
        tool = lc_tools[0]

        result = tool._run(query="React hooks")
        parsed = json.loads(result)

        # Should include quality_hints array
        assert "quality_hints" in parsed

    @pytest.mark.asyncio
    async def test_wrapper_arun_async(self, mock_search_tool):
        """Test _arun() works asynchronously."""
        from hyperx.agents.langchain import as_langchain_tools

        lc_tools = as_langchain_tools([mock_search_tool])
        tool = lc_tools[0]

        result = await tool._arun(query="React hooks")

        # Should return same format as sync
        parsed = json.loads(result)
        assert "success" in parsed
        assert "data" in parsed

    def test_wrapper_handles_failure(self, mock_client):
        """Test wrapper handles tool execution failure."""
        from hyperx.agents.langchain import as_langchain_tools

        # Make search throw an exception
        mock_client.search.side_effect = Exception("API Error")
        search_tool = SearchTool(mock_client)
        lc_tools = as_langchain_tools([search_tool])
        tool = lc_tools[0]

        result = tool._run(query="React")
        parsed = json.loads(result)

        assert parsed["success"] is False
        assert "explanation" in parsed

    @pytest.mark.asyncio
    async def test_wrapper_arun_handles_failure(self, mock_client):
        """Test async wrapper handles tool execution failure."""
        from hyperx.agents.langchain import as_langchain_tools

        # Create search tool and wrap it
        search_tool = SearchTool(mock_client)
        lc_tools = as_langchain_tools([search_tool])
        tool = lc_tools[0]

        # Mock the underlying HyperX tool's arun method to raise an exception
        tool.hyperx_tool.arun = AsyncMock(side_effect=Exception("Async API Error"))

        result = await tool._arun(query="React")
        parsed = json.loads(result)

        assert parsed["success"] is False
        assert "explanation" in parsed
        assert "Async API Error" in parsed["explanation"]

    def test_wrapper_name_passthrough(self, mock_search_tool):
        """Test tool name passes through correctly."""
        from hyperx.agents.langchain import as_langchain_tools

        lc_tools = as_langchain_tools([mock_search_tool])

        assert lc_tools[0].name == mock_search_tool.name

    def test_wrapper_description_passthrough(self, mock_search_tool):
        """Test tool description passes through correctly."""
        from hyperx.agents.langchain import as_langchain_tools

        lc_tools = as_langchain_tools([mock_search_tool])

        assert lc_tools[0].description == mock_search_tool.description


# =============================================================================
# Import Error Handling Tests
# =============================================================================


class TestImportErrorHandling:
    """Tests for graceful handling when langchain-core is not installed."""

    def test_import_error_message_is_helpful(self):
        """Test that import error message guides users to install langchain-core.

        Note: This test only verifies the module structure when langchain-core IS
        installed. Actual import error behavior is tested by attempting import
        in an environment without langchain-core.
        """
        # This test passes if we can import without error when langchain-core is present
        try:
            from hyperx.agents.langchain import HyperXToolkit, as_langchain_tools
        except ImportError as e:
            # If langchain-core not installed, verify error message is helpful
            assert "langchain-core" in str(e).lower() or "pip install" in str(e).lower()


# =============================================================================
# Integration Tests
# =============================================================================


class TestLangChainIntegration:
    """Integration tests for using tools with LangChain agents."""

    def test_toolkit_tools_work_with_langgraph_pattern(self, mock_client):
        """Test tools work with LangGraph create_react_agent pattern.

        Note: This doesn't actually create an agent but verifies the tools
        have the correct interface expected by LangGraph.
        """
        from hyperx.agents.langchain import HyperXToolkit

        toolkit = HyperXToolkit(client=mock_client, level="explore")
        tools = toolkit.get_tools()

        # Verify each tool has the required methods for LangGraph
        for tool in tools:
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")
            assert hasattr(tool, "_run") or hasattr(tool, "invoke")
            assert hasattr(tool, "_arun") or hasattr(tool, "ainvoke")

    def test_from_create_tools_integration(self, mock_client):
        """Test HyperXToolkit integrates with existing create_tools factory."""
        from hyperx.agents.langchain import HyperXToolkit

        # Both should create equivalent tool sets
        toolkit = HyperXToolkit(client=mock_client, level="read")
        toolkit_tools = toolkit.get_tools()

        native_tools = create_tools(mock_client, level="read")

        # Same number of tools
        assert len(toolkit_tools) == len(native_tools)

        # Same tool names
        toolkit_names = {t.name for t in toolkit_tools}
        native_names = {t.name for t in native_tools}
        assert toolkit_names == native_names
