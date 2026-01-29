"""
Agentic RAG Example
===================

This example demonstrates the Agentic RAG tools in HyperX:
- Creating tool collections
- Using quality signals for self-correction
- Different access levels
- Building autonomous agents
"""

from hyperx import HyperX
from hyperx.agents import create_tools, ToolCollection

client = HyperX("https://api.hyperxdb.dev", api_key="your-api-key")

# ===================
# Creating Tools
# ===================

# Create tools with different access levels
# "read" - SearchTool, PathsTool, LookupTool
# "explore" - + ExplorerTool, ExplainTool, RelationshipsTool
# "full" - + EntityCrudTool, HyperedgeCrudTool

# Read-only tools for safe RAG
read_tools = create_tools(client, access_level="read")
print(f"Read tools: {read_tools.tool_names}")

# Exploration tools for research agents
explore_tools = create_tools(client, access_level="explore")
print(f"Explore tools: {explore_tools.tool_names}")

# Full access for knowledge-building agents
full_tools = create_tools(client, access_level="full")
print(f"Full tools: {full_tools.tool_names}")

# ===================
# Using Tools
# ===================

tools = create_tools(client, access_level="explore")

# Search for entities
search_result = tools.execute(
    "search",
    query="transformer architecture attention mechanism",
    limit=10
)

print("\n=== Search Tool ===")
print(f"Success: {search_result.success}")
print(f"Found: {len(search_result.data.get('entities', []))} entities")

# Quality signals help agents decide if they need more info
print(f"\nQuality Signals:")
print(f"  Confidence: {search_result.quality.confidence:.2f}")
print(f"  Coverage: {search_result.quality.coverage:.2f}")
print(f"  Diversity: {search_result.quality.diversity:.2f}")
print(f"  Should retrieve more: {search_result.quality.should_retrieve_more}")

if search_result.quality.suggested_refinements:
    print(f"  Suggested refinements:")
    for ref in search_result.quality.suggested_refinements:
        print(f"    - {ref}")

# ===================
# Self-Correcting Agent Loop
# ===================

def agent_search(query: str, max_iterations: int = 3) -> dict:
    """Example of an agent that self-corrects based on quality signals."""

    tools = create_tools(client, access_level="explore")
    current_query = query
    all_results = []

    for i in range(max_iterations):
        print(f"\n--- Iteration {i + 1} ---")
        print(f"Query: {current_query}")

        result = tools.execute("search", query=current_query, limit=10)

        if not result.success:
            print(f"Search failed: {result.error}")
            break

        all_results.extend(result.data.get("entities", []))
        print(f"Found {len(result.data.get('entities', []))} entities")
        print(f"Confidence: {result.quality.confidence:.2f}")

        # Check if we should continue
        if not result.quality.should_retrieve_more:
            print("Quality signals indicate sufficient coverage")
            break

        # Use suggested refinements to improve the query
        if result.quality.suggested_refinements:
            current_query = result.quality.suggested_refinements[0]
            print(f"Refining query to: {current_query}")
        else:
            break

    return {"entities": all_results, "iterations": i + 1}

# Run the self-correcting search
results = agent_search("machine learning models")

# ===================
# Path Finding Tool
# ===================

# Find connections between entities
paths_result = tools.execute(
    "paths",
    source_id="entity-uuid-1",
    target_id="entity-uuid-2",
    max_hops=4
)

print("\n=== Paths Tool ===")
if paths_result.success:
    path = paths_result.data
    print(f"Found path with {path.get('hops', 0)} hops")
    print(f"Confidence: {paths_result.quality.confidence:.2f}")

# ===================
# Explorer Tool
# ===================

# Explore neighborhood of an entity
explore_result = tools.execute(
    "explorer",
    entity_id="entity-uuid",
    depth=2,
    max_entities=50
)

print("\n=== Explorer Tool ===")
if explore_result.success:
    neighborhood = explore_result.data
    print(f"Found {len(neighborhood.get('entities', []))} connected entities")
    print(f"Found {len(neighborhood.get('hyperedges', []))} relationships")

# ===================
# Explain Tool
# ===================

# Get a natural language explanation of an entity's context
explain_result = tools.execute(
    "explain",
    entity_id="entity-uuid"
)

print("\n=== Explain Tool ===")
if explain_result.success:
    print(f"Explanation:\n{explain_result.data.get('explanation', '')}")

# ===================
# Relationships Tool
# ===================

# Get all relationships for an entity
rel_result = tools.execute(
    "relationships",
    entity_id="entity-uuid",
    relationship_types=["authorship", "citation"]
)

print("\n=== Relationships Tool ===")
if rel_result.success:
    for rel in rel_result.data.get("relationships", []):
        print(f"  {rel['edge_type']}: {rel['connected_entities']}")

# ===================
# CRUD Tools (Full Access)
# ===================

full_tools = create_tools(client, access_level="full")

# Create entity via tool
create_result = full_tools.execute(
    "entity_crud",
    operation="create",
    label="New Concept",
    entity_type="Concept",
    description="A concept created by an agent",
    attributes={"source": "agent", "confidence": 0.95}
)

print("\n=== Entity CRUD Tool ===")
if create_result.success:
    new_entity = create_result.data
    print(f"Created: {new_entity.get('label')} (ID: {new_entity.get('id')})")

# Create hyperedge via tool
edge_result = full_tools.execute(
    "hyperedge_crud",
    operation="create",
    edge_type="discovered_relationship",
    members=[
        {"entity_id": "uuid-1", "role": "subject"},
        {"entity_id": "uuid-2", "role": "object"}
    ],
    attributes={"discovered_by": "agent", "confidence": 0.87}
)

print("\n=== Hyperedge CRUD Tool ===")
if edge_result.success:
    print(f"Created relationship: {edge_result.data.get('edge_type')}")

# ===================
# Tool Metadata
# ===================

print("\n=== Available Tools ===")
for name, tool in tools.tools.items():
    print(f"\n{name}:")
    print(f"  Description: {tool.description}")
    print(f"  Parameters: {list(tool.parameters.keys())}")
