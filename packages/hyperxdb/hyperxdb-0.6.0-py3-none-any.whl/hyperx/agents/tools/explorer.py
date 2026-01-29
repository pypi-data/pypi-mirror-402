"""Explorer tools for agentic RAG workflows.

This module provides the ExplorerTool, ExplainTool, and RelationshipsTool
classes for exploring the HyperX knowledge graph. These tools enable agents
to discover neighbors, explain paths, and list relationships for entities.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from hyperx.agents.base import QualitySignals, ToolResult
from hyperx.exceptions import NotFoundError

if TYPE_CHECKING:
    from hyperx import HyperX


class ExplorerTool:
    """Explore neighbors within N hops from an entity.

    ExplorerTool enables agents to discover related entities by exploring
    the graph neighborhood around a starting entity. This is useful for
    understanding context, finding related concepts, and building knowledge
    about an entity's relationships.

    The tool uses multi-hop path finding to discover reachable entities
    and can filter results by entity type.

    Attributes:
        name: Unique identifier for the tool ("hyperx_explore").
        description: Human-readable description for LLM function calling.

    Example:
        >>> from hyperx import HyperX
        >>> from hyperx.agents.tools import ExplorerTool
        >>>
        >>> client = HyperX(api_key="hx_sk_...")
        >>> explorer = ExplorerTool(client, default_max_hops=2)
        >>>
        >>> result = explorer.run(entity_id="e:react")
        >>> if result.success:
        ...     for neighbor in result.data["neighbors"]:
        ...         print(f"{neighbor['name']} ({neighbor['entity_type']})")
        ...
        ...     if result.quality.should_retrieve_more:
        ...         # Agent can decide to expand the search
        ...         print("Consider increasing max_hops")
    """

    def __init__(
        self,
        client: HyperX,
        *,
        default_max_hops: int = 2,
    ) -> None:
        """Initialize the ExplorerTool.

        Args:
            client: HyperX client instance for API calls.
            default_max_hops: Default maximum number of hops to explore.
                Higher values discover more distant neighbors.
                Defaults to 2.
        """
        self._client = client
        self._default_max_hops = default_max_hops

    @property
    def name(self) -> str:
        """Unique identifier for the tool."""
        return "hyperx_explore"

    @property
    def description(self) -> str:
        """Human-readable description of what the tool does."""
        return (
            "Explore neighbors within N hops from an entity in the HyperX "
            "knowledge graph. Discovers related entities by traversing "
            "hyperedge connections. Useful for understanding an entity's context "
            f"and finding related concepts. Default: up to {self._default_max_hops} hops."
        )

    def run(
        self,
        entity_id: str,
        *,
        max_hops: int | None = None,
        entity_types: list[str] | None = None,
    ) -> ToolResult:
        """Execute the explorer tool synchronously.

        Explores the graph neighborhood around an entity to discover
        related entities within the specified number of hops.

        Args:
            entity_id: Starting entity ID (e.g., "e:react").
            max_hops: Maximum number of hops to explore. Uses default_max_hops if not specified.
            entity_types: Optional list of entity types to filter results.
                Example: ["concept", "framework"] to only include these types.

        Returns:
            ToolResult containing:
                - success: Whether the exploration completed successfully
                - data: Dictionary with "entity" (the starting entity) and
                    "neighbors" (list of discovered neighbor entities with distance)
                - quality: QualitySignals for agentic self-correction
                - explanation: Human-readable summary of results
        """
        try:
            effective_max_hops = max_hops if max_hops is not None else self._default_max_hops

            # First, get the starting entity to validate it exists
            starting_entity = self._client.entities.get(entity_id)
            starting_entity_data = starting_entity.model_dump()

            # Use search with role_filter to find hyperedges involving this entity
            # This discovers neighbors through the hyperedge connections
            search_result = self._client.search(
                starting_entity.name,
                limit=50,  # Get a good number of related results
            )

            # Collect neighbors from hyperedges
            neighbors: list[dict[str, Any]] = []
            seen_ids = {entity_id}

            # Add entities from search results
            for entity in search_result.entities:
                if entity.id not in seen_ids:
                    entity_data = entity.model_dump()
                    entity_data["distance"] = 1  # Direct search match
                    neighbors.append(entity_data)
                    seen_ids.add(entity.id)

            # Also explore via hyperedges for additional depth
            for hyperedge in search_result.hyperedges:
                for member in hyperedge.members:
                    if member.entity_id not in seen_ids:
                        try:
                            member_entity = self._client.entities.get(member.entity_id)
                            member_data = member_entity.model_dump()
                            member_data["distance"] = 1
                            member_data["role"] = member.role
                            neighbors.append(member_data)
                            seen_ids.add(member.entity_id)
                        except NotFoundError:
                            # Entity might have been deleted or doesn't exist
                            pass

            # If we want more hops, use paths.find to discover further neighbors
            if effective_max_hops > 1 and neighbors:
                # Sample some neighbors to explore further
                sample_neighbors = neighbors[:5]
                for neighbor in sample_neighbors:
                    try:
                        # Find paths from starting entity to this neighbor's neighbors
                        paths = self._client.paths.find(
                            from_entity=entity_id,
                            to_entity=neighbor["id"],
                            max_hops=effective_max_hops,
                            k_paths=2,
                        )
                        # Extract bridge entities from paths
                        for path in paths:
                            for bridge_set in path.bridges:
                                for bridge_id in bridge_set:
                                    if bridge_id not in seen_ids:
                                        try:
                                            bridge_entity = self._client.entities.get(bridge_id)
                                            bridge_data = bridge_entity.model_dump()
                                            bridge_data["distance"] = 2
                                            neighbors.append(bridge_data)
                                            seen_ids.add(bridge_id)
                                        except NotFoundError:
                                            pass
                    except Exception:
                        # Path finding failed for this pair, continue
                        pass

            # Filter by entity types if specified
            if entity_types:
                neighbors = [
                    n for n in neighbors
                    if n.get("entity_type") in entity_types
                ]

            # Sort by distance then name
            neighbors.sort(key=lambda x: (x.get("distance", 999), x.get("name", "")))

            # Compute quality signals
            quality = self._compute_quality_signals(neighbors, entity_id)

            # Build explanation
            explanation = self._build_explanation(
                entity_id=entity_id,
                entity_name=starting_entity.name,
                neighbor_count=len(neighbors),
                max_hops=effective_max_hops,
                quality=quality,
            )

            return ToolResult(
                success=True,
                data={
                    "entity": starting_entity_data,
                    "neighbors": neighbors,
                },
                quality=quality,
                explanation=explanation,
            )

        except NotFoundError:
            return ToolResult(
                success=False,
                data=None,
                quality=QualitySignals(
                    confidence=0.0,
                    relevance_scores=[],
                    coverage=0.0,
                    diversity=0.0,
                    should_retrieve_more=True,
                    suggested_refinements=["Verify the entity ID exists"],
                    alternative_queries=[],
                    missing_context_hints=[f"Entity not found: {entity_id}"],
                ),
                explanation=f"Entity not found: {entity_id}",
            )

        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                quality=QualitySignals(
                    confidence=0.0,
                    relevance_scores=[],
                    coverage=0.0,
                    diversity=0.0,
                    should_retrieve_more=True,
                    suggested_refinements=["Check network connectivity", "Verify API key"],
                    alternative_queries=[],
                    missing_context_hints=[f"Exploration failed: {e!s}"],
                ),
                explanation=f"Exploration failed: {e!s}",
            )

    async def arun(
        self,
        entity_id: str,
        *,
        max_hops: int | None = None,
        entity_types: list[str] | None = None,
    ) -> ToolResult:
        """Execute the explorer tool asynchronously.

        Note: This method currently wraps the synchronous implementation.
        For true async support, use AsyncHyperX client.

        Args:
            entity_id: Starting entity ID (e.g., "e:react").
            max_hops: Maximum number of hops to explore.
            entity_types: Optional list of entity types to filter results.

        Returns:
            ToolResult containing exploration results and quality signals.
        """
        return self.run(entity_id=entity_id, max_hops=max_hops, entity_types=entity_types)

    def to_openai_schema(self) -> dict[str, Any]:
        """Export tool definition as OpenAI function schema.

        Returns a dictionary conforming to OpenAI's function calling schema,
        suitable for use with the OpenAI API's `tools` parameter.

        Returns:
            Dictionary with OpenAI function calling schema.

        Example:
            >>> explorer = ExplorerTool(client)
            >>> schema = explorer.to_openai_schema()
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
                        "entity_id": {
                            "type": "string",
                            "description": (
                                "The starting entity ID for exploration. "
                                'Format: "e:entity_name" (e.g., "e:react", "e:python").'
                            ),
                        },
                        "max_hops": {
                            "type": "integer",
                            "description": (
                                f"Maximum number of hops to explore from the entity. "
                                f"Higher values discover more distant neighbors. "
                                f"Defaults to {self._default_max_hops}."
                            ),
                            "minimum": 1,
                            "maximum": 5,
                        },
                        "entity_types": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "Filter neighbors to only include these entity types. "
                                'Example: ["concept", "framework"].'
                            ),
                        },
                    },
                    "required": ["entity_id"],
                },
            },
        }

    def _compute_quality_signals(
        self,
        neighbors: list[dict[str, Any]],
        entity_id: str,
    ) -> QualitySignals:
        """Compute quality signals based on discovered neighbors.

        Args:
            neighbors: List of discovered neighbor entities.
            entity_id: Starting entity ID.

        Returns:
            QualitySignals instance with computed values.
        """
        if not neighbors:
            return QualitySignals(
                confidence=0.0,
                relevance_scores=[],
                coverage=0.0,
                diversity=0.0,
                should_retrieve_more=True,
                suggested_refinements=["Try increasing max_hops"],
                alternative_queries=[],
                missing_context_hints=[f"No neighbors found for {entity_id}"],
            )

        # Confidence based on number of neighbors found
        confidence = min(1.0, len(neighbors) / 10.0)

        # Relevance scores based on distance (closer = more relevant)
        relevance_scores = [
            1.0 / (n.get("distance", 1) + 1) for n in neighbors
        ]

        # Coverage based on neighbor count
        coverage = min(1.0, len(neighbors) / 10.0)

        # Diversity based on unique entity types
        unique_types = set(n.get("entity_type", "unknown") for n in neighbors)
        diversity = min(1.0, len(unique_types) / 5.0)

        # Should retrieve more if we have few neighbors
        should_retrieve_more = len(neighbors) < 3

        suggested_refinements = []
        if should_retrieve_more:
            suggested_refinements.append("Try increasing max_hops for more neighbors")

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
        entity_id: str,
        entity_name: str,
        neighbor_count: int,
        max_hops: int,
        quality: QualitySignals,
    ) -> str:
        """Build a human-readable explanation of the exploration results.

        Args:
            entity_id: Starting entity ID.
            entity_name: Starting entity name.
            neighbor_count: Number of neighbors found.
            max_hops: Maximum hops used.
            quality: Quality signals from the analysis.

        Returns:
            Human-readable explanation string.
        """
        parts = []

        # Result summary
        if neighbor_count == 0:
            parts.append(f"No neighbors found for '{entity_name}' ({entity_id}) within {max_hops} hops.")
        elif neighbor_count == 1:
            parts.append(f"Found 1 neighbor for '{entity_name}' within {max_hops} hops.")
        else:
            parts.append(f"Found {neighbor_count} neighbors for '{entity_name}' within {max_hops} hops.")

        # Confidence assessment
        if quality.confidence >= 0.8:
            parts.append("Good coverage of the entity's neighborhood.")
        elif quality.confidence >= 0.5:
            parts.append("Moderate coverage - more neighbors may exist.")
        else:
            parts.append("Limited coverage - consider increasing max_hops.")

        # Retrieval suggestion
        if quality.should_retrieve_more:
            parts.append("Consider expanding the search radius.")

        return " ".join(parts)


class ExplainTool:
    """Get human-readable explanations of paths or relationships.

    ExplainTool helps agents understand the meaning of paths and relationships
    by fetching hyperedge details and building narrative explanations.
    This is useful for synthesizing knowledge and generating summaries.

    Attributes:
        name: Unique identifier for the tool ("hyperx_explain").
        description: Human-readable description for LLM function calling.

    Example:
        >>> from hyperx import HyperX
        >>> from hyperx.agents.tools import ExplainTool
        >>>
        >>> client = HyperX(api_key="hx_sk_...")
        >>> explain = ExplainTool(client)
        >>>
        >>> # Explain a path of hyperedge IDs
        >>> result = explain.run(ids=["h:react-hooks", "h:hooks-state"])
        >>> if result.success:
        ...     print(result.data["narrative"])
    """

    def __init__(self, client: HyperX) -> None:
        """Initialize the ExplainTool.

        Args:
            client: HyperX client instance for API calls.
        """
        self._client = client

    @property
    def name(self) -> str:
        """Unique identifier for the tool."""
        return "hyperx_explain"

    @property
    def description(self) -> str:
        """Human-readable description of what the tool does."""
        return (
            "Get human-readable explanations of paths or relationships in the HyperX "
            "knowledge graph. Takes a list of hyperedge IDs and builds a narrative "
            "explanation from their descriptions. Useful for synthesizing knowledge "
            "and generating summaries."
        )

    def run(self, ids: list[str]) -> ToolResult:
        """Execute the explain tool synchronously.

        Fetches hyperedges by ID and builds a narrative explanation
        from their descriptions.

        Args:
            ids: List of hyperedge IDs to explain. IDs should start with "h:".
                Example: ["h:react-hooks", "h:hooks-state"]

        Returns:
            ToolResult containing:
                - success: Whether the explanation was generated successfully
                - data: Dictionary with "hyperedges" (full details) and
                    "narrative" (human-readable explanation)
                - quality: QualitySignals for agentic self-correction
                - explanation: Summary of the explanation
        """
        try:
            if not ids:
                return ToolResult(
                    success=False,
                    data=None,
                    quality=QualitySignals(
                        confidence=0.0,
                        relevance_scores=[],
                        coverage=0.0,
                        diversity=0.0,
                        should_retrieve_more=True,
                        suggested_refinements=["Provide at least one hyperedge ID"],
                        alternative_queries=[],
                        missing_context_hints=["No IDs provided to explain"],
                    ),
                    explanation="No IDs provided to explain.",
                )

            # Fetch each hyperedge
            hyperedges: list[dict[str, Any]] = []
            failed_ids: list[str] = []

            for hid in ids:
                try:
                    # Handle both entity and hyperedge IDs
                    if hid.startswith("h:"):
                        hyperedge = self._client.hyperedges.get(hid)
                        hyperedges.append(hyperedge.model_dump())
                    elif hid.startswith("e:"):
                        # For entity IDs, search for related hyperedges
                        entity = self._client.entities.get(hid)
                        # Add entity info as a pseudo-hyperedge for the narrative
                        hyperedges.append({
                            "id": hid,
                            "description": f"Entity: {entity.name} (type: {entity.entity_type})",
                            "members": [],
                            "attributes": entity.attributes,
                            "confidence": entity.confidence,
                        })
                    else:
                        # Assume it's a hyperedge ID without prefix
                        try:
                            hyperedge = self._client.hyperedges.get(f"h:{hid}")
                            hyperedges.append(hyperedge.model_dump())
                        except NotFoundError:
                            failed_ids.append(hid)
                except NotFoundError:
                    failed_ids.append(hid)

            if not hyperedges:
                return ToolResult(
                    success=False,
                    data=None,
                    quality=QualitySignals(
                        confidence=0.0,
                        relevance_scores=[],
                        coverage=0.0,
                        diversity=0.0,
                        should_retrieve_more=True,
                        suggested_refinements=["Verify the IDs exist"],
                        alternative_queries=[],
                        missing_context_hints=[f"None of the IDs were found: {ids}"],
                    ),
                    explanation=f"None of the IDs were found: {ids}",
                )

            # Build narrative from descriptions
            narrative = self._build_narrative(hyperedges)

            # Compute quality signals
            found_ratio = len(hyperedges) / len(ids)
            confidence = found_ratio

            quality = QualitySignals(
                confidence=confidence,
                relevance_scores=[h.get("confidence", 1.0) for h in hyperedges],
                coverage=found_ratio,
                diversity=0.0,  # Not applicable for explanations
                should_retrieve_more=len(failed_ids) > 0,
                suggested_refinements=["Verify failed IDs exist"] if failed_ids else [],
                alternative_queries=[],
                missing_context_hints=[f"IDs not found: {failed_ids}"] if failed_ids else [],
            )

            # Build summary
            summary = f"Explained {len(hyperedges)} relationship(s)."
            if failed_ids:
                summary += f" {len(failed_ids)} ID(s) not found."

            return ToolResult(
                success=True,
                data={
                    "hyperedges": hyperedges,
                    "narrative": narrative,
                    "failed_ids": failed_ids,
                },
                quality=quality,
                explanation=summary,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                quality=QualitySignals(
                    confidence=0.0,
                    relevance_scores=[],
                    coverage=0.0,
                    diversity=0.0,
                    should_retrieve_more=True,
                    suggested_refinements=["Check network connectivity", "Verify API key"],
                    alternative_queries=[],
                    missing_context_hints=[f"Explanation failed: {e!s}"],
                ),
                explanation=f"Explanation failed: {e!s}",
            )

    async def arun(self, ids: list[str]) -> ToolResult:
        """Execute the explain tool asynchronously.

        Note: This method currently wraps the synchronous implementation.
        For true async support, use AsyncHyperX client.

        Args:
            ids: List of hyperedge IDs to explain.

        Returns:
            ToolResult containing explanation results and quality signals.
        """
        return self.run(ids=ids)

    def to_openai_schema(self) -> dict[str, Any]:
        """Export tool definition as OpenAI function schema.

        Returns a dictionary conforming to OpenAI's function calling schema,
        suitable for use with the OpenAI API's `tools` parameter.

        Returns:
            Dictionary with OpenAI function calling schema.

        Example:
            >>> explain = ExplainTool(client)
            >>> schema = explain.to_openai_schema()
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
                        "ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "List of hyperedge or entity IDs to explain. "
                                'Hyperedge IDs start with "h:" (e.g., "h:react-hooks"). '
                                'Entity IDs start with "e:" (e.g., "e:react").'
                            ),
                        },
                    },
                    "required": ["ids"],
                },
            },
        }

    def _build_narrative(self, hyperedges: list[dict[str, Any]]) -> str:
        """Build a narrative explanation from hyperedges.

        Args:
            hyperedges: List of hyperedge dictionaries with descriptions.

        Returns:
            Human-readable narrative string.
        """
        if not hyperedges:
            return "No relationships to explain."

        if len(hyperedges) == 1:
            return hyperedges[0].get("description", "No description available.")

        # Build a chain narrative for multiple hyperedges
        parts = []
        for i, h in enumerate(hyperedges):
            desc = h.get("description", "Unknown relationship")
            if i == 0:
                parts.append(desc)
            else:
                # Use transitional language
                parts.append(f"Furthermore, {desc.lower()}")

        return ". ".join(parts) + "."


class RelationshipsTool:
    """List all relationships involving an entity.

    RelationshipsTool enables agents to discover all hyperedges that
    involve a specific entity, optionally filtered by role. This is
    useful for understanding how an entity connects to others.

    Attributes:
        name: Unique identifier for the tool ("hyperx_relationships").
        description: Human-readable description for LLM function calling.

    Example:
        >>> from hyperx import HyperX
        >>> from hyperx.agents.tools import RelationshipsTool
        >>>
        >>> client = HyperX(api_key="hx_sk_...")
        >>> relationships = RelationshipsTool(client)
        >>>
        >>> result = relationships.run(entity_id="e:react")
        >>> if result.success:
        ...     for rel in result.data["relationships"]:
        ...         print(f"{rel['description']} (role: {rel['entity_role']})")
        >>>
        >>> # Filter by role
        >>> result = relationships.run(entity_id="e:react", role="subject")
        >>> if result.success:
        ...     print(f"Found {len(result.data['relationships'])} relationships as subject")
    """

    def __init__(self, client: HyperX) -> None:
        """Initialize the RelationshipsTool.

        Args:
            client: HyperX client instance for API calls.
        """
        self._client = client

    @property
    def name(self) -> str:
        """Unique identifier for the tool."""
        return "hyperx_relationships"

    @property
    def description(self) -> str:
        """Human-readable description of what the tool does."""
        return (
            "List all relationships (hyperedges) involving an entity in the HyperX "
            "knowledge graph. Can filter by role to find relationships where the "
            'entity plays a specific part (e.g., "subject", "object", "author"). '
            "Useful for understanding how an entity connects to others."
        )

    def run(
        self,
        entity_id: str,
        *,
        role: str | None = None,
    ) -> ToolResult:
        """Execute the relationships tool synchronously.

        Lists all hyperedges involving the specified entity, optionally
        filtered by the entity's role in those hyperedges.

        Args:
            entity_id: Entity ID to find relationships for (e.g., "e:react").
            role: Optional role filter. Only returns hyperedges where the
                entity has this specific role (e.g., "subject", "object").

        Returns:
            ToolResult containing:
                - success: Whether the lookup completed successfully
                - data: Dictionary with "entity" (the entity details) and
                    "relationships" (list of hyperedges with entity's role)
                - quality: QualitySignals for agentic self-correction
                - explanation: Human-readable summary of results
        """
        try:
            # First, get the entity to validate it exists and get its name
            entity = self._client.entities.get(entity_id)
            entity_data = entity.model_dump()

            # Search for hyperedges involving this entity
            # Use role_filter if a role is specified
            role_filter = {role: entity_id} if role else None

            search_result = self._client.search(
                entity.name,
                limit=50,
                role_filter=role_filter,
            )

            # Filter hyperedges to only those containing this entity
            relationships: list[dict[str, Any]] = []
            seen_ids = set()

            for hyperedge in search_result.hyperedges:
                # Check if the entity is a member
                entity_role = None
                for member in hyperedge.members:
                    if member.entity_id == entity_id:
                        entity_role = member.role
                        break

                if entity_role is not None and hyperedge.id not in seen_ids:
                    # If role filter is specified, only include if role matches
                    if role is None or entity_role == role:
                        rel_data = hyperedge.model_dump()
                        rel_data["entity_role"] = entity_role
                        relationships.append(rel_data)
                        seen_ids.add(hyperedge.id)

            # If we have no results from search, try listing hyperedges directly
            if not relationships:
                all_hyperedges = self._client.hyperedges.list(limit=100)
                for hyperedge in all_hyperedges:
                    entity_role = None
                    for member in hyperedge.members:
                        if member.entity_id == entity_id:
                            entity_role = member.role
                            break

                    if entity_role is not None and hyperedge.id not in seen_ids:
                        if role is None or entity_role == role:
                            rel_data = hyperedge.model_dump()
                            rel_data["entity_role"] = entity_role
                            relationships.append(rel_data)
                            seen_ids.add(hyperedge.id)

            # Compute quality signals
            quality = self._compute_quality_signals(relationships, entity_id, role)

            # Build explanation
            explanation = self._build_explanation(
                entity_id=entity_id,
                entity_name=entity.name,
                relationship_count=len(relationships),
                role=role,
                quality=quality,
            )

            return ToolResult(
                success=True,
                data={
                    "entity": entity_data,
                    "relationships": relationships,
                },
                quality=quality,
                explanation=explanation,
            )

        except NotFoundError:
            return ToolResult(
                success=False,
                data=None,
                quality=QualitySignals(
                    confidence=0.0,
                    relevance_scores=[],
                    coverage=0.0,
                    diversity=0.0,
                    should_retrieve_more=True,
                    suggested_refinements=["Verify the entity ID exists"],
                    alternative_queries=[],
                    missing_context_hints=[f"Entity not found: {entity_id}"],
                ),
                explanation=f"Entity not found: {entity_id}",
            )

        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                quality=QualitySignals(
                    confidence=0.0,
                    relevance_scores=[],
                    coverage=0.0,
                    diversity=0.0,
                    should_retrieve_more=True,
                    suggested_refinements=["Check network connectivity", "Verify API key"],
                    alternative_queries=[],
                    missing_context_hints=[f"Relationship lookup failed: {e!s}"],
                ),
                explanation=f"Relationship lookup failed: {e!s}",
            )

    async def arun(
        self,
        entity_id: str,
        *,
        role: str | None = None,
    ) -> ToolResult:
        """Execute the relationships tool asynchronously.

        Note: This method currently wraps the synchronous implementation.
        For true async support, use AsyncHyperX client.

        Args:
            entity_id: Entity ID to find relationships for.
            role: Optional role filter.

        Returns:
            ToolResult containing relationship results and quality signals.
        """
        return self.run(entity_id=entity_id, role=role)

    def to_openai_schema(self) -> dict[str, Any]:
        """Export tool definition as OpenAI function schema.

        Returns a dictionary conforming to OpenAI's function calling schema,
        suitable for use with the OpenAI API's `tools` parameter.

        Returns:
            Dictionary with OpenAI function calling schema.

        Example:
            >>> relationships = RelationshipsTool(client)
            >>> schema = relationships.to_openai_schema()
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
                        "entity_id": {
                            "type": "string",
                            "description": (
                                "The entity ID to find relationships for. "
                                'Format: "e:entity_name" (e.g., "e:react", "e:python").'
                            ),
                        },
                        "role": {
                            "type": "string",
                            "description": (
                                "Optional role filter. Only returns hyperedges where "
                                'the entity has this specific role (e.g., "subject", '
                                '"object", "author", "contributor").'
                            ),
                        },
                    },
                    "required": ["entity_id"],
                },
            },
        }

    def _compute_quality_signals(
        self,
        relationships: list[dict[str, Any]],
        entity_id: str,
        role: str | None,
    ) -> QualitySignals:
        """Compute quality signals based on discovered relationships.

        Args:
            relationships: List of discovered relationship hyperedges.
            entity_id: Entity ID being queried.
            role: Role filter if specified.

        Returns:
            QualitySignals instance with computed values.
        """
        if not relationships:
            hints = [f"No relationships found for {entity_id}"]
            if role:
                hints[0] += f" with role '{role}'"

            return QualitySignals(
                confidence=0.0,
                relevance_scores=[],
                coverage=0.0,
                diversity=0.0,
                should_retrieve_more=True,
                suggested_refinements=["Try without role filter"] if role else [],
                alternative_queries=[],
                missing_context_hints=hints,
            )

        # Confidence based on number of relationships
        confidence = min(1.0, len(relationships) / 5.0)

        # Relevance scores based on hyperedge confidence
        relevance_scores = [r.get("confidence", 1.0) for r in relationships]

        # Coverage based on relationship count
        coverage = min(1.0, len(relationships) / 10.0)

        # Diversity based on unique roles
        unique_roles = set(r.get("entity_role", "unknown") for r in relationships)
        diversity = min(1.0, len(unique_roles) / 3.0)

        # Should retrieve more if role filter might be limiting
        should_retrieve_more = role is not None and len(relationships) < 2

        suggested_refinements = []
        if should_retrieve_more:
            suggested_refinements.append("Try without role filter for more relationships")

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
        entity_id: str,
        entity_name: str,
        relationship_count: int,
        role: str | None,
        quality: QualitySignals,
    ) -> str:
        """Build a human-readable explanation of the relationship results.

        Args:
            entity_id: Entity ID.
            entity_name: Entity name.
            relationship_count: Number of relationships found.
            role: Role filter if specified.
            quality: Quality signals from the analysis.

        Returns:
            Human-readable explanation string.
        """
        parts = []

        # Result summary
        role_suffix = f" as '{role}'" if role else ""
        if relationship_count == 0:
            parts.append(f"No relationships found for '{entity_name}'{role_suffix}.")
        elif relationship_count == 1:
            parts.append(f"Found 1 relationship for '{entity_name}'{role_suffix}.")
        else:
            parts.append(f"Found {relationship_count} relationships for '{entity_name}'{role_suffix}.")

        # Diversity assessment
        if quality.diversity >= 0.6:
            parts.append("Diverse set of relationship roles.")
        elif quality.diversity >= 0.3:
            parts.append("Moderate variety of relationship roles.")

        # Retrieval suggestion
        if quality.should_retrieve_more:
            parts.append("Consider removing role filter for more results.")

        return " ".join(parts)
