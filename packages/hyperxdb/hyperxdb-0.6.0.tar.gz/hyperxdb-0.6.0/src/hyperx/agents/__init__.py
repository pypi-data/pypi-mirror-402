"""HyperX agent tools for agentic RAG workflows.

This module provides base classes, protocols, and ready-to-use tools
for building agent systems that integrate with LLM frameworks.

The recommended way to create tools is using the `create_tools()` factory:

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
    >>> if result.success:
    ...     print(result.data)

Access levels:
    - "read": SearchTool, PathsTool, LookupTool (default)
    - "explore": read + ExplorerTool, ExplainTool, RelationshipsTool
    - "full": explore + EntityCrudTool, HyperedgeCrudTool

You can also use individual tools directly:

Example:
    >>> from hyperx import HyperX
    >>> from hyperx.agents import SearchTool, PathsTool, LookupTool, QualitySignals, ToolResult
    >>>
    >>> # Use ready-to-use SearchTool
    >>> client = HyperX(api_key="hx_sk_...")
    >>> search = SearchTool(client, mode="hybrid", default_limit=10)
    >>> result = search.run(query="react hooks")
    >>> if result.quality.should_retrieve_more:
    ...     print("Consider retrieving more data")
    >>>
    >>> # Use PathsTool for multi-hop reasoning
    >>> paths_tool = PathsTool(client, default_max_hops=4)
    >>> result = paths_tool.run(from_entity="e:useState", to_entity="e:redux")
    >>> if result.success:
    ...     for path in result.data["paths"]:
    ...         print(f"Path via: {path['hyperedges']}")
    >>>
    >>> # Use LookupTool to retrieve by ID
    >>> lookup = LookupTool(client)
    >>> result = lookup.run(id="e:react")
    >>> if result.success:
    ...     print(result.data["name"])
    >>>
    >>> # Explore neighbors within N hops
    >>> explorer = ExplorerTool(client, default_max_hops=2)
    >>> result = explorer.run(entity_id="e:react")
    >>> if result.success:
    ...     for neighbor in result.data["neighbors"]:
    ...         print(f"{neighbor['name']} at distance {neighbor['distance']}")
    >>>
    >>> # Get explanations for paths/relationships
    >>> explain = ExplainTool(client)
    >>> result = explain.run(ids=["h:react-hooks", "h:hooks-state"])
    >>> if result.success:
    ...     print(result.data["narrative"])
    >>>
    >>> # List all relationships for an entity
    >>> relationships = RelationshipsTool(client)
    >>> result = relationships.run(entity_id="e:react", role="subject")
    >>> if result.success:
    ...     for rel in result.data["relationships"]:
    ...         print(f"{rel['description']} (role: {rel['entity_role']})")
    >>>
    >>> # Or implement your own tool
    >>> class MySearchTool:
    ...     @property
    ...     def name(self) -> str:
    ...         return "my_search"
    ...
    ...     @property
    ...     def description(self) -> str:
    ...         return "Search the knowledge graph"
    ...
    ...     def run(self, query: str) -> ToolResult:
    ...         # Implementation here
    ...         pass
    ...
    ...     async def arun(self, query: str) -> ToolResult:
    ...         # Async implementation here
    ...         pass
    ...
    ...     def to_openai_schema(self) -> dict:
    ...         return {
    ...             "type": "function",
    ...             "function": {
    ...                 "name": self.name,
    ...                 "description": self.description,
    ...                 "parameters": {
    ...                     "type": "object",
    ...                     "properties": {
    ...                         "query": {"type": "string"}
    ...                     },
    ...                     "required": ["query"]
    ...                 }
    ...             }
    ...         }

For LangChain integration, see hyperx.agents.langchain:

Example:
    >>> from hyperx import HyperX
    >>> from hyperx.agents.langchain import HyperXToolkit, as_langchain_tools
    >>>
    >>> # Quick setup with toolkit
    >>> db = HyperX(api_key="hx_sk_...")
    >>> toolkit = HyperXToolkit(client=db, level="explore")
    >>> tools = toolkit.get_tools()
    >>>
    >>> # Use with LangGraph
    >>> from langgraph.prebuilt import create_react_agent
    >>> agent = create_react_agent(llm, tools)
"""

from hyperx.agents.base import (
    BaseTool,
    QualitySignals,
    ToolError,
    ToolResult,
)
from hyperx.agents.factory import ToolCollection, create_tools
from hyperx.agents.quality import QualityAnalyzer
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

__all__ = [
    # Base classes and protocols
    "BaseTool",
    "QualityAnalyzer",
    "QualitySignals",
    "ToolCollection",
    "ToolError",
    "ToolResult",
    # Factory
    "create_tools",
    # Read-level tools
    "SearchTool",
    "PathsTool",
    "LookupTool",
    # Explore-level tools
    "ExplorerTool",
    "ExplainTool",
    "RelationshipsTool",
    # Full-level tools
    "EntityCrudTool",
    "HyperedgeCrudTool",
    # LangChain integration (optional)
    "HyperXToolkit",
    "as_langchain_tools",
    # LlamaIndex integration (optional)
    "HyperXToolSpec",
    "as_llamaindex_tools",
]


def __getattr__(name: str):
    """Lazy import for optional framework integrations."""
    if name in ("HyperXToolkit", "as_langchain_tools"):
        try:
            from hyperx.agents.langchain import HyperXToolkit, as_langchain_tools

            if name == "HyperXToolkit":
                return HyperXToolkit
            return as_langchain_tools
        except ImportError:
            raise ImportError(
                f"{name} requires langchain-core. "
                "Install it with: pip install hyperxdb[langchain]"
            ) from None

    if name in ("HyperXToolSpec", "as_llamaindex_tools"):
        try:
            from hyperx.agents.llamaindex import HyperXToolSpec, as_llamaindex_tools

            if name == "HyperXToolSpec":
                return HyperXToolSpec
            return as_llamaindex_tools
        except ImportError:
            raise ImportError(
                f"{name} requires llama-index-core. "
                "Install it with: pip install hyperxdb[llamaindex]"
            ) from None

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
