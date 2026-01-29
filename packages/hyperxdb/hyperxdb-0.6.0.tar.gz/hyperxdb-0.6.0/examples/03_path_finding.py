"""
Path Finding Example
====================

This example demonstrates multi-hop reasoning with HyperX:
- Finding paths between entities
- K-shortest paths
- Path constraints
- Using paths for RAG context
"""

from hyperx import HyperX

client = HyperX("https://api.hyperxdb.dev", api_key="your-api-key")

# ===================
# Basic Path Finding
# ===================

# Find how two entities are connected
# Example: How is "BERT" connected to "ImageNet"?

source_id = "entity-uuid-for-bert"
target_id = "entity-uuid-for-imagenet"

path_result = client.paths.find(
    source=source_id,
    target=target_id,
    max_hops=5
)

print("=== Path Finding ===")
print(f"Found path with {path_result.hops} hops")
print("\nPath:")
for i, step in enumerate(path_result.steps):
    print(f"  Step {i + 1}:")
    print(f"    Entity: {step.entity.label}")
    print(f"    Via: {step.hyperedge.edge_type if step.hyperedge else 'START'}")
    print(f"    Role: {step.role}")

# ===================
# K-Shortest Paths
# ===================

# Find multiple paths between entities
paths = client.paths.find_k_shortest(
    source=source_id,
    target=target_id,
    k=3,
    max_hops=6
)

print(f"\n=== K-Shortest Paths (k=3) ===")
print(f"Found {len(paths)} paths")

for i, path in enumerate(paths):
    print(f"\nPath {i + 1} ({path.hops} hops):")
    entities = [step.entity.label for step in path.steps]
    print(f"  {' -> '.join(entities)}")

# ===================
# Path Constraints
# ===================

# Find paths that go through specific types of relationships
constrained_path = client.paths.find(
    source=source_id,
    target=target_id,
    max_hops=5,
    edge_types=["authorship", "citation", "builds_on"],  # Only these relationship types
    min_intersection_size=2  # Hyperedges must have at least 2 shared entities
)

print("\n=== Constrained Path ===")
if constrained_path:
    print(f"Found path: {constrained_path.hops} hops")
    for step in constrained_path.steps:
        if step.hyperedge:
            print(f"  {step.entity.label} --[{step.hyperedge.edge_type}]-->")
else:
    print("No path found with constraints")

# ===================
# Path for RAG Context
# ===================

# Use path finding to build context for LLM
def build_rag_context(source_id: str, target_id: str) -> str:
    """Build RAG context from path between entities."""

    path = client.paths.find(
        source=source_id,
        target=target_id,
        max_hops=4
    )

    if not path:
        return "No connection found between entities."

    context_parts = []
    context_parts.append(f"Connection path ({path.hops} hops):\n")

    for i, step in enumerate(path.steps):
        entity = step.entity
        context_parts.append(f"{i + 1}. {entity.label} ({entity.entity_type})")
        if entity.description:
            context_parts.append(f"   {entity.description}")

        if step.hyperedge:
            edge = step.hyperedge
            context_parts.append(f"   Connected via: {edge.edge_type}")
            if edge.attributes:
                attrs = ", ".join(f"{k}={v}" for k, v in edge.attributes.items())
                context_parts.append(f"   Attributes: {attrs}")

        context_parts.append("")

    return "\n".join(context_parts)

# Build context for a question like:
# "How is BERT related to ImageNet?"
context = build_rag_context(source_id, target_id)
print("\n=== RAG Context ===")
print(context)

# ===================
# Bidirectional Search
# ===================

# Search from both ends (faster for long paths)
bidirectional_path = client.paths.find(
    source=source_id,
    target=target_id,
    max_hops=8,
    bidirectional=True  # Search from both source and target
)

print("\n=== Bidirectional Search ===")
if bidirectional_path:
    print(f"Found path: {bidirectional_path.hops} hops")

# ===================
# Path Metadata
# ===================

# Get detailed metadata about the path
print("\n=== Path Metadata ===")
print(f"Total entities: {len(path_result.steps)}")
print(f"Relationship types used: {set(s.hyperedge.edge_type for s in path_result.steps if s.hyperedge)}")
print(f"Entity types: {set(s.entity.entity_type for s in path_result.steps)}")
