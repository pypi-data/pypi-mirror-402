"""
Batch Operations Example
========================

This example demonstrates efficient bulk operations with HyperX:
- Batch entity creation
- Batch hyperedge creation
- Batch updates and deletes
- Import/export workflows
"""

from hyperx import HyperX
from datetime import datetime

client = HyperX("https://api.hyperxdb.dev", api_key="your-api-key")

# ===================
# Batch Entity Creation
# ===================

# Prepare entities for batch creation
entities_data = [
    {
        "label": f"Research Paper {i}",
        "entity_type": "Publication",
        "description": f"A research paper about topic {i}",
        "attributes": {
            "year": 2020 + (i % 5),
            "citations": i * 10,
            "venue": ["NeurIPS", "ICML", "ICLR", "ACL"][i % 4]
        }
    }
    for i in range(100)
]

print("=== Batch Entity Creation ===")
print(f"Creating {len(entities_data)} entities...")

# Batch create (much faster than individual creates)
result = client.entities.batch_create(entities_data)

print(f"Created: {len(result.created)} entities")
print(f"Failed: {len(result.failed)} entities")

if result.failed:
    for failure in result.failed[:5]:  # Show first 5 failures
        print(f"  Failed: {failure.label} - {failure.error}")

# Get the created entity IDs
entity_ids = [e.id for e in result.created]

# ===================
# Batch Hyperedge Creation
# ===================

# Create relationships between entities
hyperedges_data = []

for i in range(0, len(entity_ids) - 1, 2):
    hyperedges_data.append({
        "edge_type": "cites",
        "members": [
            {"entity_id": entity_ids[i], "role": "citing_paper"},
            {"entity_id": entity_ids[i + 1], "role": "cited_paper"}
        ],
        "attributes": {
            "citation_context": "methodology",
            "year": 2024
        }
    })

print(f"\n=== Batch Hyperedge Creation ===")
print(f"Creating {len(hyperedges_data)} hyperedges...")

edge_result = client.hyperedges.batch_create(hyperedges_data)

print(f"Created: {len(edge_result.created)} hyperedges")
print(f"Failed: {len(edge_result.failed)} hyperedges")

# ===================
# Batch Update
# ===================

# Update multiple entities at once
updates = [
    {
        "id": entity_ids[i],
        "attributes": {
            "updated_at": datetime.now().isoformat(),
            "batch_updated": True
        }
    }
    for i in range(min(50, len(entity_ids)))
]

print(f"\n=== Batch Update ===")
print(f"Updating {len(updates)} entities...")

update_result = client.entities.batch_update(updates)

print(f"Updated: {len(update_result.updated)} entities")
print(f"Failed: {len(update_result.failed)} entities")

# ===================
# Batch Delete
# ===================

# Delete entities in batch (be careful!)
# This will also delete associated hyperedges

# Only delete a subset for this example
to_delete = entity_ids[80:100]  # Last 20 entities

print(f"\n=== Batch Delete ===")
print(f"Deleting {len(to_delete)} entities...")

delete_result = client.entities.batch_delete(to_delete)

print(f"Deleted: {len(delete_result.deleted)} entities")
print(f"Failed: {len(delete_result.failed)} entities")

# ===================
# Import from JSON
# ===================

import json

def import_from_json(filepath: str):
    """Import entities and hyperedges from a JSON file."""

    with open(filepath, 'r') as f:
        data = json.load(f)

    print(f"\n=== Importing from {filepath} ===")

    # Import entities first
    if 'entities' in data:
        print(f"Importing {len(data['entities'])} entities...")
        entity_result = client.entities.batch_create(data['entities'])
        print(f"  Created: {len(entity_result.created)}")

        # Build ID mapping (old_id -> new_id)
        id_mapping = {}
        for i, entity in enumerate(entity_result.created):
            if i < len(data['entities']):
                old_id = data['entities'][i].get('id')
                if old_id:
                    id_mapping[old_id] = entity.id

    # Import hyperedges with ID remapping
    if 'hyperedges' in data:
        print(f"Importing {len(data['hyperedges'])} hyperedges...")

        # Remap entity IDs in hyperedge members
        for edge in data['hyperedges']:
            for member in edge.get('members', []):
                old_id = member.get('entity_id')
                if old_id in id_mapping:
                    member['entity_id'] = id_mapping[old_id]

        edge_result = client.hyperedges.batch_create(data['hyperedges'])
        print(f"  Created: {len(edge_result.created)}")

    return id_mapping

# Example JSON file format:
# {
#   "entities": [
#     {"id": "old-1", "label": "Entity 1", "entity_type": "Concept", ...},
#     {"id": "old-2", "label": "Entity 2", "entity_type": "Person", ...}
#   ],
#   "hyperedges": [
#     {"edge_type": "related_to", "members": [{"entity_id": "old-1", "role": "source"}, ...]}
#   ]
# }

# import_from_json("./data/knowledge_graph.json")

# ===================
# Export to JSON
# ===================

def export_to_json(filepath: str, entity_types: list = None):
    """Export entities and hyperedges to a JSON file."""

    print(f"\n=== Exporting to {filepath} ===")

    # Export entities
    entities = []
    offset = 0
    limit = 100

    while True:
        page = client.entities.list(
            entity_type=entity_types[0] if entity_types and len(entity_types) == 1 else None,
            limit=limit,
            offset=offset
        )

        if not page.items:
            break

        for entity in page.items:
            if entity_types is None or entity.entity_type in entity_types:
                entities.append({
                    "id": entity.id,
                    "label": entity.label,
                    "entity_type": entity.entity_type,
                    "description": entity.description,
                    "attributes": entity.attributes
                })

        offset += limit
        if offset >= page.total:
            break

    print(f"  Exported {len(entities)} entities")

    # Export hyperedges
    hyperedges = []
    offset = 0

    while True:
        page = client.hyperedges.list(limit=limit, offset=offset)

        if not page.items:
            break

        for edge in page.items:
            hyperedges.append({
                "id": edge.id,
                "edge_type": edge.edge_type,
                "members": [
                    {"entity_id": m.entity_id, "role": m.role}
                    for m in edge.members
                ],
                "attributes": edge.attributes
            })

        offset += limit
        if offset >= page.total:
            break

    print(f"  Exported {len(hyperedges)} hyperedges")

    # Write to file
    with open(filepath, 'w') as f:
        json.dump({
            "entities": entities,
            "hyperedges": hyperedges,
            "exported_at": datetime.now().isoformat()
        }, f, indent=2)

    print(f"  Written to {filepath}")

# export_to_json("./data/export.json", entity_types=["Publication", "Person"])

# ===================
# Chunked Processing
# ===================

def process_in_chunks(items: list, chunk_size: int = 100):
    """Process large datasets in chunks to avoid memory issues."""

    print(f"\n=== Chunked Processing ===")
    print(f"Processing {len(items)} items in chunks of {chunk_size}")

    total_created = 0
    total_failed = 0

    for i in range(0, len(items), chunk_size):
        chunk = items[i:i + chunk_size]
        result = client.entities.batch_create(chunk)

        total_created += len(result.created)
        total_failed += len(result.failed)

        print(f"  Chunk {i // chunk_size + 1}: {len(result.created)} created, {len(result.failed)} failed")

    print(f"Total: {total_created} created, {total_failed} failed")
    return total_created, total_failed

# Example: Process 1000 entities in chunks of 100
# large_dataset = [{"label": f"Entity {i}", ...} for i in range(1000)]
# process_in_chunks(large_dataset, chunk_size=100)

# ===================
# Upsert (Create or Update)
# ===================

def batch_upsert(entities_data: list, key_field: str = "label"):
    """Create entities if they don't exist, update if they do."""

    print(f"\n=== Batch Upsert ===")

    # Get existing entities by key
    existing = {}
    for data in entities_data:
        key_value = data.get(key_field)
        if key_value:
            # Search for existing
            results = client.search.text(query=key_value, limit=1)
            for r in results.items:
                if r.entity.label == key_value:
                    existing[key_value] = r.entity.id

    # Split into creates and updates
    to_create = []
    to_update = []

    for data in entities_data:
        key_value = data.get(key_field)
        if key_value in existing:
            to_update.append({
                "id": existing[key_value],
                **{k: v for k, v in data.items() if k != key_field}
            })
        else:
            to_create.append(data)

    print(f"  To create: {len(to_create)}")
    print(f"  To update: {len(to_update)}")

    # Execute batch operations
    if to_create:
        create_result = client.entities.batch_create(to_create)
        print(f"  Created: {len(create_result.created)}")

    if to_update:
        update_result = client.entities.batch_update(to_update)
        print(f"  Updated: {len(update_result.updated)}")

# batch_upsert(entities_data)
