"""LangChain integration for HyperX agent tools.

This module provides LangChain-compatible wrappers for HyperX agent tools,
enabling use with LangChain agents, LangGraph, and any LangChain-compatible
framework.

Install: pip install hyperx[langchain]

Example:
    >>> from hyperx import HyperX
    >>> from hyperx.agents.langchain import HyperXToolkit, as_langchain_tools
    >>>
    >>> # Quick setup with toolkit
    >>> db = HyperX(api_key="hx_sk_...")
    >>> toolkit = HyperXToolkit(client=db, level="explore")
    >>> tools = toolkit.get_tools()
    >>>
    >>> # Custom tools
    >>> from hyperx.agents import SearchTool, PathsTool
    >>> tools = as_langchain_tools([
    ...     SearchTool(db, mode="hybrid"),
    ...     PathsTool(db),
    ... ])
    >>>
    >>> # Use with LangGraph
    >>> from langgraph.prebuilt import create_react_agent
    >>> agent = create_react_agent(llm, tools)
"""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import TYPE_CHECKING, Any, Literal, Type

from pydantic import BaseModel, ConfigDict, Field, create_model

try:
    from langchain_core.tools import BaseTool as LangChainBaseTool
except ImportError as e:
    raise ImportError(
        "LangChain integration requires langchain-core. "
        "Install with: pip install hyperx[langchain]"
    ) from e

from hyperx.agents.base import BaseTool, QualitySignals, ToolResult
from hyperx.agents.factory import AccessLevel, ToolCollection, create_tools

if TYPE_CHECKING:
    from hyperx import HyperX

__all__ = ["HyperXToolkit", "as_langchain_tools", "LangChainToolWrapper"]


class LangChainToolWrapper(LangChainBaseTool):
    """Wrapper that adapts a HyperX tool to the LangChain BaseTool interface.

    This wrapper converts a HyperX tool (implementing the BaseTool protocol)
    into a LangChain-compatible tool that can be used with LangChain agents,
    LangGraph, and other LangChain-compatible frameworks.

    The wrapper:
        - Passes through tool name and description
        - Converts OpenAI schema to Pydantic args_schema
        - Converts ToolResult to JSON string with quality hints
        - Supports both sync (_run) and async (_arun) execution

    Attributes:
        name: The tool name (passed through from wrapped tool).
        description: The tool description (passed through from wrapped tool).
        args_schema: Pydantic model for tool arguments.
        hyperx_tool: The underlying HyperX tool instance.

    Example:
        >>> from hyperx.agents import SearchTool
        >>> from hyperx.agents.langchain import LangChainToolWrapper
        >>>
        >>> search = SearchTool(client)
        >>> lc_tool = LangChainToolWrapper.from_hyperx_tool(search)
        >>> result = lc_tool._run(query="React hooks")
    """

    name: str = ""
    description: str = ""
    args_schema: Type[BaseModel] | None = None
    hyperx_tool: Any = None  # BaseTool protocol, but Any for pydantic

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def from_hyperx_tool(cls, tool: BaseTool) -> "LangChainToolWrapper":
        """Create a LangChain wrapper from a HyperX tool.

        Args:
            tool: HyperX tool implementing the BaseTool protocol.

        Returns:
            LangChainToolWrapper instance wrapping the tool.

        Example:
            >>> search = SearchTool(client)
            >>> lc_tool = LangChainToolWrapper.from_hyperx_tool(search)
        """
        # Extract schema from OpenAI format
        openai_schema = tool.to_openai_schema()
        function_def = openai_schema.get("function", openai_schema)
        parameters = function_def.get("parameters", {})

        # Build Pydantic model from OpenAI schema
        args_schema = _openai_schema_to_pydantic(
            name=f"{tool.name}_args",
            parameters=parameters,
        )

        return cls(
            name=tool.name,
            description=tool.description,
            args_schema=args_schema,
            hyperx_tool=tool,
        )

    def _run(self, **kwargs: Any) -> str:
        """Execute the tool synchronously.

        Calls the underlying HyperX tool's run() method and formats
        the ToolResult as a JSON string for LangChain agents.

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

    async def _arun(self, **kwargs: Any) -> str:
        """Execute the tool asynchronously.

        Calls the underlying HyperX tool's arun() method and formats
        the ToolResult as a JSON string for LangChain agents.

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
        """Format a ToolResult as JSON string for LangChain.

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


class HyperXToolkit:
    """Toolkit that creates LangChain-compatible tools from a HyperX client.

    HyperXToolkit provides a convenient way to create a set of LangChain
    tools based on a HyperX client and access level. It follows the
    LangChain toolkit pattern while integrating with HyperX's tool factory.

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
        >>> from hyperx.agents.langchain import HyperXToolkit
        >>>
        >>> db = HyperX(api_key="hx_sk_...")
        >>> toolkit = HyperXToolkit(client=db, level="explore")
        >>> tools = toolkit.get_tools()
        >>>
        >>> # Use with LangGraph
        >>> from langgraph.prebuilt import create_react_agent
        >>> agent = create_react_agent(llm, tools)
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
        """Initialize the HyperXToolkit.

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

        # Wrap as LangChain tools
        self._langchain_tools: list[LangChainToolWrapper] = []
        self._tools_by_name: dict[str, LangChainToolWrapper] = {}
        for tool in self._tool_collection:
            wrapped = LangChainToolWrapper.from_hyperx_tool(tool)
            self._langchain_tools.append(wrapped)
            self._tools_by_name[wrapped.name] = wrapped

    def get_tools(self) -> list[LangChainToolWrapper]:
        """Get all LangChain tools in the toolkit.

        Returns:
            List of LangChain-wrapped HyperX tools.

        Example:
            >>> toolkit = HyperXToolkit(client=db, level="explore")
            >>> tools = toolkit.get_tools()
            >>> for tool in tools:
            ...     print(f"{tool.name}: {tool.description}")
        """
        return list(self._langchain_tools)

    def get_tool(self, name: str) -> LangChainToolWrapper:
        """Get a specific tool by name.

        Args:
            name: Name of the tool to retrieve.

        Returns:
            The LangChain-wrapped tool.

        Raises:
            KeyError: If no tool with that name exists.

        Example:
            >>> toolkit = HyperXToolkit(client=db)
            >>> search_tool = toolkit.get_tool("hyperx_search")
        """
        if name not in self._tools_by_name:
            raise KeyError(f"Tool not found: {name}")
        return self._tools_by_name[name]


def as_langchain_tools(tools: list[BaseTool]) -> list[LangChainToolWrapper]:
    """Convert a list of HyperX tools to LangChain-compatible tools.

    This function wraps each HyperX tool as a LangChain BaseTool,
    enabling use with LangChain agents, LangGraph, and other
    LangChain-compatible frameworks.

    Args:
        tools: List of HyperX tools implementing the BaseTool protocol.

    Returns:
        List of LangChain-wrapped tools.

    Example:
        >>> from hyperx import HyperX
        >>> from hyperx.agents import SearchTool, PathsTool
        >>> from hyperx.agents.langchain import as_langchain_tools
        >>>
        >>> db = HyperX(api_key="hx_sk_...")
        >>> tools = as_langchain_tools([
        ...     SearchTool(db, mode="hybrid"),
        ...     PathsTool(db),
        ... ])
        >>>
        >>> # Use with LangGraph
        >>> from langgraph.prebuilt import create_react_agent
        >>> agent = create_react_agent(llm, tools)
    """
    return [LangChainToolWrapper.from_hyperx_tool(tool) for tool in tools]


def _openai_schema_to_pydantic(
    name: str,
    parameters: dict[str, Any],
) -> Type[BaseModel]:
    """Convert OpenAI function parameters schema to a Pydantic model.

    This helper function takes an OpenAI function parameters schema
    and generates a Pydantic model class that can be used as
    args_schema in LangChain tools.

    Args:
        name: Name for the generated Pydantic model.
        parameters: OpenAI parameters schema dictionary.

    Returns:
        Dynamically created Pydantic model class.

    Example:
        >>> params = {
        ...     "type": "object",
        ...     "properties": {
        ...         "query": {"type": "string", "description": "Search query"},
        ...         "limit": {"type": "integer", "description": "Max results"},
        ...     },
        ...     "required": ["query"],
        ... }
        >>> Model = _openai_schema_to_pydantic("SearchArgs", params)
        >>> m = Model(query="test")
    """
    # Validate parameters is a dict
    if not isinstance(parameters, dict):
        # Return minimal valid schema for malformed input
        return create_model(name)

    # Validate and extract properties
    properties = parameters.get("properties", {})
    if not isinstance(properties, dict):
        properties = {}

    # Validate and extract required fields
    required_list = parameters.get("required", [])
    if not isinstance(required_list, list):
        required_list = []
    required = set(required_list)

    # Build field definitions for Pydantic
    field_definitions: dict[str, tuple[type, Any]] = {}

    for prop_name, prop_schema in properties.items():
        # Map JSON schema types to Python types
        python_type = _json_type_to_python(prop_schema.get("type", "string"))
        description = prop_schema.get("description", "")

        # Determine if field is required
        if prop_name in required:
            field_definitions[prop_name] = (
                python_type,
                Field(description=description),
            )
        else:
            field_definitions[prop_name] = (
                python_type | None,
                Field(default=None, description=description),
            )

    # Create the Pydantic model dynamically
    return create_model(name, **field_definitions)


def _json_type_to_python(json_type: str) -> type:
    """Map JSON schema type to Python type.

    Args:
        json_type: JSON schema type string.

    Returns:
        Corresponding Python type.
    """
    type_map = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": list,
        "object": dict,
    }
    return type_map.get(json_type, Any)
