# HyperX Python SDK Examples

This directory contains comprehensive examples for using the HyperX Python SDK.

## Prerequisites

```bash
# Install the SDK
pip install hyperxdb

# For framework integrations
pip install hyperxdb[langchain]   # LangChain support
pip install hyperxdb[llamaindex]  # LlamaIndex support
pip install hyperxdb[all]         # All optional dependencies
```

## Examples

| # | Example | Description |
|---|---------|-------------|
| 01 | [Basic Usage](01_basic_usage.py) | Entities, hyperedges, and CRUD operations |
| 02 | [Search](02_search.py) | Hybrid, vector, and BM25 search |
| 03 | [Path Finding](03_path_finding.py) | Multi-hop reasoning and graph traversal |
| 04 | [Temporal Queries](04_temporal_queries.py) | Bi-temporal support and versioning |
| 05 | [Agentic RAG](05_agentic_rag.py) | Agent tools with quality signals |
| 06 | [LangChain](06_langchain_integration.py) | LangChain toolkit and agents |
| 07 | [LlamaIndex](07_llamaindex_integration.py) | LlamaIndex tool spec and agents |
| 08 | [OpenAI Functions](08_openai_functions.py) | OpenAI function calling |
| 09 | [Async Client](09_async_client.py) | Async operations and concurrency |
| 10 | [Batch Operations](10_batch_operations.py) | Bulk imports and exports |

## Quick Start

```python
from hyperx import HyperX

# Connect to HyperX
client = HyperX("https://api.hyperxdb.dev", api_key="your-api-key")

# Create an entity
entity = client.entities.create(
    label="My First Entity",
    entity_type="Concept",
    description="A test entity"
)

# Search
results = client.search.hybrid(query="machine learning", limit=10)
```

## Running Examples

Each example is self-contained. Replace `your-api-key` with your actual API key:

```bash
# Run an example
python 01_basic_usage.py

# Or interactively
python -i 05_agentic_rag.py
```

## Agentic RAG Quick Reference

```python
from hyperx.agents import create_tools

# Access levels: "read", "explore", "full"
tools = create_tools(client, access_level="explore")

# Execute a tool
result = tools.execute("search", query="transformers", limit=10)

# Check quality signals
if result.quality.should_retrieve_more:
    print(f"Suggestions: {result.quality.suggested_refinements}")
```

## Framework Integration Quick Reference

### LangChain

```python
from hyperx.agents.langchain import HyperXToolkit

toolkit = HyperXToolkit(client, access_level="explore")
tools = toolkit.get_tools()
```

### LlamaIndex

```python
from hyperx.agents.llamaindex import HyperXToolSpec

tool_spec = HyperXToolSpec(client, access_level="explore")
tools = tool_spec.to_tool_list()
```

### OpenAI Functions

```python
functions = tools.get_openai_functions()
result = tools.call_function("search", query="test")
```

## Support

- Documentation: [hyperxdb.dev/docs](https://hyperxdb.dev/docs)
- Issues: [GitHub Issues](https://github.com/memoist-ai/hypergraph-engine/issues)
