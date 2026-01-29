"""
Temporal Queries Example
========================

This example demonstrates bi-temporal support in HyperX:
- Creating entities with validity periods
- Querying at specific points in time
- Entity lifecycle management
- Version history
"""

from datetime import datetime, timedelta
from hyperx import HyperX

client = HyperX("https://api.hyperxdb.dev", api_key="your-api-key")

# ===================
# Temporal Entity Creation
# ===================

# Create an entity with a validity period
# "This fact is valid from Jan 1, 2024"
employee = client.entities.create(
    label="Alice Chen",
    entity_type="Person",
    description="Software Engineer at TechCorp",
    attributes={
        "role": "Software Engineer",
        "department": "Engineering",
        "salary_band": "L4"
    },
    valid_from=datetime(2024, 1, 1),
    valid_until=None  # Still valid (no end date)
)

print(f"Created: {employee.label}")
print(f"  Valid from: {employee.valid_from}")
print(f"  Valid until: {employee.valid_until or 'ongoing'}")
print(f"  State: {employee.state}")

# ===================
# Updating with Temporal Awareness
# ===================

# When Alice gets promoted, we create a new version
# The old version remains for historical queries
promoted = client.entities.update(
    employee.id,
    attributes={
        "role": "Senior Software Engineer",
        "department": "Engineering",
        "salary_band": "L5"
    },
    valid_from=datetime(2024, 6, 1)  # Promotion effective June 1
)

print(f"\nUpdated: {promoted.label}")
print(f"  New role: {promoted.attributes['role']}")
print(f"  Valid from: {promoted.valid_from}")

# ===================
# Point-in-Time Queries
# ===================

# Query what was true at a specific time
# "What was Alice's role in March 2024?"
march_state = client.entities.get(
    employee.id,
    point_in_time=datetime(2024, 3, 15)
)

print(f"\n=== Point-in-Time Query (March 2024) ===")
print(f"Role: {march_state.attributes['role']}")  # "Software Engineer"

# "What is Alice's role now?"
current_state = client.entities.get(
    employee.id,
    point_in_time=datetime.now()
)

print(f"\n=== Current State ===")
print(f"Role: {current_state.attributes['role']}")  # "Senior Software Engineer"

# ===================
# Temporal Hyperedges
# ===================

# Create a project assignment with time bounds
project = client.entities.create(
    label="Project Phoenix",
    entity_type="Project",
    description="Next-gen platform rewrite"
)

assignment = client.hyperedges.create(
    edge_type="project_assignment",
    members=[
        {"entity_id": employee.id, "role": "tech_lead"},
        {"entity_id": project.id, "role": "project"}
    ],
    attributes={"allocation": "100%"},
    valid_from=datetime(2024, 2, 1),
    valid_until=datetime(2024, 12, 31)  # Assignment ends Dec 31
)

print(f"\n=== Temporal Hyperedge ===")
print(f"Assignment: {assignment.edge_type}")
print(f"Valid: {assignment.valid_from} to {assignment.valid_until}")

# ===================
# Entity Lifecycle
# ===================

# Deprecate an entity (soft delete with history preservation)
old_project = client.entities.create(
    label="Legacy System",
    entity_type="Project",
    description="The old system being replaced"
)

# Mark as deprecated
deprecated = client.entities.deprecate(
    old_project.id,
    reason="Replaced by Project Phoenix"
)

print(f"\n=== Deprecated Entity ===")
print(f"Entity: {deprecated.label}")
print(f"State: {deprecated.state}")  # "Deprecated"

# Supersede with a new version
superseded = client.entities.supersede(
    old_project.id,
    successor_id=project.id,
    reason="Migrated to new platform"
)

print(f"\n=== Superseded Entity ===")
print(f"Entity: {superseded.label}")
print(f"State: {superseded.state}")  # "Superseded"
print(f"Superseded by: {superseded.superseded_by}")

# Retire permanently
retired = client.entities.retire(
    old_project.id,
    reason="Decommissioned after migration complete"
)

print(f"\n=== Retired Entity ===")
print(f"Entity: {retired.label}")
print(f"State: {retired.state}")  # "Retired"

# ===================
# Version History
# ===================

# Get full history of an entity
history = client.entities.history(employee.id)

print(f"\n=== Entity History ===")
print(f"Total versions: {len(history)}")
for version in history:
    print(f"\nVersion {version.version}:")
    print(f"  Valid from: {version.valid_from}")
    print(f"  State: {version.state}")
    print(f"  Role: {version.attributes.get('role')}")

# ===================
# Listing with Temporal Filters
# ===================

# List entities that were valid at a specific time
past_employees = client.entities.list(
    entity_type="Person",
    valid_at=datetime(2024, 3, 1),  # Who was employed in March?
    limit=100
)

print(f"\n=== Employees valid in March 2024 ===")
print(f"Found: {len(past_employees.items)}")

# Include historical (superseded/deprecated) entities
all_projects = client.entities.list(
    entity_type="Project",
    include_historical=True,  # Include non-active states
    limit=100
)

print(f"\n=== All Projects (including historical) ===")
for proj in all_projects.items:
    print(f"  {proj.label} - {proj.state}")

# ===================
# Reactivation
# ===================

# Reactivate a deprecated entity
# (Maybe we need that legacy system back temporarily)
reactivated = client.entities.reactivate(old_project.id)

print(f"\n=== Reactivated Entity ===")
print(f"Entity: {reactivated.label}")
print(f"State: {reactivated.state}")  # "Active"
