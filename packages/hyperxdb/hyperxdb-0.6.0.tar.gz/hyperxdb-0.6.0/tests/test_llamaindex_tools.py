"""Tests for LlamaIndex tools integration.

Tests for HyperXToolSpec, as_llamaindex_tools(), and LlamaIndexToolWrapper
that provide LlamaIndex-compatible wrappers for HyperX agent tools.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from hyperx import Entity, Hyperedge, HyperedgeMember, SearchResult
from hyperx.agents import PathsTool, SearchTool, create_tools

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
# HyperXToolSpec Tests
# =============================================================================


class TestHyperXToolSpec:
    """Tests for HyperXToolSpec class."""

    def test_toolspec_creation_default_level(self, mock_client):
        """Test toolspec creates with default read level."""
        from hyperx.agents.llamaindex import HyperXToolSpec

        tool_spec = HyperXToolSpec(client=mock_client)
        tools = tool_spec.to_tool_list()

        # Read level should have 3 tools
        assert len(tools) == 3
        tool_names = {t.metadata.name for t in tools}
        assert "hyperx_search" in tool_names
        assert "hyperx_find_paths" in tool_names
        assert "hyperx_lookup" in tool_names

    def test_toolspec_creation_explore_level(self, mock_client):
        """Test toolspec creates with explore level."""
        from hyperx.agents.llamaindex import HyperXToolSpec

        tool_spec = HyperXToolSpec(client=mock_client, level="explore")
        tools = tool_spec.to_tool_list()

        # Explore level should have 6 tools
        assert len(tools) == 6
        tool_names = {t.metadata.name for t in tools}
        assert "hyperx_explore" in tool_names
        assert "hyperx_explain" in tool_names
        assert "hyperx_relationships" in tool_names

    def test_toolspec_creation_full_level(self, mock_client):
        """Test toolspec creates with full level."""
        from hyperx.agents.llamaindex import HyperXToolSpec

        tool_spec = HyperXToolSpec(client=mock_client, level="full")
        tools = tool_spec.to_tool_list()

        # Full level should have 8 tools
        assert len(tools) == 8
        tool_names = {t.metadata.name for t in tools}
        # CRUD tools use shorter names (hyperx_entity, hyperx_hyperedge)
        assert "hyperx_entity" in tool_names
        assert "hyperx_hyperedge" in tool_names

    def test_toolspec_get_tool_by_name(self, mock_client):
        """Test getting a single tool by name."""
        from hyperx.agents.llamaindex import HyperXToolSpec

        tool_spec = HyperXToolSpec(client=mock_client)
        tool = tool_spec.get_tool("hyperx_search")

        assert tool is not None
        assert tool.metadata.name == "hyperx_search"

    def test_toolspec_get_tool_not_found(self, mock_client):
        """Test getting a non-existent tool raises KeyError."""
        from hyperx.agents.llamaindex import HyperXToolSpec

        tool_spec = HyperXToolSpec(client=mock_client)

        with pytest.raises(KeyError, match="not_a_tool"):
            tool_spec.get_tool("not_a_tool")

    def test_toolspec_tools_are_llamaindex_functiontools(self, mock_client):
        """Test that returned tools are LlamaIndex FunctionTool instances."""
        from hyperx.agents.llamaindex import HyperXToolSpec

        try:
            from llama_index.core.tools import FunctionTool
        except ImportError:
            pytest.skip("llama-index-core not installed")

        tool_spec = HyperXToolSpec(client=mock_client)
        tools = tool_spec.to_tool_list()

        for tool in tools:
            assert isinstance(tool, FunctionTool)

    def test_toolspec_with_custom_kwargs(self, mock_client):
        """Test toolspec passes through custom kwargs to tools."""
        from hyperx.agents.llamaindex import HyperXToolSpec

        tool_spec = HyperXToolSpec(
            client=mock_client,
            level="read",
            default_limit=20,
            search_mode="vector",
        )
        tools = tool_spec.to_tool_list()

        # Find the search tool and verify it exists
        search_tool = next(t for t in tools if t.metadata.name == "hyperx_search")
        assert search_tool is not None


# =============================================================================
# as_llamaindex_tools() Tests
# =============================================================================


class TestAsLlamaindexTools:
    """Tests for as_llamaindex_tools() function."""

    def test_wrap_single_tool(self, mock_search_tool):
        """Test wrapping a single HyperX tool."""
        from hyperx.agents.llamaindex import as_llamaindex_tools

        li_tools = as_llamaindex_tools([mock_search_tool])

        assert len(li_tools) == 1
        assert li_tools[0].metadata.name == "hyperx_search"

    def test_wrap_multiple_tools(self, mock_search_tool, mock_paths_tool):
        """Test wrapping multiple HyperX tools."""
        from hyperx.agents.llamaindex import as_llamaindex_tools

        li_tools = as_llamaindex_tools([mock_search_tool, mock_paths_tool])

        assert len(li_tools) == 2
        names = {t.metadata.name for t in li_tools}
        assert "hyperx_search" in names
        assert "hyperx_find_paths" in names

    def test_wrapped_tools_have_descriptions(self, mock_search_tool):
        """Test wrapped tools have correct descriptions."""
        from hyperx.agents.llamaindex import as_llamaindex_tools

        li_tools = as_llamaindex_tools([mock_search_tool])

        assert li_tools[0].metadata.description is not None
        assert len(li_tools[0].metadata.description) > 0
        assert (
            "HyperX" in li_tools[0].metadata.description
            or "search" in li_tools[0].metadata.description.lower()
        )

    def test_empty_tool_list(self):
        """Test wrapping empty list returns empty list."""
        from hyperx.agents.llamaindex import as_llamaindex_tools

        li_tools = as_llamaindex_tools([])
        assert li_tools == []


# =============================================================================
# LlamaIndexToolWrapper Tests
# =============================================================================


class TestLlamaIndexToolWrapper:
    """Tests for LlamaIndexToolWrapper class."""

    def test_wrapper_call_returns_json_string(self, mock_search_tool):
        """Test tool call returns JSON-formatted string."""
        from hyperx.agents.llamaindex import as_llamaindex_tools

        li_tools = as_llamaindex_tools([mock_search_tool])
        tool = li_tools[0]

        result = tool.call(query="React hooks")

        # LlamaIndex FunctionTool.call() returns ToolOutput with content attribute
        assert result.content is not None
        # Should be valid JSON
        parsed = json.loads(result.content)
        assert "success" in parsed
        assert "data" in parsed
        assert "explanation" in parsed

    def test_wrapper_call_success_format(self, mock_search_tool):
        """Test tool call formats successful results correctly."""
        from hyperx.agents.llamaindex import as_llamaindex_tools

        li_tools = as_llamaindex_tools([mock_search_tool])
        tool = li_tools[0]

        result = tool.call(query="React hooks")
        parsed = json.loads(result.content)

        assert parsed["success"] is True
        assert "entities" in parsed["data"]

    def test_wrapper_call_includes_quality_hints(self, mock_search_tool):
        """Test tool call includes quality hints when relevant."""
        from hyperx.agents.llamaindex import as_llamaindex_tools

        li_tools = as_llamaindex_tools([mock_search_tool])
        tool = li_tools[0]

        result = tool.call(query="React hooks")
        parsed = json.loads(result.content)

        # Should include quality_hints array
        assert "quality_hints" in parsed

    @pytest.mark.asyncio
    async def test_wrapper_acall_async(self, mock_search_tool):
        """Test acall() works asynchronously."""
        from hyperx.agents.llamaindex import as_llamaindex_tools

        li_tools = as_llamaindex_tools([mock_search_tool])
        tool = li_tools[0]

        result = await tool.acall(query="React hooks")

        # Should return same format as sync
        parsed = json.loads(result.content)
        assert "success" in parsed
        assert "data" in parsed

    def test_wrapper_handles_failure(self, mock_client):
        """Test wrapper handles tool execution failure."""
        from hyperx.agents.llamaindex import as_llamaindex_tools

        # Make search throw an exception
        mock_client.search.side_effect = Exception("API Error")
        search_tool = SearchTool(mock_client)
        li_tools = as_llamaindex_tools([search_tool])
        tool = li_tools[0]

        result = tool.call(query="React")
        parsed = json.loads(result.content)

        assert parsed["success"] is False
        assert "explanation" in parsed

    @pytest.mark.asyncio
    async def test_wrapper_acall_handles_failure(self, mock_client):
        """Test async wrapper handles tool execution failure."""
        from hyperx.agents.llamaindex import LlamaIndexToolWrapper

        # Create search tool and wrap it
        search_tool = SearchTool(mock_client)
        wrapper = LlamaIndexToolWrapper(search_tool)

        # Mock the underlying HyperX tool's arun method to raise an exception
        wrapper.hyperx_tool.arun = AsyncMock(side_effect=Exception("Async API Error"))

        # Call the async function directly (this is what FunctionTool uses internally)
        result = await wrapper.async_fn(query="React")
        parsed = json.loads(result)

        assert parsed["success"] is False
        assert "explanation" in parsed
        assert "Async API Error" in parsed["explanation"]

    def test_wrapper_name_passthrough(self, mock_search_tool):
        """Test tool name passes through correctly."""
        from hyperx.agents.llamaindex import as_llamaindex_tools

        li_tools = as_llamaindex_tools([mock_search_tool])

        assert li_tools[0].metadata.name == mock_search_tool.name

    def test_wrapper_description_passthrough(self, mock_search_tool):
        """Test tool description passes through correctly."""
        from hyperx.agents.llamaindex import as_llamaindex_tools

        li_tools = as_llamaindex_tools([mock_search_tool])

        assert li_tools[0].metadata.description == mock_search_tool.description


# =============================================================================
# Import Error Handling Tests
# =============================================================================


class TestImportErrorHandling:
    """Tests for graceful handling when llama-index-core is not installed."""

    def test_import_error_message_is_helpful(self):
        """Test that import error message guides users to install llama-index-core.

        Note: This test only verifies the module structure when llama-index-core IS
        installed. Actual import error behavior is tested by attempting import
        in an environment without llama-index-core.
        """
        # This test passes if we can import without error when llama-index-core is present
        try:
            from hyperx.agents.llamaindex import (  # noqa: F401
                HyperXToolSpec,
                as_llamaindex_tools,
            )
        except ImportError as e:
            # If llama-index-core not installed, verify error message is helpful
            assert "llama-index-core" in str(e).lower() or "pip install" in str(e).lower()


# =============================================================================
# Integration Tests
# =============================================================================


class TestLlamaIndexIntegration:
    """Integration tests for using tools with LlamaIndex agents."""

    def test_toolspec_tools_work_with_agent_pattern(self, mock_client):
        """Test tools work with LlamaIndex agent pattern.

        Note: This doesn't actually create an agent but verifies the tools
        have the correct interface expected by LlamaIndex agents.
        """
        from hyperx.agents.llamaindex import HyperXToolSpec

        tool_spec = HyperXToolSpec(client=mock_client, level="explore")
        tools = tool_spec.to_tool_list()

        # Verify each tool has the required attributes for LlamaIndex
        for tool in tools:
            assert hasattr(tool, "metadata")
            assert hasattr(tool.metadata, "name")
            assert hasattr(tool.metadata, "description")
            assert callable(tool.call) or callable(tool)

    def test_from_create_tools_integration(self, mock_client):
        """Test HyperXToolSpec integrates with existing create_tools factory."""
        from hyperx.agents.llamaindex import HyperXToolSpec

        # Both should create equivalent tool sets
        tool_spec = HyperXToolSpec(client=mock_client, level="read")
        spec_tools = tool_spec.to_tool_list()

        native_tools = create_tools(mock_client, level="read")

        # Same number of tools
        assert len(spec_tools) == len(native_tools)

        # Same tool names
        spec_names = {t.metadata.name for t in spec_tools}
        native_names = {t.name for t in native_tools}
        assert spec_names == native_names

    def test_toolspec_with_openai_agent_pattern(self, mock_client):
        """Test tools can be used with OpenAIAgent.from_tools() pattern.

        This verifies the to_tool_list() method returns proper FunctionTool
        instances that would work with LlamaIndex OpenAIAgent.
        """
        from hyperx.agents.llamaindex import HyperXToolSpec

        try:
            from llama_index.core.tools import FunctionTool
        except ImportError:
            pytest.skip("llama-index-core not installed")

        tool_spec = HyperXToolSpec(client=mock_client, level="full")
        tools = tool_spec.to_tool_list()

        # All tools should be FunctionTool instances
        for tool in tools:
            assert isinstance(tool, FunctionTool)

        # Tools should have proper metadata for OpenAI function calling
        for tool in tools:
            assert tool.metadata.name is not None
            assert tool.metadata.description is not None
            # FunctionTool should be callable
            assert callable(tool)
