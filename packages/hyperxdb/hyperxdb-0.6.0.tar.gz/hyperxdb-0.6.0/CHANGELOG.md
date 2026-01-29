# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.1] - 2026-01-18

### Added

#### MCP Server (`hyperx-mcp`)
- New `hyperx-mcp` package for Claude Desktop and MCP-compatible clients
- Wraps all 8 agent tools for MCP protocol
- Environment-based configuration (`HYPERX_API_KEY`, `HYPERX_ACCESS_LEVEL`)
- Quality signals included in all tool responses
- Install: `pip install hyperx-mcp`

## [0.6.0] - 2026-01-17

### Added

#### Agentic RAG Support
- New `hyperx.agents` module for AI agent tool integration
- **8 Agent Tools** across 3 access levels:
  - **Read Level**: `SearchTool`, `PathsTool`, `LookupTool`
  - **Explore Level**: `ExplorerTool`, `ExplainTool`, `RelationshipsTool`
  - **Full Level**: `EntityCrudTool`, `HyperedgeCrudTool`
- **Quality Signals** for agent self-correction:
  - `confidence`: Result quality score (0.0-1.0)
  - `coverage`: Query coverage metric
  - `diversity`: Entity diversity score
  - `should_retrieve_more`: Boolean hint for agents
  - `suggested_refinements`: List of query improvement suggestions
- `ToolCollection` class with `create_tools()` factory and unified `execute()` method
- `ToolResult` dataclass with success, data, quality signals, and metadata

#### Framework Integrations
- **LangChain Integration**:
  - `HyperXToolkit` for LangChain agents
  - `as_langchain_tools()` method for tool conversion
  - Structured tool support with proper typing
- **LlamaIndex Integration**:
  - `HyperXToolSpec` for LlamaIndex agents
  - `as_llamaindex_tools()` method for tool conversion
- **OpenAI Function Calling**:
  - `get_openai_functions()` for function definitions
  - `call_function()` for function execution

### Changed
- Bumped version from 0.5.0 to 0.6.0

## [0.5.0] - 2026-01-17

### Added
- Redis caching support via optional `redis` dependency
- Cache configuration with TTL settings
- Automatic cache invalidation on mutations

## [0.4.0] - 2026-01-16

### Added
- Batch operations for entities and hyperedges
- Connection pooling configuration
- Request retry logic with exponential backoff

## [0.3.0] - 2026-01-16

### Added

#### Bi-Temporal Support
- `valid_from` and `valid_until` parameters on entity/hyperedge creation
- Temporal query parameters: `point_in_time`, `valid_at`, `include_historical`
- Entity lifecycle methods:
  - `deprecate()` - Mark entity as deprecated
  - `supersede()` - Replace with newer version
  - `retire()` - Permanently retire entity
  - `reactivate()` - Restore deprecated/retired entity
  - `history()` - Get full version history
- Hyperedge lifecycle methods (same as entities)
- `state` field on Entity/Hyperedge models (Active, Deprecated, Superseded, Retired)
- `valid_from`, `valid_until`, `superseded_by` fields on models

### Changed
- Entity and Hyperedge models now include temporal fields
- List methods accept temporal filtering parameters

## [0.2.0] - 2026-01-15

### Added

#### Path Finding (Multi-Hop Reasoning)
- `client.paths.find()` method for path finding between entities
- `PathResult` model with steps, hops, and metadata
- Support for path constraints (max_hops, min_intersection_size)
- K-shortest paths support

### Changed
- Updated documentation with path finding examples

## [0.1.0] - 2026-01-15

### Added
- Initial release
- `HyperX` sync client with context manager support
- `AsyncHyperX` async client with async context manager
- Entities API (create, get, update, delete, list)
- Hyperedges API (create, get, delete, list)
- Search API (hybrid, vector, text)
- Paths API for multi-hop reasoning (hero feature)
- Typed exception hierarchy (AuthenticationError, NotFoundError, etc.)
- Full type hints with py.typed marker
- Comprehensive test suite with 33 tests
