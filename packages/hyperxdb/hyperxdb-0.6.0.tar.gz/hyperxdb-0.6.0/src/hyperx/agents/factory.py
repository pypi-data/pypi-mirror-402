"""Factory functions for creating HyperX agent tools.

This module provides the `create_tools()` factory function and `ToolCollection`
class for building sets of agent tools with configurable access levels.

Example:
    >>> from hyperx import HyperX
    >>> from hyperx.agents import create_tools
    >>>
    >>> client = HyperX(api_key="hx_sk_...")
    >>> tools = create_tools(client, level="explore")
    >>>
    >>> # Get OpenAI function schemas
    >>> schemas = tools.schemas
    >>>
    >>> # Execute tool by name
    >>> result = tools.execute("hyperx_search", query="React hooks")
    >>>
    >>> # List available tools
    >>> print(tools.names)
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, Literal

from hyperx.agents.base import BaseTool, ToolResult
from hyperx.agents.tools import (
    EntityCrudTool,
    ExplainTool,
    ExplorerTool,
    HyperedgeCrudTool,
    LookupTool,
    PathsTool,
    RelationshipsTool,
    SearchTool,
)

if TYPE_CHECKING:
    from hyperx import HyperX


AccessLevel = Literal["read", "explore", "full"]


class ToolCollection:
    """A collection of HyperX agent tools with convenience methods.

    ToolCollection provides a container for multiple tools with methods
    to execute tools by name, get OpenAI schemas, and iterate over tools.

    The collection supports:
        - Iteration: `for tool in collection`
        - Length: `len(collection)`
        - Contains: `"hyperx_search" in collection`
        - Named access: `collection.get("hyperx_search")`
        - Execution: `collection.execute("hyperx_search", query="test")`

    Attributes:
        names: List of all tool names in the collection.
        schemas: List of OpenAI function schemas for all tools.

    Example:
        >>> from hyperx import HyperX
        >>> from hyperx.agents import create_tools
        >>>
        >>> client = HyperX(api_key="hx_sk_...")
        >>> tools = create_tools(client, level="explore")
        >>>
        >>> # Iterate over tools
        >>> for tool in tools:
        ...     print(f"{tool.name}: {tool.description}")
        >>>
        >>> # Get OpenAI schemas
        >>> schemas = tools.schemas
        >>> # Use in OpenAI API call
        >>> response = openai.chat.completions.create(
        ...     model="gpt-4",
        ...     messages=[...],
        ...     tools=schemas,
        ... )
        >>>
        >>> # Execute a tool by name
        >>> result = tools.execute("hyperx_search", query="React hooks")
        >>> if result.success:
        ...     print(result.data)
    """

    def __init__(self, tools: list[BaseTool]) -> None:
        """Initialize the ToolCollection.

        Args:
            tools: List of tool instances to include in the collection.
        """
        self._tools = tools
        self._tools_by_name: dict[str, BaseTool] = {t.name: t for t in tools}

    def __iter__(self) -> Iterator[BaseTool]:
        """Iterate over tools in the collection.

        Yields:
            Each tool in the collection.
        """
        return iter(self._tools)

    def __len__(self) -> int:
        """Return the number of tools in the collection.

        Returns:
            Number of tools.
        """
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        """Check if a tool with the given name exists.

        Args:
            name: Name of the tool to check for.

        Returns:
            True if a tool with that name exists, False otherwise.
        """
        return name in self._tools_by_name

    @property
    def names(self) -> list[str]:
        """List of all tool names in the collection.

        Returns:
            List of tool name strings.
        """
        return list(self._tools_by_name.keys())

    @property
    def schemas(self) -> list[dict[str, Any]]:
        """List of OpenAI function schemas for all tools.

        Returns:
            List of OpenAI-compatible function schema dictionaries.

        Example:
            >>> schemas = tools.schemas
            >>> # Use in OpenAI API call
            >>> response = openai.chat.completions.create(
            ...     model="gpt-4",
            ...     messages=[...],
            ...     tools=schemas,
            ... )
        """
        return [t.to_openai_schema() for t in self._tools]

    def get(self, name: str) -> BaseTool:
        """Get a tool by name.

        Args:
            name: Name of the tool to retrieve.

        Returns:
            The tool instance.

        Raises:
            KeyError: If no tool with that name exists.

        Example:
            >>> search = tools.get("hyperx_search")
            >>> result = search.run(query="React hooks")
        """
        if name not in self._tools_by_name:
            raise KeyError(f"Tool not found: {name}")
        return self._tools_by_name[name]

    def execute(self, name: str, **kwargs: Any) -> ToolResult:
        """Execute a tool by name with the given arguments.

        This is a convenience method that looks up the tool by name
        and calls its `run()` method with the provided arguments.

        Args:
            name: Name of the tool to execute.
            **kwargs: Arguments to pass to the tool's run method.

        Returns:
            ToolResult from the tool execution.

        Raises:
            KeyError: If no tool with that name exists.

        Example:
            >>> result = tools.execute("hyperx_search", query="React hooks")
            >>> if result.success:
            ...     print(result.data)
        """
        tool = self.get(name)
        return tool.run(**kwargs)

    async def aexecute(self, name: str, **kwargs: Any) -> ToolResult:
        """Execute a tool asynchronously by name with the given arguments.

        This is a convenience method that looks up the tool by name
        and calls its `arun()` method with the provided arguments.

        Args:
            name: Name of the tool to execute.
            **kwargs: Arguments to pass to the tool's arun method.

        Returns:
            ToolResult from the tool execution.

        Raises:
            KeyError: If no tool with that name exists.

        Example:
            >>> result = await tools.aexecute("hyperx_search", query="React hooks")
            >>> if result.success:
            ...     print(result.data)
        """
        tool = self.get(name)
        return await tool.arun(**kwargs)


def create_tools(
    client: HyperX,
    *,
    level: AccessLevel = "read",
    # SearchTool kwargs
    search_mode: Literal["hybrid", "vector", "text"] | None = None,
    vector_weight: float | None = None,
    reranker: Any | None = None,
    default_limit: int | None = None,
    expand_graph: bool | None = None,
    # PathsTool kwargs
    default_max_hops: int | None = None,
    default_k_paths: int | None = None,
    # ExplorerTool kwargs (uses default_max_hops too)
) -> ToolCollection:
    """Create a collection of HyperX agent tools with the specified access level.

    This factory function creates a complete set of tools based on the
    specified access level. Each level builds on the previous:

        - "read": SearchTool, PathsTool, LookupTool (read-only operations)
        - "explore": read + ExplorerTool, ExplainTool, RelationshipsTool
        - "full": explore + EntityCrudTool, HyperedgeCrudTool

    Args:
        client: HyperX client instance for API calls.
        level: Access level determining which tools to include.
            Defaults to "read".
        search_mode: Search mode for SearchTool ("hybrid", "vector", "text").
            Defaults to "hybrid".
        vector_weight: Weight for vector similarity in hybrid search (0.0-1.0).
        reranker: Optional callable to rerank search results.
        default_limit: Default number of search results to return.
        expand_graph: Whether to expand search results by following edges.
        default_max_hops: Default max hops for PathsTool and ExplorerTool.
        default_k_paths: Default number of paths for PathsTool.

    Returns:
        ToolCollection containing the tools for the specified access level.

    Raises:
        ValueError: If an invalid access level is specified.

    Example:
        >>> from hyperx import HyperX
        >>> from hyperx.agents import create_tools
        >>>
        >>> client = HyperX(api_key="hx_sk_...")
        >>>
        >>> # Create read-only tools (default)
        >>> tools = create_tools(client)
        >>> print(tools.names)
        ['hyperx_search', 'hyperx_find_paths', 'hyperx_lookup']
        >>>
        >>> # Create explore-level tools
        >>> tools = create_tools(client, level="explore")
        >>> print(len(tools))
        6
        >>>
        >>> # Create full-access tools with custom settings
        >>> tools = create_tools(
        ...     client,
        ...     level="full",
        ...     search_mode="hybrid",
        ...     default_limit=20,
        ...     default_max_hops=5,
        ... )
        >>>
        >>> # Get OpenAI function schemas
        >>> schemas = tools.schemas
        >>>
        >>> # Execute tool by name
        >>> result = tools.execute("hyperx_search", query="React hooks")
    """
    valid_levels = {"read", "explore", "full"}
    if level not in valid_levels:
        raise ValueError(f"Invalid level '{level}'. Must be one of: {', '.join(valid_levels)}")

    tools: list[BaseTool] = []

    # Build SearchTool kwargs
    search_kwargs: dict[str, Any] = {}
    if search_mode is not None:
        search_kwargs["mode"] = search_mode
    if vector_weight is not None:
        search_kwargs["vector_weight"] = vector_weight
    if reranker is not None:
        search_kwargs["reranker"] = reranker
    if default_limit is not None:
        search_kwargs["default_limit"] = default_limit
    if expand_graph is not None:
        search_kwargs["expand_graph"] = expand_graph

    # Build PathsTool kwargs
    paths_kwargs: dict[str, Any] = {}
    if default_max_hops is not None:
        paths_kwargs["default_max_hops"] = default_max_hops
    if default_k_paths is not None:
        paths_kwargs["default_k_paths"] = default_k_paths

    # Build ExplorerTool kwargs
    explorer_kwargs: dict[str, Any] = {}
    if default_max_hops is not None:
        explorer_kwargs["default_max_hops"] = default_max_hops

    # === Read Level Tools ===
    # Always included at all levels
    tools.append(SearchTool(client, **search_kwargs))
    tools.append(PathsTool(client, **paths_kwargs))
    tools.append(LookupTool(client))

    # === Explore Level Tools ===
    # Included at "explore" and "full" levels
    if level in ("explore", "full"):
        tools.append(ExplorerTool(client, **explorer_kwargs))
        tools.append(ExplainTool(client))
        tools.append(RelationshipsTool(client))

    # === Full Level Tools ===
    # Only included at "full" level
    if level == "full":
        tools.append(EntityCrudTool(client))
        tools.append(HyperedgeCrudTool(client))

    return ToolCollection(tools)
