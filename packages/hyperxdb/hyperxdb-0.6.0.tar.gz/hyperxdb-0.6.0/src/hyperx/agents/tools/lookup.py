"""LookupTool for agentic RAG workflows.

This module provides the LookupTool class which wraps HyperX entity and
hyperedge retrieval by ID in a tool interface compatible with LLM function calling.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from hyperx.agents.base import QualitySignals, ToolResult
from hyperx.exceptions import NotFoundError

if TYPE_CHECKING:
    from hyperx import HyperX


class LookupTool:
    """Lookup tool for retrieving entities or hyperedges by ID from HyperX.

    LookupTool provides a simple interface for direct ID-based retrieval of
    entities and hyperedges. This is useful for agents that need to fetch
    specific items by their known ID, such as following up on search results
    or traversing graph relationships.

    The tool automatically detects the type of resource to fetch based on
    the ID prefix:
        - "h:" prefix: Fetches a hyperedge
        - Otherwise: Fetches an entity (e.g., "e:uuid...")

    Quality signals for direct lookup are straightforward:
        - confidence = 1.0 (direct lookup is always confident when found)
        - should_retrieve_more = False (we have the exact item requested)

    Attributes:
        name: Unique identifier for the tool ("hyperx_lookup").
        description: Human-readable description for LLM function calling.

    Example:
        >>> from hyperx import HyperX
        >>> from hyperx.agents.tools import LookupTool
        >>>
        >>> client = HyperX(api_key="hx_sk_...")
        >>> lookup = LookupTool(client)
        >>>
        >>> # Lookup an entity by ID
        >>> result = lookup.run(id="e:react")
        >>> if result.success:
        ...     print(result.data["name"])
        >>>
        >>> # Lookup a hyperedge by ID
        >>> result = lookup.run(id="h:react-hooks")
        >>> if result.success:
        ...     print(result.data["description"])
    """

    def __init__(self, client: HyperX) -> None:
        """Initialize the LookupTool.

        Args:
            client: HyperX client instance for API calls.
        """
        self._client = client

    @property
    def name(self) -> str:
        """Unique identifier for the tool."""
        return "hyperx_lookup"

    @property
    def description(self) -> str:
        """Human-readable description of what the tool does."""
        return (
            "Look up an entity or hyperedge by ID from the HyperX knowledge graph. "
            "Use 'h:' prefix for hyperedges, otherwise treats ID as an entity. "
            "Returns the complete item data including attributes and metadata."
        )

    def run(self, id: str) -> ToolResult:
        """Execute the lookup tool synchronously.

        Fetches an entity or hyperedge by ID from the HyperX knowledge graph.
        The ID prefix determines which resource type to fetch:
            - "h:" prefix: Fetches a hyperedge
            - Otherwise: Fetches an entity

        Args:
            id: The ID of the entity or hyperedge to look up.
                Examples: "e:react", "e:uuid-...", "h:react-hooks"

        Returns:
            ToolResult containing:
                - success: Whether the lookup completed successfully
                - data: Dictionary with the entity or hyperedge data (model_dump)
                - quality: QualitySignals (confidence=1.0 for found items)
                - explanation: Human-readable summary of the result
        """
        try:
            # Detect resource type by prefix
            if id.startswith("h:"):
                item = self._client.hyperedges.get(id)
                item_type = "hyperedge"
            else:
                item = self._client.entities.get(id)
                item_type = "entity"

            # Convert to dictionary
            item_data = item.model_dump()

            # Direct lookup has perfect quality signals
            quality = QualitySignals(
                confidence=1.0,
                relevance_scores=[1.0],
                coverage=1.0,
                diversity=0.0,  # Single result has no diversity
                should_retrieve_more=False,
                suggested_refinements=[],
                alternative_queries=[],
                missing_context_hints=[],
            )

            # Build explanation
            if item_type == "hyperedge":
                name_or_desc = item_data.get("description", id)
                explanation = f"Found hyperedge '{name_or_desc}' with ID {id}."
            else:
                name_or_desc = item_data.get("name", id)
                explanation = f"Found entity '{name_or_desc}' with ID {id}."

            return ToolResult(
                success=True,
                data=item_data,
                quality=quality,
                explanation=explanation,
            )

        except NotFoundError:
            # Return failed result for not found
            return ToolResult(
                success=False,
                data=None,
                quality=QualitySignals(
                    confidence=0.0,
                    relevance_scores=[],
                    coverage=0.0,
                    diversity=0.0,
                    should_retrieve_more=True,
                    suggested_refinements=["Verify the ID exists", "Try searching instead"],
                    alternative_queries=[],
                    missing_context_hints=[f"No item found with ID '{id}'"],
                ),
                explanation=f"Item not found with ID '{id}'.",
            )

        except Exception as e:
            # Return failed result for other errors
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
                    missing_context_hints=[f"Lookup failed: {e!s}"],
                ),
                explanation=f"Lookup failed: {e!s}",
            )

    async def arun(self, id: str) -> ToolResult:
        """Execute the lookup tool asynchronously.

        Fetches an entity or hyperedge by ID from the HyperX knowledge graph.

        Note: This method currently wraps the synchronous implementation.
        For true async support, use AsyncHyperX client.

        Args:
            id: The ID of the entity or hyperedge to look up.

        Returns:
            ToolResult containing the lookup result and quality signals.
        """
        # Currently wraps sync implementation
        # For true async, would need AsyncHyperX client
        return self.run(id=id)

    def to_openai_schema(self) -> dict[str, Any]:
        """Export tool definition as OpenAI function schema.

        Returns a dictionary conforming to OpenAI's function calling schema,
        suitable for use with the OpenAI API's `tools` parameter.

        Returns:
            Dictionary with OpenAI function calling schema.

        Example:
            >>> lookup = LookupTool(client)
            >>> schema = lookup.to_openai_schema()
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
                        "id": {
                            "type": "string",
                            "description": (
                                "The ID of the entity or hyperedge to look up. "
                                "Use 'h:' prefix for hyperedges (e.g., 'h:react-hooks'). "
                                "Entity IDs typically have 'e:' prefix (e.g., 'e:react')."
                            ),
                        },
                    },
                    "required": ["id"],
                },
            },
        }
