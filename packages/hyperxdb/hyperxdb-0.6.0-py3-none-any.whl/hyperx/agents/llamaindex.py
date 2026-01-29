"""LlamaIndex integration for HyperX agent tools.

This module provides LlamaIndex-compatible wrappers for HyperX agent tools,
enabling use with LlamaIndex agents, query engines, and any LlamaIndex-compatible
framework.

Install: pip install hyperx[llamaindex]

Example:
    >>> from hyperx import HyperX
    >>> from hyperx.agents.llamaindex import HyperXToolSpec, as_llamaindex_tools
    >>>
    >>> # Quick setup with tool spec
    >>> db = HyperX(api_key="hx_sk_...")
    >>> tool_spec = HyperXToolSpec(client=db, level="explore")
    >>> tools = tool_spec.to_tool_list()
    >>>
    >>> # Use with OpenAI agent
    >>> from llama_index.agent.openai import OpenAIAgent
    >>> agent = OpenAIAgent.from_tools(tools)
    >>>
    >>> # Custom tools
    >>> from hyperx.agents import SearchTool, PathsTool
    >>> tools = as_llamaindex_tools([
    ...     SearchTool(db, mode="hybrid"),
    ...     PathsTool(db),
    ... ])
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Literal

try:
    from llama_index.core.tools import FunctionTool
except ImportError as e:
    raise ImportError(
        "LlamaIndex integration requires llama-index-core. "
        "Install with: pip install hyperx[llamaindex]"
    ) from e

from hyperx.agents.base import BaseTool, QualitySignals, ToolResult
from hyperx.agents.factory import AccessLevel, create_tools

if TYPE_CHECKING:
    from hyperx import HyperX

__all__ = ["HyperXToolSpec", "as_llamaindex_tools", "LlamaIndexToolWrapper"]


class LlamaIndexToolWrapper:
    """Wrapper that adapts a HyperX tool for use with LlamaIndex FunctionTool.

    This wrapper provides sync and async callable functions that can be
    passed to LlamaIndex's FunctionTool.from_defaults() to create
    LlamaIndex-compatible tools.

    The wrapper:
        - Provides a sync function for tool.call()
        - Provides an async function for tool.acall()
        - Converts ToolResult to JSON string with quality hints
        - Handles errors gracefully with formatted error responses

    Attributes:
        hyperx_tool: The underlying HyperX tool instance.
        name: The tool name (passed through from wrapped tool).
        description: The tool description (passed through from wrapped tool).

    Example:
        >>> from hyperx.agents import SearchTool
        >>> from hyperx.agents.llamaindex import LlamaIndexToolWrapper
        >>>
        >>> search = SearchTool(client)
        >>> wrapper = LlamaIndexToolWrapper(search)
        >>> result = wrapper.sync_fn(query="React hooks")
    """

    def __init__(self, tool: BaseTool) -> None:
        """Initialize the LlamaIndexToolWrapper.

        Args:
            tool: HyperX tool implementing the BaseTool protocol.
        """
        self.hyperx_tool = tool
        self.name = tool.name
        self.description = tool.description

    def sync_fn(self, **kwargs: Any) -> str:
        """Execute the tool synchronously.

        Calls the underlying HyperX tool's run() method and formats
        the ToolResult as a JSON string for LlamaIndex agents.

        Args:
            **kwargs: Arguments to pass to the underlying tool.

        Returns:
            JSON string containing:
                - success: Whether the tool execution succeeded
                - data: The result data
                - explanation: Human-readable explanation
                - quality_hints: List of quality-related hints
        """
        try:
            result = self.hyperx_tool.run(**kwargs)
            return self._format_result(result)
        except Exception as e:
            error_result = ToolResult(
                success=False,
                data=None,
                quality=QualitySignals.default(),
                explanation=f"Tool execution failed: {e}",
            )
            return self._format_result(error_result)

    async def async_fn(self, **kwargs: Any) -> str:
        """Execute the tool asynchronously.

        Calls the underlying HyperX tool's arun() method and formats
        the ToolResult as a JSON string for LlamaIndex agents.

        Args:
            **kwargs: Arguments to pass to the underlying tool.

        Returns:
            JSON string containing the formatted result.
        """
        try:
            result = await self.hyperx_tool.arun(**kwargs)
            return self._format_result(result)
        except Exception as e:
            error_result = ToolResult(
                success=False,
                data=None,
                quality=QualitySignals.default(),
                explanation=f"Tool execution failed: {e}",
            )
            return self._format_result(error_result)

    def _format_result(self, result: ToolResult) -> str:
        """Format a ToolResult as JSON string for LlamaIndex.

        Converts the ToolResult into a JSON string that includes
        the result data, explanation, and quality hints to help
        LLM agents make informed decisions.

        Args:
            result: ToolResult from the underlying tool execution.

        Returns:
            JSON string with success, data, explanation, and quality_hints.
        """
        quality_hints = self._extract_quality_hints(result.quality)

        output = {
            "success": result.success,
            "data": result.data,
            "explanation": result.explanation,
            "quality_hints": quality_hints,
        }

        return json.dumps(output, default=str)

    def _extract_quality_hints(self, quality: QualitySignals) -> list[str]:
        """Extract actionable hints from QualitySignals.

        Converts quality signals into human-readable hints that can
        guide LLM agent behavior for self-correction.

        Args:
            quality: QualitySignals from the tool result.

        Returns:
            List of hint strings.
        """
        hints = []

        # Confidence hint
        if quality.confidence < 0.5:
            hints.append("Low confidence results - consider refining the query")
        elif quality.confidence >= 0.8:
            hints.append("High confidence results")

        # Coverage hint
        if quality.coverage < 0.5:
            hints.append("Low topic coverage - results may be incomplete")

        # Diversity hint
        if quality.diversity < 0.3:
            hints.append("Low result diversity - results may be too similar")

        # Should retrieve more hint
        if quality.should_retrieve_more:
            hints.append("Consider retrieving more data")

        # Suggested refinements
        if quality.suggested_refinements:
            refinements = ", ".join(quality.suggested_refinements[:3])
            hints.append(f"Suggested query refinements: {refinements}")

        # Alternative queries
        if quality.alternative_queries:
            alternatives = ", ".join(quality.alternative_queries[:3])
            hints.append(f"Alternative queries to try: {alternatives}")

        # Missing context
        if quality.missing_context_hints:
            missing = ", ".join(quality.missing_context_hints[:3])
            hints.append(f"Missing context: {missing}")

        return hints

    def to_function_tool(self) -> FunctionTool:
        """Convert this wrapper to a LlamaIndex FunctionTool.

        Returns:
            FunctionTool instance ready for use with LlamaIndex agents.

        Example:
            >>> wrapper = LlamaIndexToolWrapper(search_tool)
            >>> function_tool = wrapper.to_function_tool()
            >>> agent = OpenAIAgent.from_tools([function_tool])
        """
        return FunctionTool.from_defaults(
            fn=self.sync_fn,
            async_fn=self.async_fn,
            name=self.name,
            description=self.description,
        )


class HyperXToolSpec:
    """Tool spec that creates LlamaIndex-compatible tools from a HyperX client.

    HyperXToolSpec provides a convenient way to create a set of LlamaIndex
    FunctionTool instances based on a HyperX client and access level. It
    follows a similar pattern to LlamaIndex's BaseToolSpec while integrating
    with HyperX's tool factory.

    Access levels:
        - "read": SearchTool, PathsTool, LookupTool (default)
        - "explore": read + ExplorerTool, ExplainTool, RelationshipsTool
        - "full": explore + EntityCrudTool, HyperedgeCrudTool

    Attributes:
        client: HyperX client instance.
        level: Access level for tool creation.
        tool_kwargs: Additional kwargs passed to underlying tools.

    Example:
        >>> from hyperx import HyperX
        >>> from hyperx.agents.llamaindex import HyperXToolSpec
        >>>
        >>> db = HyperX(api_key="hx_sk_...")
        >>> tool_spec = HyperXToolSpec(client=db, level="explore")
        >>> tools = tool_spec.to_tool_list()
        >>>
        >>> # Use with OpenAI agent
        >>> from llama_index.agent.openai import OpenAIAgent
        >>> agent = OpenAIAgent.from_tools(tools)
    """

    def __init__(
        self,
        client: HyperX,
        *,
        level: AccessLevel = "read",
        # Tool configuration kwargs (passed to create_tools)
        search_mode: Literal["hybrid", "vector", "text"] | None = None,
        vector_weight: float | None = None,
        reranker: Any | None = None,
        default_limit: int | None = None,
        expand_graph: bool | None = None,
        default_max_hops: int | None = None,
        default_k_paths: int | None = None,
    ) -> None:
        """Initialize the HyperXToolSpec.

        Args:
            client: HyperX client instance for API calls.
            level: Access level determining which tools to include.
                Defaults to "read".
            search_mode: Search mode for SearchTool.
            vector_weight: Weight for vector similarity in hybrid search.
            reranker: Optional callable to rerank search results.
            default_limit: Default number of search results.
            expand_graph: Whether to expand search results by following edges.
            default_max_hops: Default max hops for PathsTool and ExplorerTool.
            default_k_paths: Default number of paths for PathsTool.
        """
        self._client = client
        self._level = level

        # Build tool kwargs dict, excluding None values
        self._tool_kwargs: dict[str, Any] = {}
        if search_mode is not None:
            self._tool_kwargs["search_mode"] = search_mode
        if vector_weight is not None:
            self._tool_kwargs["vector_weight"] = vector_weight
        if reranker is not None:
            self._tool_kwargs["reranker"] = reranker
        if default_limit is not None:
            self._tool_kwargs["default_limit"] = default_limit
        if expand_graph is not None:
            self._tool_kwargs["expand_graph"] = expand_graph
        if default_max_hops is not None:
            self._tool_kwargs["default_max_hops"] = default_max_hops
        if default_k_paths is not None:
            self._tool_kwargs["default_k_paths"] = default_k_paths

        # Create underlying tools
        self._tool_collection = create_tools(
            self._client,
            level=self._level,
            **self._tool_kwargs,
        )

        # Wrap as LlamaIndex tools
        self._llamaindex_tools: list[FunctionTool] = []
        self._tools_by_name: dict[str, FunctionTool] = {}
        for tool in self._tool_collection:
            wrapper = LlamaIndexToolWrapper(tool)
            function_tool = wrapper.to_function_tool()
            self._llamaindex_tools.append(function_tool)
            # Tool name is always set by our wrapper, so this is safe
            tool_name = function_tool.metadata.name
            assert tool_name is not None, "Tool name should never be None"
            self._tools_by_name[tool_name] = function_tool

    def to_tool_list(self) -> list[FunctionTool]:
        """Get all LlamaIndex tools as a list.

        Returns:
            List of LlamaIndex FunctionTool instances.

        Example:
            >>> tool_spec = HyperXToolSpec(client=db, level="explore")
            >>> tools = tool_spec.to_tool_list()
            >>> for tool in tools:
            ...     print(f"{tool.metadata.name}: {tool.metadata.description}")
        """
        return list(self._llamaindex_tools)

    def get_tool(self, name: str) -> FunctionTool:
        """Get a specific tool by name.

        Args:
            name: Name of the tool to retrieve.

        Returns:
            The LlamaIndex FunctionTool.

        Raises:
            KeyError: If no tool with that name exists.

        Example:
            >>> tool_spec = HyperXToolSpec(client=db)
            >>> search_tool = tool_spec.get_tool("hyperx_search")
        """
        if name not in self._tools_by_name:
            raise KeyError(f"Tool not found: {name}")
        return self._tools_by_name[name]


def as_llamaindex_tools(tools: list[BaseTool]) -> list[FunctionTool]:
    """Convert a list of HyperX tools to LlamaIndex-compatible FunctionTools.

    This function wraps each HyperX tool as a LlamaIndex FunctionTool,
    enabling use with LlamaIndex agents, query engines, and other
    LlamaIndex-compatible frameworks.

    Args:
        tools: List of HyperX tools implementing the BaseTool protocol.

    Returns:
        List of LlamaIndex FunctionTool instances.

    Example:
        >>> from hyperx import HyperX
        >>> from hyperx.agents import SearchTool, PathsTool
        >>> from hyperx.agents.llamaindex import as_llamaindex_tools
        >>>
        >>> db = HyperX(api_key="hx_sk_...")
        >>> tools = as_llamaindex_tools([
        ...     SearchTool(db, mode="hybrid"),
        ...     PathsTool(db),
        ... ])
        >>>
        >>> # Use with OpenAI agent
        >>> from llama_index.agent.openai import OpenAIAgent
        >>> agent = OpenAIAgent.from_tools(tools)
    """
    return [LlamaIndexToolWrapper(tool).to_function_tool() for tool in tools]
