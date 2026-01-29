# HyperX Python SDK

The official Python SDK for [HyperX](https://hyperxdb.dev) - the knowledge layer for AI that outgrows vector search.

HyperX is a hypergraph database designed for AI/ML applications. Unlike vector databases that only find similar items, HyperX enables **multi-hop reasoning** across complex relationships - the kind of inference that RAG applications actually need.

## Installation

```bash
pip install hyperxdb
```

**Optional dependencies:**

```bash
pip install hyperxdb[redis]      # Redis caching backend
pip install hyperxdb[langchain]  # LangChain integration
pip install hyperxdb[llamaindex] # LlamaIndex integration
pip install hyperxdb[all]        # Everything
```

**Requirements:** Python 3.10+

## Quick Start

```python
from hyperx import HyperX

# Initialize the client
db = HyperX(api_key="hx_sk_live_abc123...")

# Create entities (nodes in the hypergraph)
react = db.entities.create(name="React", entity_type="framework")
hooks = db.entities.create(name="Hooks", entity_type="concept")

# Create hyperedges (n-ary relationships)
edge = db.hyperedges.create(
    description="React provides Hooks for state management",
    members=[
        {"entity_id": react.id, "role": "subject"},
        {"entity_id": hooks.id, "role": "object"},
    ]
)

# Find multi-hop paths (the hero feature!)
paths = db.paths.find(
    from_entity="e:useState",
    to_entity="e:redux",
    max_hops=4
)

for path in paths:
    print(f"Path cost: {path.cost}, Hops: {len(path.hyperedges)}")
```

## Async Support

For async/await patterns, use `AsyncHyperX`:

```python
from hyperx import AsyncHyperX

async def main():
    async with AsyncHyperX(api_key="hx_sk_live_abc123...") as db:
        entity = await db.entities.create(name="React", entity_type="concept")
        paths = await db.paths.find(from_entity="e:...", to_entity="e:...")
```

## API Reference

### Client Initialization

```python
from hyperx import HyperX, AsyncHyperX

# Sync client
db = HyperX(
    api_key="hx_sk_live_abc123...",           # Required: your API key
    base_url="https://api.hyperxdb.dev",  # Optional: defaults to this
    timeout=30.0,                  # Optional: request timeout in seconds
)

# Async client (same parameters)
db = AsyncHyperX(api_key="hx_sk_live_abc123...")

# Both support context managers
with HyperX(api_key="hx_sk_live_abc123...") as db:
    ...

async with AsyncHyperX(api_key="hx_sk_live_abc123...") as db:
    ...
```

### Entities

Entities are nodes in the hypergraph - the "things" in your knowledge base.

```python
# Create an entity
entity = db.entities.create(
    name="React Hooks",           # Required: human-readable name
    entity_type="concept",        # Required: type classification
    attributes={"version": "18"}, # Optional: key-value attributes
    embedding=[0.1, 0.2, ...],    # Optional: vector embedding
)

# Get an entity by ID
entity = db.entities.get("e:uuid...")

# Update an entity
entity = db.entities.update(
    "e:uuid...",
    name="New Name",
    attributes={"updated": True}
)

# List entities with pagination
entities = db.entities.list(limit=100, offset=0)

# Delete an entity
db.entities.delete("e:uuid...")
```

### Hyperedges

Hyperedges are n-ary relationships connecting multiple entities with semantic roles.

```python
from hyperx import MemberInput

# Create a hyperedge with dict syntax
edge = db.hyperedges.create(
    description="React provides Hooks for state management",
    members=[
        {"entity_id": "e:react", "role": "subject"},
        {"entity_id": "e:hooks", "role": "object"},
        {"entity_id": "e:state", "role": "context"},
    ],
    attributes={"source": "documentation"},
)

# Or use the MemberInput helper
edge = db.hyperedges.create(
    description="React provides Hooks",
    members=[
        MemberInput("e:react", "subject"),
        MemberInput("e:hooks", "object"),
    ]
)

# Get a hyperedge
edge = db.hyperedges.get("h:uuid...")

# List hyperedges
edges = db.hyperedges.list(limit=100, offset=0)

# Update a hyperedge
edge = db.hyperedges.update(
    "h:uuid...",
    description="Updated description",
)

# Delete a hyperedge
db.hyperedges.delete("h:uuid...")
```

### Paths (Hero Feature)

The paths API enables **multi-hop reasoning** - finding how concepts connect through chains of relationships. This is what sets HyperX apart from vector databases.

```python
# Find paths between two entities
paths = db.paths.find(
    from_entity="e:useState",     # Starting entity
    to_entity="e:redux",          # Target entity
    max_hops=4,                   # Maximum hyperedge hops (default: 4)
    intersection_size=1,          # Min bridge entities between edges (default: 1)
    k_paths=3,                    # Number of paths to return (default: 3)
)

# Each path contains:
for path in paths:
    print(f"Hyperedges: {path.hyperedges}")  # List of hyperedge IDs
    print(f"Bridges: {path.bridges}")         # Bridge entities between edges
    print(f"Cost: {path.cost}")               # Path cost (lower = better)
```

**Why this matters:** Vector search finds "React is similar to Vue". Path finding discovers "useState connects to Redux through React's state management pattern, which inspired Redux's design." That's the difference between similarity and understanding.

### Temporal Queries

HyperX supports bi-temporal queries - find what was true at any point in time.

```python
from datetime import datetime

# Create with temporal bounds
edge = db.hyperedges.create(
    description="React 18 introduces concurrent features",
    members=[...],
    valid_from=datetime(2022, 3, 29),  # React 18 release date
)

# Query at a specific point in time
edges = db.hyperedges.list(as_of=datetime(2021, 1, 1))

# Include deprecated knowledge
edges = db.hyperedges.list(include_deprecated=True)

# Get full history
edges = db.hyperedges.list(include_history=True)
```

### Lifecycle Management

Track knowledge evolution with lifecycle operations.

```python
# Deprecate outdated knowledge
db.hyperedges.deprecate("h:uuid", reason="Superseded by new info")

# Create new version
new_edge = db.hyperedges.supersede(
    "h:uuid",
    description="Updated relationship",
    members=[...]
)

# Get version history
history = db.hyperedges.history("h:uuid")
for version in history:
    print(f"v{version.version}: {version.description}")
```

### Search

HyperX supports hybrid search combining vector similarity and text matching.

```python
# Hybrid search (recommended)
results = db.search("react state management", limit=10)

# Access results
for entity in results.entities:
    print(entity.name)
for edge in results.hyperedges:
    print(edge.description)

# Vector-only search
results = db.search.vector(embedding=[0.1, 0.2, ...], limit=10)

# Text-only search (BM25)
results = db.search.text("react hooks tutorial", limit=10)
```

## Error Handling

The SDK provides typed exceptions for different error cases:

```python
from hyperx import (
    HyperXError,          # Base exception
    AuthenticationError,  # Invalid or missing API key
    NotFoundError,        # Resource not found
    ValidationError,      # Request validation failed
    RateLimitError,       # Rate limit exceeded
    ServerError,          # Server error (5xx)
)

try:
    entity = db.entities.get("e:nonexistent")
except NotFoundError:
    print("Entity not found")
except AuthenticationError:
    print("Invalid API key")
except HyperXError as e:
    print(f"HyperX error: {e.message}")
```

## Models

The SDK uses Pydantic models for type safety:

```python
from hyperx import Entity, Hyperedge, HyperedgeMember, PathResult, SearchResult

# Entity fields
entity.id           # str: "e:uuid..."
entity.name         # str
entity.entity_type  # str
entity.attributes   # dict[str, Any]
entity.confidence   # float
entity.created_at   # datetime
entity.updated_at   # datetime

# Hyperedge fields
edge.id             # str: "h:uuid..."
edge.description    # str
edge.members        # list[HyperedgeMember]
edge.attributes     # dict[str, Any]
edge.confidence     # float
edge.created_at     # datetime
edge.updated_at     # datetime

# HyperedgeMember fields
member.entity_id    # str
member.role         # str

# PathResult fields
path.hyperedges     # list[str]: ordered hyperedge IDs
path.bridges        # list[list[str]]: bridge entities
path.cost           # float: path cost

# SearchResult fields
results.entities    # list[Entity]
results.hyperedges  # list[Hyperedge]
```

### Batch Models

```python
from hyperx import BatchResult, BatchItemResult

# BatchResult fields (from batch operations)
result.success      # bool: all operations succeeded
result.total        # int: total operations
result.succeeded    # int: successful operations
result.failed       # int: failed operations
result.results      # list[BatchItemResult]

# BatchItemResult fields
item.success        # bool
item.item           # Entity | Hyperedge | None
item.error          # str | None
```

### Event Models

```python
from hyperx import Webhook, Trigger
from hyperx.events import Event

# Webhook fields
webhook.id          # str
webhook.url         # str
webhook.events      # list[str]
webhook.active      # bool
webhook.created_at  # datetime

# Trigger fields
trigger.id          # str
trigger.name        # str
trigger.condition   # str
trigger.event_types # list[str]
trigger.action      # "webhook" | "notification"
trigger.webhook_id  # str | None
trigger.active      # bool

# Event fields (from streaming)
event.type          # str: e.g., "entity.created"
event.data          # dict[str, Any]
event.timestamp     # datetime
event.metadata      # dict[str, Any]
```

## Examples

### Building a Knowledge Graph

```python
from hyperx import HyperX

db = HyperX(api_key="hx_sk_live_abc123...")

# Create entities for a tech knowledge graph
python = db.entities.create(name="Python", entity_type="language")
django = db.entities.create(name="Django", entity_type="framework")
flask = db.entities.create(name="Flask", entity_type="framework")
web = db.entities.create(name="Web Development", entity_type="concept")

# Create relationships
db.hyperedges.create(
    description="Django is built with Python",
    members=[
        {"entity_id": django.id, "role": "subject"},
        {"entity_id": python.id, "role": "language"},
    ]
)

db.hyperedges.create(
    description="Flask is a Python microframework",
    members=[
        {"entity_id": flask.id, "role": "subject"},
        {"entity_id": python.id, "role": "language"},
    ]
)

db.hyperedges.create(
    description="Django enables web development",
    members=[
        {"entity_id": django.id, "role": "tool"},
        {"entity_id": web.id, "role": "domain"},
    ]
)
```

### Find Reasoning Paths

```python
# Find how concepts connect through relationships
paths = db.paths.find(
    from_entity="e:useState",
    to_entity="e:redux",
    max_hops=4,
    k_paths=3
)

for path in paths:
    print(f"Path cost: {path.cost}")
    print(f"  Hyperedges: {' -> '.join(path.hyperedges)}")
    print(f"  Bridges: {path.bridges}")
```

This is HyperX's key differentiator from vector databases - multi-hop reasoning paths that explain *how* concepts relate, not just that they're similar.

### Multi-Hop Reasoning for RAG

```python
# When your LLM asks "How does Flask relate to web development?"
paths = db.paths.find(
    from_entity=flask.id,
    to_entity=web.id,
    max_hops=3
)

# Build context from the path
context = []
for path in paths:
    for edge_id in path.hyperedges:
        edge = db.hyperedges.get(edge_id)
        context.append(edge.description)

# Result: "Flask is a Python microframework" -> "Django is built with Python"
#         -> "Django enables web development"
# Your LLM now understands the indirect connection!
```

### Async Batch Operations

```python
import asyncio
from hyperx import AsyncHyperX

async def create_entities(db: AsyncHyperX, names: list[str]):
    tasks = [
        db.entities.create(name=name, entity_type="concept")
        for name in names
    ]
    return await asyncio.gather(*tasks)

async def main():
    async with AsyncHyperX(api_key="hx_sk_live_abc123...") as db:
        entities = await create_entities(db, ["React", "Vue", "Angular"])
        print(f"Created {len(entities)} entities")

asyncio.run(main())
```

## Framework Integrations

HyperX integrates with popular AI/ML frameworks. Install optional dependencies:

```bash
pip install hyperx[langchain]      # LangChain integration
pip install hyperx[llamaindex]     # LlamaIndex integration
pip install hyperx[all]            # Both frameworks
```

### LangChain

Use HyperX as a LangChain retriever:

```python
from hyperx import HyperX
from hyperx.integrations.langchain import HyperXRetriever

db = HyperX(api_key="hx_sk_...")

# Simple search retriever
retriever = HyperXRetriever(client=db, strategy="search", k=10)

# Graph-enhanced retriever (expands via relationships)
retriever = HyperXRetriever(
    client=db,
    strategy="graph",
    k=10,
    max_hops=2,
)

# Use in a chain
docs = retriever.invoke("React state management")
```

#### Full Retrieval Pipeline

For advanced use cases with hybrid search and reranking:

```python
from hyperx.integrations.langchain import HyperXRetrievalPipeline

pipeline = HyperXRetrievalPipeline(
    client=db,
    vector_weight=0.7,      # 70% semantic similarity
    text_weight=0.3,        # 30% keyword matching
    expand_graph=True,      # Include related concepts
    reranker=my_rerank_fn,  # Optional: (query, docs) -> ranked docs
    k=10,
)
docs = pipeline.invoke("distributed caching strategies")
```

### LlamaIndex

Use HyperX as a LlamaIndex knowledge graph:

```python
from hyperx import HyperX
from hyperx.integrations.llamaindex import HyperXKnowledgeGraph

db = HyperX(api_key="hx_sk_...")

# Create knowledge graph
kg = HyperXKnowledgeGraph(client=db)

# Use as retriever
retriever = kg.as_retriever(similarity_top_k=10)
nodes = retriever.retrieve("React state management")
```

## Agentic RAG (v0.6.0+)

HyperX provides a comprehensive toolkit for building AI agents that can query, explore, and modify knowledge graphs with **built-in self-correction capabilities**.

### Quick Start

```python
from hyperx import HyperX
from hyperx.agents import create_tools

db = HyperX(api_key="hx_sk_...")
tools = create_tools(db, level="explore")

# Get OpenAI function schemas for tool-using LLMs
schemas = tools.schemas

# Execute tool by name (from LLM function call response)
result = tools.execute("hyperx_search", query="React hooks")

if result.success:
    print(result.data)
    # Check quality signals for self-correction
    if result.quality.should_retrieve_more:
        print("Agent hint: Consider retrieving more results")
```

### Access Levels

Tools are organized into three access levels:

| Level | Tools | Use Case |
|-------|-------|----------|
| `"read"` (default) | SearchTool, PathsTool, LookupTool | Read-only retrieval |
| `"explore"` | read + ExplorerTool, ExplainTool, RelationshipsTool | Exploration & explanation |
| `"full"` | explore + EntityCrudTool, HyperedgeCrudTool | Full CRUD operations |

### Quality Signals for Self-Correction

Every tool returns quality signals that enable agent self-correction:

```python
result = tools.execute("hyperx_search", query="vague query")

# Quality signals tell the agent when/how to improve
quality = result.quality
quality.confidence           # 0.0-1.0 overall confidence
quality.coverage             # How well results cover the query
quality.should_retrieve_more # Explicit hint to get more results
quality.suggested_refinements  # ["Try: more specific term"]
quality.alternative_queries    # ["React useState", "hooks API"]
quality.missing_context_hints  # ["Consider also fetching X"]
```

### Available Tools

#### Read-Level Tools

```python
from hyperx.agents import SearchTool, PathsTool, LookupTool

# Configurable hybrid search
search = SearchTool(
    db,
    mode="hybrid",        # "hybrid", "vector", or "text"
    vector_weight=0.7,    # Balance semantic vs keyword
    reranker=my_reranker, # Optional reranking function
    default_limit=10,
)
result = search.run(query="React hooks", limit=20)

# Multi-hop reasoning paths
paths = PathsTool(db, default_max_hops=4)
result = paths.run(from_entity="e:useState", to_entity="e:redux")

# Direct lookup by ID
lookup = LookupTool(db)
result = lookup.run(id="e:react")  # or "h:hyperedge-id"
```

#### Explore-Level Tools

```python
from hyperx.agents import ExplorerTool, ExplainTool, RelationshipsTool

# Explore neighbors within N hops
explorer = ExplorerTool(db, default_max_hops=2)
result = explorer.run(entity_id="e:react", entity_types=["concept", "framework"])

# Get human-readable explanations
explain = ExplainTool(db)
result = explain.run(ids=["h:edge1", "h:edge2"])  # Explains paths/relationships

# List all relationships for an entity
relationships = RelationshipsTool(db)
result = relationships.run(entity_id="e:react", role="subject")
```

#### Full-Level Tools

```python
from hyperx.agents import EntityCrudTool, HyperedgeCrudTool

# Entity CRUD operations
entity_tool = EntityCrudTool(db)
result = entity_tool.run(action="create", name="React 19", entity_type="framework")
result = entity_tool.run(action="update", entity_id="e:...", name="Updated Name")
result = entity_tool.run(action="delete", entity_id="e:...")

# Hyperedge CRUD operations
edge_tool = HyperedgeCrudTool(db)
result = edge_tool.run(
    action="create",
    description="React 19 introduces new features",
    participants=[
        {"entity_id": "e:react-19", "role": "subject"},
        {"entity_id": "e:features", "role": "object"},
    ]
)
result = edge_tool.run(action="deprecate", hyperedge_id="h:...", reason="Outdated")
```

### LangChain Agent Integration

For LangChain/LangGraph agents, use `HyperXToolkit`:

```python
from hyperx import HyperX
from hyperx.agents.langchain import HyperXToolkit, as_langchain_tools

db = HyperX(api_key="hx_sk_...")

# Quick setup with toolkit
toolkit = HyperXToolkit(client=db, level="explore")
tools = toolkit.get_tools()

# Use with LangGraph
from langgraph.prebuilt import create_react_agent
agent = create_react_agent(llm, tools)

# Or wrap custom-configured tools
from hyperx.agents import SearchTool, PathsTool
tools = as_langchain_tools([
    SearchTool(db, mode="hybrid", reranker=my_reranker),
    PathsTool(db, default_max_hops=6),
])
```

### LlamaIndex Agent Integration

For LlamaIndex agents, use `HyperXToolSpec`:

```python
from hyperx import HyperX
from hyperx.agents.llamaindex import HyperXToolSpec, as_llamaindex_tools

db = HyperX(api_key="hx_sk_...")

# Quick setup with tool spec
tool_spec = HyperXToolSpec(client=db, level="full")
tools = tool_spec.to_tool_list()

# Use with OpenAI agent
from llama_index.agent.openai import OpenAIAgent
agent = OpenAIAgent.from_tools(tools)

# Or wrap custom tools
tools = as_llamaindex_tools([
    SearchTool(db, mode="vector"),
    PathsTool(db),
])
```

### OpenAI/Anthropic Function Calling

For direct function calling without a framework:

```python
from hyperx import HyperX
from hyperx.agents import create_tools

db = HyperX(api_key="hx_sk_...")
tools = create_tools(db, level="read")

# Get OpenAI function schemas
schemas = tools.schemas

# Send to OpenAI/Anthropic with your messages
response = openai.chat.completions.create(
    model="gpt-4",
    messages=messages,
    tools=schemas,
)

# Execute the tool call
tool_call = response.choices[0].message.tool_calls[0]
result = tools.execute(tool_call.function.name, **json.loads(tool_call.function.arguments))
```

## Batch Operations

For bulk ingestion, use batch methods or the unified batch API.

### Resource Batch Methods

```python
from hyperx import HyperX

db = HyperX(api_key="hx_sk_...")

# Create many entities at once
entities = db.entities.create_many([
    {"name": "React", "entity_type": "framework"},
    {"name": "Vue", "entity_type": "framework"},
    {"name": "Angular", "entity_type": "framework"},
], atomic=True)  # All-or-nothing (default)

# Best-effort mode: create what succeeds
entities = db.entities.create_many([...], atomic=False)
for item in entities:
    if item.success:
        print(f"Created: {item.item.id}")
    else:
        print(f"Failed: {item.error}")

# Bulk delete
results = db.entities.delete_many(["e:id1", "e:id2", "e:id3"])

# Same methods available for hyperedges
edges = db.hyperedges.create_many([...])
db.hyperedges.delete_many(["h:id1", "h:id2"])
```

### Unified Batch API

For mixed operations, use the batch resource:

```python
from hyperx import HyperX, EntityCreate, EntityDelete, HyperedgeCreate

db = HyperX(api_key="hx_sk_...")

# Execute mixed operations in a single request
result = db.batch.execute([
    EntityCreate(name="React", entity_type="framework"),
    EntityCreate(name="Hooks", entity_type="concept"),
    HyperedgeCreate(
        description="React provides Hooks",
        members=[
            {"entity_id": "e:react", "role": "subject"},
            {"entity_id": "e:hooks", "role": "object"},
        ]
    ),
    EntityDelete(entity_id="e:old-entity"),
], atomic=True)

# Check results
print(f"Succeeded: {result.succeeded}/{result.total}")
for item in result.failed_items:
    print(f"Failed: {item.error}")
```

**Available operations:**
- `EntityCreate` - Create an entity
- `EntityDelete` - Delete an entity
- `HyperedgeCreate` - Create a hyperedge
- `HyperedgeDelete` - Delete a hyperedge

## Caching

HyperX supports client-side caching with pluggable backends and optional server-side cache hints.

### In-Memory Cache

```python
from hyperx import HyperX
from hyperx.cache import InMemoryCache

# Create client with in-memory cache
cache = InMemoryCache(max_size=1000, ttl=300)  # 1000 entries, 5 min TTL
db = HyperX(api_key="hx_sk_...", cache=cache)

# Paths are cached by default when cache is configured
paths = db.paths.find("e:react", "e:redux")  # Cached
paths = db.paths.find("e:react", "e:redux")  # From cache

# Per-method cache control
paths = db.paths.find("e:a", "e:b", cache=False)  # Skip cache

# Search with caching
results = db.search("react hooks", cache=True)
```

### Redis Cache

For production deployments:

```bash
pip install hyperx[redis]  # or pip install redis
```

```python
from hyperx import HyperX
from hyperx.cache import RedisCache

# Redis with custom prefix
cache = RedisCache(
    url="redis://localhost:6379",
    prefix="myapp:hyperx:",
    ttl=600  # 10 minutes
)
db = HyperX(api_key="hx_sk_...", cache=cache)

# Cache operations
cache.clear()  # Clear all HyperX cache entries
```

### Server-Side Cache Hints

Request server-side caching for expensive operations:

```python
# Enable server-side caching
db = HyperX(api_key="hx_sk_...", server_cache=True)

# Cache hints for path queries
paths = db.paths.find(
    "e:react", "e:redux",
    cache_hint="long"  # "short", "medium", or "long"
)
```

## Query Builder

For complex queries, use the fluent query builder:

```python
from hyperx import HyperX, Query

db = HyperX(api_key="hx_sk_...")

# Build complex queries with method chaining
results = db.query(
    Query()
    .text("state management")
    .where(role="subject", entity="e:react")
    .or_where(role="subject", entity="e:vue")
    .with_hops(max=2)
    .limit(20)
)

# Temporal queries
from datetime import datetime

results = db.query(
    Query()
    .text("concurrent rendering")
    .temporal(as_of=datetime(2022, 1, 1))
    .limit(10)
)
```

### Query Builder Methods

| Method | Description |
|--------|-------------|
| `.text(query)` | Add text search query |
| `.where(role, entity=, entity_type=)` | Add role filter (AND) |
| `.or_where(...)` | Add role filter (OR) |
| `.with_hops(max)` | Set max hops for graph traversal |
| `.temporal(as_of)` | Query at specific time |
| `.limit(n)` | Limit results |

### Simple Role Filtering

For simple cases, use the `role_filter` parameter directly:

```python
# Filter by role
results = db.search(
    "state management",
    role_filter={"subject": "e:react"}
)

# Multiple roles
results = db.search(
    "hooks tutorial",
    role_filter={
        "subject": "e:react",
        "context": "e:state-management"
    }
)
```

## Webhooks & Events

HyperX provides real-time event notifications through webhooks and streaming.

### Webhook Management

```python
from hyperx import HyperX

db = HyperX(api_key="hx_sk_...")

# Create a webhook
webhook = db.webhooks.create(
    url="https://myapp.com/webhooks/hyperx",
    events=["entity.created", "hyperedge.created"],
    secret="whsec_my_secret_key"  # For HMAC signature verification
)
print(f"Webhook ID: {webhook.id}")

# List all webhooks
webhooks = db.webhooks.list()

# Test a webhook (sends a test event)
delivery = db.webhooks.test(webhook.id)
print(f"Delivery status: {delivery.status_code}")

# Delete a webhook
db.webhooks.delete(webhook.id)
```

**Available events:**
- `entity.created`, `entity.updated`, `entity.deleted`
- `hyperedge.created`, `hyperedge.updated`, `hyperedge.deleted`
- `path.discovered` - New paths found
- `search.threshold_match` - Search exceeds threshold

### Event Decorator

Register local handlers for events:

```python
from hyperx import HyperX

db = HyperX(api_key="hx_sk_...")

# Register handler with decorator
@db.on("entity.created")
def handle_entity(event):
    print(f"New entity: {event.data['name']}")

@db.on("hyperedge.*")  # Wildcard patterns
def handle_hyperedge(event):
    print(f"Hyperedge event: {event.type}")

# Filter by additional criteria
@db.on("entity.created", filter={"entity_type": "concept"})
def handle_concept(event):
    print(f"New concept: {event.data['name']}")

# Emit events locally (for testing)
db.emit("entity.created", {"id": "e:test", "name": "Test"})
```

### Event Streaming

For real-time event processing:

```python
from hyperx import HyperX
from datetime import datetime, timedelta

db = HyperX(api_key="hx_sk_...")

# Stream all events (sync)
for event in db.events.stream():
    print(f"{event.type}: {event.data}")

# Filter event types
for event in db.events.stream(["entity.*", "hyperedge.created"]):
    print(f"{event.type}: {event.data}")

# Resume from timestamp
since = datetime.now() - timedelta(hours=1)
for event in db.events.stream(since=since):
    print(f"{event.type}: {event.data}")

# Get event history
events = db.events.history(
    event_types=["entity.created"],
    since=datetime(2024, 1, 1),
    limit=100
)
```

### Async Streaming

```python
from hyperx import AsyncHyperX

async with AsyncHyperX(api_key="hx_sk_...") as db:
    async for event in db.events.stream(["entity.*"]):
        print(f"{event.type}: {event.data}")
```

## Custom Triggers

Create custom triggers that fire webhooks based on conditions:

```python
from hyperx import HyperX

db = HyperX(api_key="hx_sk_...")

# Create a trigger
trigger = db.triggers.create(
    name="high_confidence_path",
    condition="path.cost < 0.5 AND path.hops <= 2",
    event_types=["path.discovered"],
    action="webhook",
    webhook_id="wh:your-webhook-id"
)

# Create notification trigger
trigger = db.triggers.create(
    name="important_entity",
    condition="entity.entity_type == 'critical'",
    event_types=["entity.created"],
    action="notification"
)

# List triggers
triggers = db.triggers.list()

# Test a trigger with sample data
result = db.triggers.test(
    trigger.id,
    event_data={"path": {"cost": 0.3, "hops": 1}}
)
print(f"Matched: {result['matched']}")

# Update trigger
trigger = db.triggers.update(
    trigger.id,
    condition="path.cost < 0.3"
)

# Delete trigger
db.triggers.delete(trigger.id)
```

**Condition syntax:**
- Comparisons: `==`, `!=`, `<`, `>`, `<=`, `>=`
- Logical: `AND`, `OR`, `NOT`
- Paths: `entity.name`, `path.cost`, `hyperedge.members.length`

## Development

```bash
# Install dev dependencies
pip install hyperx[dev]

# Run tests
pytest

# Type checking
mypy src/hyperx

# Linting
ruff check src/hyperx
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- **Website:** [hyperxdb.dev](https://hyperxdb.dev)
- **Documentation:** [hyperxdb.dev/docs](https://hyperxdb.dev/docs)
- **GitHub:** [github.com/hyperxdb/hyperx-python](https://github.com/hyperxdb/hyperx-python)
- **Issues:** [github.com/hyperxdb/hyperx-python/issues](https://github.com/hyperxdb/hyperx-python/issues)
