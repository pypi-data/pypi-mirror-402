"""
Basic Usage Example
===================

This example demonstrates the fundamental operations with HyperX:
- Creating entities
- Creating hyperedges (N-ary relationships)
- Querying data
"""

from hyperx import HyperX

# Initialize client
client = HyperX(
    base_url="https://api.hyperxdb.dev",
    api_key="your-api-key"
)

# Or use context manager for automatic cleanup
with HyperX("https://api.hyperxdb.dev", api_key="your-api-key") as client:

    # ===================
    # Creating Entities
    # ===================

    # Create a person entity
    alice = client.entities.create(
        label="Alice Chen",
        entity_type="Person",
        description="Senior ML Engineer at TechCorp",
        attributes={
            "role": "ML Engineer",
            "department": "AI Research",
            "years_experience": 8
        }
    )
    print(f"Created: {alice.label} (ID: {alice.id})")

    # Create more entities
    bob = client.entities.create(
        label="Bob Smith",
        entity_type="Person",
        description="Data Scientist",
        attributes={"role": "Data Scientist", "department": "Analytics"}
    )

    paper = client.entities.create(
        label="Attention Is All You Need",
        entity_type="Publication",
        description="The transformer architecture paper",
        attributes={"year": 2017, "venue": "NeurIPS", "citations": 100000}
    )

    transformer = client.entities.create(
        label="Transformer Architecture",
        entity_type="Concept",
        description="A neural network architecture based on self-attention",
        attributes={"domain": "deep learning"}
    )

    # ===================
    # Creating Hyperedges
    # ===================

    # Hyperedges can connect multiple entities with semantic roles
    # This represents: "Alice and Bob co-authored this paper about transformers"
    authorship = client.hyperedges.create(
        edge_type="authorship",
        members=[
            {"entity_id": alice.id, "role": "primary_author"},
            {"entity_id": bob.id, "role": "co_author"},
            {"entity_id": paper.id, "role": "publication"},
            {"entity_id": transformer.id, "role": "subject"}
        ],
        attributes={
            "contribution_type": "research",
            "year": 2017
        }
    )
    print(f"Created hyperedge: {authorship.edge_type} with {len(authorship.members)} members")

    # Another hyperedge: "Alice mentors Bob on ML"
    mentorship = client.hyperedges.create(
        edge_type="mentorship",
        members=[
            {"entity_id": alice.id, "role": "mentor"},
            {"entity_id": bob.id, "role": "mentee"},
            {"entity_id": transformer.id, "role": "topic"}
        ],
        attributes={"started": "2023-01", "status": "active"}
    )

    # ===================
    # Querying Data
    # ===================

    # Get entity by ID
    retrieved = client.entities.get(alice.id)
    print(f"\nRetrieved: {retrieved.label}")
    print(f"  Type: {retrieved.entity_type}")
    print(f"  Attributes: {retrieved.attributes}")

    # List entities with filtering
    people = client.entities.list(entity_type="Person", limit=10)
    print(f"\nFound {len(people.items)} people")
    for person in people.items:
        print(f"  - {person.label}")

    # Get hyperedges for an entity
    alice_edges = client.hyperedges.list(entity_id=alice.id)
    print(f"\nAlice is involved in {len(alice_edges.items)} relationships")

    # ===================
    # Updating Entities
    # ===================

    # Update entity attributes
    updated = client.entities.update(
        alice.id,
        attributes={
            **alice.attributes,
            "years_experience": 9,  # Promotion!
            "title": "Principal ML Engineer"
        }
    )
    print(f"\nUpdated Alice: {updated.attributes.get('title')}")

    # ===================
    # Cleanup (optional)
    # ===================

    # Delete entities (cascades to hyperedges)
    # client.entities.delete(alice.id)
    # client.entities.delete(bob.id)
