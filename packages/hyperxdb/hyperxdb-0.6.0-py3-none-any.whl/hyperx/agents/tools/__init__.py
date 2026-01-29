"""HyperX agent tools for agentic RAG workflows.

This module provides ready-to-use tools for building agentic RAG
systems with LLM frameworks like OpenAI, LangChain, and others.

Tools are organized by access level:
    - Read-only: SearchTool, PathsTool, LookupTool, ExplorerTool, ExplainTool, RelationshipsTool
    - Full access: EntityCrudTool, HyperedgeCrudTool

Example:
    >>> from hyperx import HyperX
    >>> from hyperx.agents.tools import SearchTool, PathsTool, LookupTool
    >>>
    >>> client = HyperX(api_key="hx_sk_...")
    >>> search = SearchTool(client, mode="hybrid", default_limit=10)
    >>>
    >>> # Use with OpenAI function calling
    >>> schema = search.to_openai_schema()
    >>>
    >>> # Execute search
    >>> result = search.run(query="react state management")
    >>> if result.quality.should_retrieve_more:
    ...     # Agent decides to retrieve more
    ...     result = search.run(query=result.quality.alternative_queries[0])
    >>>
    >>> # Find multi-hop paths between entities
    >>> paths_tool = PathsTool(client, default_max_hops=4)
    >>> result = paths_tool.run(from_entity="e:useState", to_entity="e:redux")
    >>> if result.success:
    ...     for path in result.data["paths"]:
    ...         print(f"Path cost: {path['cost']}")
    >>>
    >>> # Look up an entity or hyperedge by ID
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
    >>> # Create, update, delete entities (full access level)
    >>> from hyperx.agents.tools import EntityCrudTool
    >>> entity_tool = EntityCrudTool(client)
    >>> result = entity_tool.run(
    ...     action="create",
    ...     name="React",
    ...     entity_type="framework",
    ...     attributes={"version": "18.2"}
    ... )
    >>> if result.success:
    ...     print(f"Created entity: {result.data['id']}")
    >>>
    >>> # Create, update, deprecate, delete hyperedges (full access level)
    >>> from hyperx.agents.tools import HyperedgeCrudTool
    >>> edge_tool = HyperedgeCrudTool(client)
    >>> result = edge_tool.run(
    ...     action="create",
    ...     description="React provides Hooks",
    ...     participants=[
    ...         {"entity_id": "e:react", "role": "subject"},
    ...         {"entity_id": "e:hooks", "role": "object"},
    ...     ]
    ... )
    >>> if result.success:
    ...     print(f"Created hyperedge: {result.data['id']}")
"""

from hyperx.agents.tools.crud import EntityCrudTool, HyperedgeCrudTool
from hyperx.agents.tools.explorer import ExplainTool, ExplorerTool, RelationshipsTool
from hyperx.agents.tools.lookup import LookupTool
from hyperx.agents.tools.paths import PathsTool
from hyperx.agents.tools.search import SearchTool

__all__ = [
    "EntityCrudTool",
    "ExplainTool",
    "ExplorerTool",
    "HyperedgeCrudTool",
    "LookupTool",
    "PathsTool",
    "RelationshipsTool",
    "SearchTool",
]
