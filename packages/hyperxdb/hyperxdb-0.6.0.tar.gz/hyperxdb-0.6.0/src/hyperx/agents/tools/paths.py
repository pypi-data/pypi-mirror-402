"""PathsTool for agentic RAG workflows.

This module provides the PathsTool class which wraps HyperX multi-hop
path finding capabilities in a tool interface compatible with LLM function calling.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from hyperx.agents.base import QualitySignals, ToolResult

if TYPE_CHECKING:
    from hyperx import HyperX


class PathsTool:
    """Path finding tool for multi-hop reasoning across the HyperX knowledge graph.

    PathsTool enables agents to discover reasoning paths between entities,
    which is essential for complex question answering and knowledge synthesis.
    This is HyperX's differentiating feature - intersection-constrained
    pathfinding that vector databases cannot perform.

    The tool finds paths through hyperedges that share bridge entities,
    enabling multi-hop reasoning like:
    - "How does React's useState relate to Redux?"
    - "What connects GraphQL to REST APIs?"

    Quality signals help agents decide whether to expand their search
    or try different entity pairs based on path costs and availability.

    Attributes:
        name: Unique identifier for the tool ("hyperx_find_paths").
        description: Human-readable description for LLM function calling.

    Example:
        >>> from hyperx import HyperX
        >>> from hyperx.agents.tools import PathsTool
        >>>
        >>> client = HyperX(api_key="hx_sk_...")
        >>> paths_tool = PathsTool(client, default_max_hops=4, default_k_paths=5)
        >>>
        >>> result = paths_tool.run(
        ...     from_entity="e:useState",
        ...     to_entity="e:redux",
        ... )
        >>> if result.success:
        ...     for path in result.data["paths"]:
        ...         print(f"Cost: {path['cost']}, Via: {path['hyperedges']}")
        ...
        ...     if result.quality.should_retrieve_more:
        ...         # Agent can decide to increase max_hops
        ...         print("Consider increasing max_hops")
    """

    def __init__(
        self,
        client: HyperX,
        *,
        default_max_hops: int = 4,
        default_k_paths: int = 3,
    ) -> None:
        """Initialize the PathsTool.

        Args:
            client: HyperX client instance for API calls.
            default_max_hops: Default maximum number of hyperedge hops to traverse.
                Higher values find more distant connections but take longer.
                Defaults to 4.
            default_k_paths: Default number of paths to return.
                Returns the k lowest-cost paths. Defaults to 3.
        """
        self._client = client
        self._default_max_hops = default_max_hops
        self._default_k_paths = default_k_paths

    @property
    def name(self) -> str:
        """Unique identifier for the tool."""
        return "hyperx_find_paths"

    @property
    def description(self) -> str:
        """Human-readable description of what the tool does."""
        return (
            "Find multi-hop reasoning paths between two entities in the HyperX "
            "knowledge graph. Returns paths that traverse through hyperedges "
            "sharing bridge entities, enabling complex relational reasoning. "
            f"Default: up to {self._default_max_hops} hops, top {self._default_k_paths} paths."
        )

    def run(
        self,
        from_entity: str,
        to_entity: str,
        *,
        max_hops: int | None = None,
        k_paths: int | None = None,
    ) -> ToolResult:
        """Execute the path finding tool synchronously.

        Finds multi-hop reasoning paths between two entities in the HyperX
        knowledge graph and returns results with quality signals.

        Args:
            from_entity: Starting entity ID (e.g., "e:useState").
            to_entity: Target entity ID (e.g., "e:redux").
            max_hops: Maximum number of hyperedge hops. Uses default_max_hops if not specified.
            k_paths: Number of paths to return. Uses default_k_paths if not specified.

        Returns:
            ToolResult containing:
                - success: Whether the path finding completed successfully
                - data: Dictionary with "paths" list, each containing hyperedges, bridges, cost
                - quality: QualitySignals for agentic self-correction
                - explanation: Human-readable summary of results
        """
        try:
            effective_max_hops = max_hops if max_hops is not None else self._default_max_hops
            effective_k_paths = k_paths if k_paths is not None else self._default_k_paths

            # Execute path finding
            path_results = self._client.paths.find(
                from_entity=from_entity,
                to_entity=to_entity,
                max_hops=effective_max_hops,
                k_paths=effective_k_paths,
            )

            # Convert results to dictionaries
            paths = [p.model_dump() for p in path_results]

            # Compute quality signals based on path costs
            quality = self._compute_quality_signals(paths, from_entity, to_entity)

            # Build explanation
            explanation = self._build_explanation(
                from_entity=from_entity,
                to_entity=to_entity,
                path_count=len(paths),
                quality=quality,
            )

            return ToolResult(
                success=True,
                data={"paths": paths},
                quality=quality,
                explanation=explanation,
            )

        except Exception as e:
            # Return failed result instead of raising
            return ToolResult(
                success=False,
                data=None,
                quality=QualitySignals(
                    confidence=0.0,
                    relevance_scores=[],
                    coverage=0.0,
                    diversity=0.0,
                    should_retrieve_more=True,
                    suggested_refinements=["Try increasing max_hops", "Verify entity IDs exist"],
                    alternative_queries=[],
                    missing_context_hints=[f"Path finding failed: {e!s}"],
                ),
                explanation=f"Path finding failed: {e!s}",
            )

    async def arun(
        self,
        from_entity: str,
        to_entity: str,
        *,
        max_hops: int | None = None,
        k_paths: int | None = None,
    ) -> ToolResult:
        """Execute the path finding tool asynchronously.

        Finds multi-hop reasoning paths between two entities in the HyperX
        knowledge graph and returns results with quality signals.

        Note: This method currently wraps the synchronous implementation.
        For true async support, use AsyncHyperX client.

        Args:
            from_entity: Starting entity ID (e.g., "e:useState").
            to_entity: Target entity ID (e.g., "e:redux").
            max_hops: Maximum number of hyperedge hops. Uses default_max_hops if not specified.
            k_paths: Number of paths to return. Uses default_k_paths if not specified.

        Returns:
            ToolResult containing path results and quality signals.
        """
        # Currently wraps sync implementation
        # For true async, would need AsyncHyperX client
        return self.run(
            from_entity=from_entity,
            to_entity=to_entity,
            max_hops=max_hops,
            k_paths=k_paths,
        )

    def to_openai_schema(self) -> dict[str, Any]:
        """Export tool definition as OpenAI function schema.

        Returns a dictionary conforming to OpenAI's function calling schema,
        suitable for use with the OpenAI API's `tools` parameter.

        Returns:
            Dictionary with OpenAI function calling schema.

        Example:
            >>> paths_tool = PathsTool(client)
            >>> schema = paths_tool.to_openai_schema()
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
                        "from_entity": {
                            "type": "string",
                            "description": (
                                "The starting entity ID for path finding. "
                                'Format: "e:entity_name" (e.g., "e:useState", "e:react").'
                            ),
                        },
                        "to_entity": {
                            "type": "string",
                            "description": (
                                "The target entity ID for path finding. "
                                'Format: "e:entity_name" (e.g., "e:redux", "e:graphql").'
                            ),
                        },
                        "max_hops": {
                            "type": "integer",
                            "description": (
                                f"Maximum number of hyperedge hops to traverse. "
                                f"Higher values find more distant connections. "
                                f"Defaults to {self._default_max_hops}."
                            ),
                            "minimum": 1,
                            "maximum": 10,
                        },
                        "k_paths": {
                            "type": "integer",
                            "description": (
                                f"Number of paths to return (lowest cost first). "
                                f"Defaults to {self._default_k_paths}."
                            ),
                            "minimum": 1,
                            "maximum": 20,
                        },
                    },
                    "required": ["from_entity", "to_entity"],
                },
            },
        }

    def _compute_quality_signals(
        self,
        paths: list[dict[str, Any]],
        from_entity: str,
        to_entity: str,
    ) -> QualitySignals:
        """Compute quality signals based on path costs.

        Quality signals are derived from path costs:
        - Lower cost paths indicate stronger/more direct connections
        - confidence = 1.0 - average_cost (higher for lower costs)
        - relevance_scores = [1.0 - cost for each path]
        - should_retrieve_more = True if no paths or low confidence

        Args:
            paths: List of path dictionaries with cost field.
            from_entity: Starting entity ID.
            to_entity: Target entity ID.

        Returns:
            QualitySignals instance with computed values.
        """
        if not paths:
            return QualitySignals(
                confidence=0.0,
                relevance_scores=[],
                coverage=0.0,
                diversity=0.0,
                should_retrieve_more=True,
                suggested_refinements=["Try increasing max_hops"],
                alternative_queries=[],
                missing_context_hints=[
                    f"No paths found between {from_entity} and {to_entity}"
                ],
            )

        # Compute relevance scores from path costs (lower cost = higher relevance)
        # Costs are typically 0-1, so relevance = 1 - cost
        relevance_scores = [max(0.0, min(1.0, 1.0 - p.get("cost", 0.5))) for p in paths]

        # Confidence is average relevance (which is 1 - average_cost)
        average_cost = sum(p.get("cost", 0.5) for p in paths) / len(paths)
        confidence = max(0.0, min(1.0, 1.0 - average_cost))

        # Coverage based on number of paths found (more paths = better coverage)
        # Assume 3+ paths is good coverage
        coverage = min(1.0, len(paths) / 3.0)

        # Diversity based on unique bridge entities across paths
        all_bridges = set()
        for p in paths:
            for bridge_set in p.get("bridges", []):
                all_bridges.update(bridge_set)
        # More unique bridges = more diversity
        diversity = min(1.0, len(all_bridges) / 5.0) if all_bridges else 0.0

        # Should retrieve more if confidence is low or we have few paths
        should_retrieve_more = confidence < 0.5 or len(paths) < 2

        # Build refinement suggestions
        suggested_refinements = []
        if confidence < 0.5:
            suggested_refinements.append("Try increasing max_hops for more distant connections")
        if len(paths) < 2:
            suggested_refinements.append("Try increasing k_paths for more alternatives")

        return QualitySignals(
            confidence=confidence,
            relevance_scores=relevance_scores,
            coverage=coverage,
            diversity=diversity,
            should_retrieve_more=should_retrieve_more,
            suggested_refinements=suggested_refinements,
            alternative_queries=[],
            missing_context_hints=[],
        )

    def _build_explanation(
        self,
        from_entity: str,
        to_entity: str,
        path_count: int,
        quality: QualitySignals,
    ) -> str:
        """Build a human-readable explanation of the path finding results.

        Args:
            from_entity: Starting entity ID.
            to_entity: Target entity ID.
            path_count: Number of paths found.
            quality: Quality signals from the analysis.

        Returns:
            Human-readable explanation string.
        """
        parts = []

        # Result summary
        if path_count == 0:
            parts.append(f"No paths found between {from_entity} and {to_entity}.")
        elif path_count == 1:
            parts.append(f"Found 1 path between {from_entity} and {to_entity}.")
        else:
            parts.append(f"Found {path_count} paths between {from_entity} and {to_entity}.")

        # Confidence assessment
        if quality.confidence >= 0.8:
            parts.append("High confidence - strong connections found.")
        elif quality.confidence >= 0.5:
            parts.append("Moderate confidence - reasonable paths found.")
        else:
            parts.append("Low confidence - paths may be indirect or weak.")

        # Retrieval suggestion
        if quality.should_retrieve_more:
            parts.append("Consider increasing max_hops or trying related entities.")

        return " ".join(parts)
