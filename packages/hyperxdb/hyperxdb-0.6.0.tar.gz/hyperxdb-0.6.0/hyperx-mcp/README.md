# HyperX MCP Server

Connect Claude to your HyperX knowledge graph using the Model Context Protocol (MCP).

## Installation

```bash
pip install hyperx-mcp
```

Or install from source:

```bash
cd hyperx-mcp
pip install -e .
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HYPERX_API_KEY` | Yes | - | Your HyperX API key |
| `HYPERX_BASE_URL` | No | `https://api.hyperxdb.dev` | API base URL |
| `HYPERX_ACCESS_LEVEL` | No | `explore` | Tool access level: `read`, `explore`, or `full` |

### Claude Desktop Configuration

Add to your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "hyperx": {
      "command": "hyperx-mcp",
      "env": {
        "HYPERX_API_KEY": "your-api-key-here",
        "HYPERX_ACCESS_LEVEL": "explore"
      }
    }
  }
}
```

### Alternative: Using uvx (no install required)

```json
{
  "mcpServers": {
    "hyperx": {
      "command": "uvx",
      "args": ["hyperx-mcp"],
      "env": {
        "HYPERX_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## Available Tools

### Read Level (`read`)
Basic read-only access for RAG applications.

| Tool | Description |
|------|-------------|
| `hyperx_search` | Hybrid search (vector + text) for entities |
| `hyperx_lookup` | Get entity by ID |
| `hyperx_paths` | Find paths between entities |

### Explore Level (`explore`)
Extended read access for graph exploration.

| Tool | Description |
|------|-------------|
| `hyperx_explorer` | Explore entity neighborhood |
| `hyperx_explain` | Natural language entity explanation |
| `hyperx_relationships` | Get entity relationships |

### Full Level (`full`)
Complete access including mutations.

| Tool | Description |
|------|-------------|
| `hyperx_entity_crud` | Create, update, delete entities |
| `hyperx_hyperedge_crud` | Create, update, delete hyperedges |

## Quality Signals

All tool responses include quality signals to help Claude self-correct:

```json
{
  "success": true,
  "data": { ... },
  "quality": {
    "confidence": 0.85,
    "coverage": 0.72,
    "diversity": 0.68,
    "should_retrieve_more": false,
    "suggested_refinements": ["Try searching for 'transformer attention'"]
  }
}
```

- **confidence**: Overall result quality (0.0-1.0)
- **coverage**: How well results cover the query
- **diversity**: Entity type diversity in results
- **should_retrieve_more**: Hint to expand search
- **suggested_refinements**: Query improvement suggestions

## Example Usage

Once configured, you can ask Claude:

> "Search my knowledge graph for information about transformer architectures"

> "Find the connection between BERT and GPT in the knowledge graph"

> "Explore all entities related to machine learning within 2 hops"

> "Create a new concept entity for 'Retrieval Augmented Generation'"

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check .
```

## Troubleshooting

### "HYPERX_API_KEY environment variable is required"

Make sure you've set the API key in your Claude Desktop config or environment.

### Tools not appearing in Claude

1. Restart Claude Desktop after config changes
2. Check the config file path is correct for your OS
3. Verify the `hyperx-mcp` command is in your PATH

### Connection errors

1. Check your API key is valid
2. Verify network connectivity to `api.hyperxdb.dev`
3. Check if you need to set a custom `HYPERX_BASE_URL`

## License

MIT
