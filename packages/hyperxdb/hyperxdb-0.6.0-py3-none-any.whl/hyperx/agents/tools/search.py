"""SearchTool for agentic RAG workflows.

This module provides the SearchTool class which wraps HyperX search
capabilities in a tool interface compatible with LLM function calling.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Literal

from hyperx.agents.base import QualitySignals, ToolResult
from hyperx.agents.quality import QualityAnalyzer

if TYPE_CHECKING:
    from hyperx import HyperX


class SearchTool:
    """Search tool for HyperX knowledge graph queries.

    SearchTool provides a unified interface for searching the HyperX
    knowledge graph with configurable search modes, reranking, and
    quality signals for agentic self-correction.

    The tool supports three search modes:
        - "hybrid" (default): Combines vector similarity and text matching
        - "vector": Vector-only search using embedding similarity
        - "text": Text-only search using BM25 ranking

    Quality signals help agents decide whether to retrieve more data
    or refine their queries based on confidence, coverage, and diversity.

    Attributes:
        name: Unique identifier for the tool ("hyperx_search").
        description: Human-readable description for LLM function calling.

    Example:
        >>> from hyperx import HyperX
        >>> from hyperx.agents.tools import SearchTool
        >>>
        >>> client = HyperX(api_key="hx_sk_...")
        >>> search = SearchTool(
        ...     client,
        ...     mode="hybrid",
        ...     default_limit=10,
        ...     expand_graph=True,
        ...     max_hops=2,
        ... )
        >>>
        >>> result = search.run("react hooks tutorial")
        >>> if result.success:
        ...     for entity in result.data["entities"]:
        ...         print(entity["name"])
        ...
        ...     if result.quality.should_retrieve_more:
        ...         # Agent can decide to expand the search
        ...         print("Consider expanding search:", result.quality.alternative_queries)
    """

    def __init__(
        self,
        client: HyperX,
        *,
        mode: Literal["hybrid", "vector", "text"] = "hybrid",
        vector_weight: float = 0.7,
        reranker: Callable[[str, list[dict[str, Any]]], list[dict[str, Any]]] | None = None,
        default_limit: int = 10,
        expand_graph: bool = False,
        max_hops: int = 2,
    ) -> None:
        """Initialize the SearchTool.

        Args:
            client: HyperX client instance for API calls.
            mode: Search mode - "hybrid", "vector", or "text".
                Defaults to "hybrid".
            vector_weight: Weight for vector similarity in hybrid mode (0.0-1.0).
                Higher values favor semantic similarity. Defaults to 0.7.
            reranker: Optional callable to rerank search results.
                Takes (query, results) and returns reordered results.
            default_limit: Default number of results to return. Defaults to 10.
            expand_graph: Whether to expand results by following graph edges.
                Defaults to False.
            max_hops: Maximum number of hops when expand_graph is True.
                Defaults to 2.
        """
        self._client = client
        self._mode = mode
        self._vector_weight = vector_weight
        self._reranker = reranker
        self._default_limit = default_limit
        self._expand_graph = expand_graph
        self._max_hops = max_hops
        self._analyzer = QualityAnalyzer()

    @property
    def name(self) -> str:
        """Unique identifier for the tool."""
        return "hyperx_search"

    @property
    def description(self) -> str:
        """Human-readable description of what the tool does."""
        return (
            "Search the HyperX knowledge graph for entities and relationships. "
            "Returns relevant entities and hyperedges based on the query. "
            f"Uses {self._mode} search mode with up to {self._default_limit} results."
        )

    def run(
        self,
        query: str,
        *,
        limit: int | None = None,
        role_filter: dict[str, str] | None = None,
    ) -> ToolResult:
        """Execute the search tool synchronously.

        Performs a search against the HyperX knowledge graph using the
        configured search mode and returns results with quality signals.

        Args:
            query: Search query string.
            limit: Maximum number of results. Uses default_limit if not specified.
            role_filter: Optional filter to constrain hyperedges by role.
                Example: {"subject": "e:react"} to find hyperedges where
                React is the subject.

        Returns:
            ToolResult containing:
                - success: Whether the search completed successfully
                - data: Dictionary with "entities" and "hyperedges" lists
                - quality: QualitySignals for agentic self-correction
                - explanation: Human-readable summary of results
        """
        try:
            effective_limit = limit if limit is not None else self._default_limit

            # Execute search based on mode
            if self._mode == "text":
                search_result = self._client.search.text(
                    query,
                    limit=effective_limit,
                    role_filter=role_filter,
                )
            elif self._mode == "vector":
                # For vector mode, we would need an embedding
                # Fall back to hybrid if no embedding provided
                search_result = self._client.search(
                    query,
                    limit=effective_limit,
                    role_filter=role_filter,
                )
            else:  # hybrid (default)
                search_result = self._client.search(
                    query,
                    limit=effective_limit,
                    role_filter=role_filter,
                )

            # Convert results to dictionaries
            entities = [e.model_dump() for e in search_result.entities]
            hyperedges = [h.model_dump() for h in search_result.hyperedges]

            # Apply reranker if provided
            if self._reranker is not None:
                entities = self._reranker(query, entities)

            # Compute relevance scores (use confidence from entities)
            scores = [e.get("confidence", 0.5) for e in entities]

            # Generate quality signals using the analyzer
            quality = self._analyzer.analyze(
                query=query,
                results=entities,
                scores=scores,
            )

            # Build explanation
            entity_count = len(entities)
            hyperedge_count = len(hyperedges)
            explanation = self._build_explanation(
                query=query,
                entity_count=entity_count,
                hyperedge_count=hyperedge_count,
                quality=quality,
            )

            return ToolResult(
                success=True,
                data={
                    "entities": entities,
                    "hyperedges": hyperedges,
                },
                quality=quality,
                explanation=explanation,
            )

        except Exception as e:
            # Return failed result instead of raising
            return ToolResult(
                success=False,
                data=None,
                quality=QualitySignals.default(),
                explanation=f"Search failed: {e!s}",
            )

    async def arun(
        self,
        query: str,
        *,
        limit: int | None = None,
        role_filter: dict[str, str] | None = None,
    ) -> ToolResult:
        """Execute the search tool asynchronously.

        Performs a search against the HyperX knowledge graph using the
        configured search mode and returns results with quality signals.

        Note: This method currently wraps the synchronous implementation.
        For true async support, use AsyncHyperX client.

        Args:
            query: Search query string.
            limit: Maximum number of results. Uses default_limit if not specified.
            role_filter: Optional filter to constrain hyperedges by role.

        Returns:
            ToolResult containing search results and quality signals.
        """
        # Currently wraps sync implementation
        # For true async, would need AsyncHyperX client
        return self.run(query, limit=limit, role_filter=role_filter)

    def to_openai_schema(self) -> dict[str, Any]:
        """Export tool definition as OpenAI function schema.

        Returns a dictionary conforming to OpenAI's function calling schema,
        suitable for use with the OpenAI API's `tools` parameter.

        Returns:
            Dictionary with OpenAI function calling schema.

        Example:
            >>> search = SearchTool(client)
            >>> schema = search.to_openai_schema()
            >>> # Use in OpenAI API call
            >>> response = openai.chat.completions.create(
            ...     model="gpt-4",
            ...     messages=[...],
            ...     tools=[schema],
            ... )
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": (
                                "The search query to find relevant entities and "
                                "relationships in the knowledge graph."
                            ),
                        },
                        "limit": {
                            "type": "integer",
                            "description": (
                                f"Maximum number of results to return. "
                                f"Defaults to {self._default_limit}."
                            ),
                            "minimum": 1,
                            "maximum": 100,
                        },
                        "role_filter": {
                            "type": "object",
                            "description": (
                                "Filter hyperedges by role conditions. "
                                'Example: {"subject": "e:react"} finds hyperedges '
                                "where React is the subject."
                            ),
                            "additionalProperties": {
                                "type": "string",
                            },
                        },
                    },
                    "required": ["query"],
                },
            },
        }

    def _build_explanation(
        self,
        query: str,
        entity_count: int,
        hyperedge_count: int,
        quality: QualitySignals,
    ) -> str:
        """Build a human-readable explanation of the search results.

        Args:
            query: The original search query.
            entity_count: Number of entities found.
            hyperedge_count: Number of hyperedges found.
            quality: Quality signals from the analysis.

        Returns:
            Human-readable explanation string.
        """
        parts = []

        # Result summary
        if entity_count == 0 and hyperedge_count == 0:
            parts.append(f"No results found for '{query}'.")
        else:
            parts.append(
                f"Found {entity_count} entities and {hyperedge_count} "
                f"hyperedges for '{query}'."
            )

        # Confidence assessment
        if quality.confidence >= 0.8:
            parts.append("High confidence results.")
        elif quality.confidence >= 0.5:
            parts.append("Moderate confidence results.")
        else:
            parts.append("Low confidence results.")

        # Retrieval suggestion
        if quality.should_retrieve_more:
            parts.append("Consider retrieving more data or refining the query.")

        return " ".join(parts)
