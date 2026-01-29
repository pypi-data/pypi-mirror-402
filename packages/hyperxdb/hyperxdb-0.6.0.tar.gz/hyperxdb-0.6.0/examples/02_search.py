"""
Search Example
==============

This example demonstrates HyperX search capabilities:
- Hybrid search (vector + text)
- Vector-only search
- Text-only search (BM25)
- Filtering and faceting
"""

from hyperx import HyperX

client = HyperX("https://api.hyperxdb.dev", api_key="your-api-key")

# ===================
# Hybrid Search
# ===================

# Hybrid search combines semantic (vector) and keyword (BM25) matching
results = client.search.hybrid(
    query="machine learning transformer architecture",
    limit=10,
    alpha=0.7  # 70% vector, 30% text
)

print("=== Hybrid Search Results ===")
for result in results.items:
    print(f"  [{result.score:.3f}] {result.entity.label}")
    print(f"           Type: {result.entity.entity_type}")

# ===================
# Vector Search
# ===================

# Pure semantic search - finds conceptually similar entities
# even if they don't share exact keywords
vector_results = client.search.vector(
    query="deep neural networks for NLP",
    limit=5
)

print("\n=== Vector Search Results ===")
for result in vector_results.items:
    print(f"  [{result.score:.3f}] {result.entity.label}")

# ===================
# Text Search (BM25)
# ===================

# Keyword-based search with TF-IDF scoring
text_results = client.search.text(
    query="attention mechanism",
    limit=5
)

print("\n=== Text Search Results ===")
for result in text_results.items:
    print(f"  [{result.score:.3f}] {result.entity.label}")

# ===================
# Filtered Search
# ===================

# Search with entity type filter
filtered = client.search.hybrid(
    query="neural network",
    limit=10,
    entity_types=["Concept", "Publication"],
    min_score=0.5
)

print("\n=== Filtered Search (Concepts & Publications) ===")
for result in filtered.items:
    print(f"  [{result.score:.3f}] {result.entity.label} ({result.entity.entity_type})")

# ===================
# Search with Role Filter
# ===================

# Find entities that play specific roles in hyperedges
role_filtered = client.search.hybrid(
    query="researcher",
    limit=10,
    role_filter="author"  # Only entities with "author" role
)

print("\n=== Search with Role Filter ===")
for result in role_filtered.items:
    print(f"  [{result.score:.3f}] {result.entity.label}")

# ===================
# Search Hyperedges
# ===================

# Search for relationships, not just entities
edge_results = client.search.hyperedges(
    query="collaboration research",
    edge_types=["authorship", "collaboration"],
    limit=5
)

print("\n=== Hyperedge Search Results ===")
for result in edge_results.items:
    print(f"  [{result.score:.3f}] {result.hyperedge.edge_type}")
    print(f"           Members: {len(result.hyperedge.members)}")

# ===================
# Pagination
# ===================

# Handle large result sets
page1 = client.search.hybrid(query="AI", limit=10, offset=0)
page2 = client.search.hybrid(query="AI", limit=10, offset=10)

print(f"\n=== Pagination ===")
print(f"Page 1: {len(page1.items)} results")
print(f"Page 2: {len(page2.items)} results")
print(f"Total available: {page1.total}")
