"""CRUD tools for agentic RAG workflows.

This module provides EntityCrudTool and HyperedgeCrudTool classes which wrap
HyperX entity and hyperedge CRUD operations in tool interfaces compatible
with LLM function calling. These are "full" access level tools that allow
AI agents to create, update, and delete graph data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from hyperx.agents.base import QualitySignals, ToolResult
from hyperx.exceptions import NotFoundError

if TYPE_CHECKING:
    from hyperx import HyperX


class EntityCrudTool:
    """CRUD tool for creating, updating, and deleting entities in HyperX.

    EntityCrudTool provides a unified interface for all entity write operations.
    This is a "full" access level tool that allows AI agents to modify the
    knowledge graph by creating new entities, updating existing ones, or
    deleting them entirely.

    The tool uses an action-based interface where the 'action' parameter
    determines which operation to perform:
        - "create": Create a new entity (requires name, entity_type)
        - "update": Update an existing entity (requires entity_id)
        - "delete": Delete an entity (requires entity_id)

    Quality signals for write operations are minimal since there's no retrieval
    quality to measure - success/failure is the primary indicator.

    Attributes:
        name: Unique identifier for the tool ("hyperx_entity").
        description: Human-readable description for LLM function calling.

    Example:
        >>> from hyperx import HyperX
        >>> from hyperx.agents.tools import EntityCrudTool
        >>>
        >>> client = HyperX(api_key="hx_sk_...")
        >>> entity_tool = EntityCrudTool(client)
        >>>
        >>> # Create an entity
        >>> result = entity_tool.run(
        ...     action="create",
        ...     name="React",
        ...     entity_type="framework",
        ...     attributes={"version": "18.2"}
        ... )
        >>> if result.success:
        ...     print(f"Created entity: {result.data['id']}")
        >>>
        >>> # Update an entity
        >>> result = entity_tool.run(
        ...     action="update",
        ...     entity_id="e:react",
        ...     attributes={"version": "19.0"}
        ... )
        >>>
        >>> # Delete an entity
        >>> result = entity_tool.run(action="delete", entity_id="e:react")
    """

    VALID_ACTIONS = {"create", "update", "delete"}

    def __init__(self, client: HyperX) -> None:
        """Initialize the EntityCrudTool.

        Args:
            client: HyperX client instance for API calls.
        """
        self._client = client

    @property
    def name(self) -> str:
        """Unique identifier for the tool."""
        return "hyperx_entity"

    @property
    def description(self) -> str:
        """Human-readable description of what the tool does."""
        return (
            "Create, update, or delete entities in the HyperX knowledge graph. "
            "Use action='create' with name and entity_type to create a new entity. "
            "Use action='update' with entity_id and fields to modify to update. "
            "Use action='delete' with entity_id to remove an entity."
        )

    def run(
        self,
        action: str | None = None,
        entity_id: str | None = None,
        name: str | None = None,
        entity_type: str | None = None,
        attributes: dict[str, Any] | None = None,
        embedding: list[float] | None = None,
        **kwargs: Any,
    ) -> ToolResult:
        """Execute the entity CRUD tool synchronously.

        Args:
            action: The action to perform ("create", "update", or "delete").
            entity_id: The ID of the entity (required for update/delete).
            name: Human-readable name for the entity (required for create).
            entity_type: Type classification (required for create).
            attributes: Optional key-value attributes.
            embedding: Optional vector embedding (for create).
            **kwargs: Additional arguments (ignored).

        Returns:
            ToolResult containing:
                - success: Whether the operation completed successfully
                - data: Dictionary with the entity data (for create/update)
                        or None (for delete)
                - quality: QualitySignals (default for write operations)
                - explanation: Human-readable summary of the result
        """
        # Validate action
        if action is None:
            return self._failed_result("Missing required parameter: action")

        if action not in self.VALID_ACTIONS:
            return self._failed_result(
                f"Invalid action '{action}'. Must be one of: {', '.join(self.VALID_ACTIONS)}"
            )

        # Dispatch to appropriate handler
        try:
            if action == "create":
                return self._handle_create(name, entity_type, attributes, embedding)
            elif action == "update":
                return self._handle_update(entity_id, name, entity_type, attributes)
            else:  # delete
                return self._handle_delete(entity_id)

        except NotFoundError:
            return self._failed_result(
                f"Entity not found with ID '{entity_id}'.",
                missing_hints=[f"No entity found with ID '{entity_id}'"],
            )
        except Exception as e:
            return self._failed_result(
                f"Operation failed: {e!s}",
                suggested_refinements=["Check network connectivity", "Verify API key"],
            )

    def _handle_create(
        self,
        name: str | None,
        entity_type: str | None,
        attributes: dict[str, Any] | None,
        embedding: list[float] | None,
    ) -> ToolResult:
        """Handle create action."""
        # Validate required fields
        if name is None:
            return self._failed_result("Missing required parameter: name (for create)")
        if entity_type is None:
            return self._failed_result(
                "Missing required parameter: entity_type (for create)"
            )

        # Create the entity
        entity = self._client.entities.create(
            name=name,
            entity_type=entity_type,
            attributes=attributes,
            embedding=embedding,
        )

        return ToolResult(
            success=True,
            data=entity.model_dump(),
            quality=self._write_quality_signals(),
            explanation=f"Created entity '{name}' with ID {entity.id}.",
        )

    def _handle_update(
        self,
        entity_id: str | None,
        name: str | None,
        entity_type: str | None,
        attributes: dict[str, Any] | None,
    ) -> ToolResult:
        """Handle update action."""
        # Validate required fields
        if entity_id is None:
            return self._failed_result(
                "Missing required parameter: entity_id (for update)"
            )

        # Update the entity
        entity = self._client.entities.update(
            entity_id=entity_id,
            name=name,
            entity_type=entity_type,
            attributes=attributes,
        )

        return ToolResult(
            success=True,
            data=entity.model_dump(),
            quality=self._write_quality_signals(),
            explanation=f"Updated entity '{entity.name}' (ID: {entity.id}).",
        )

    def _handle_delete(self, entity_id: str | None) -> ToolResult:
        """Handle delete action."""
        # Validate required fields
        if entity_id is None:
            return self._failed_result(
                "Missing required parameter: entity_id (for delete)"
            )

        # Delete the entity
        self._client.entities.delete(entity_id)

        return ToolResult(
            success=True,
            data={"deleted": True, "entity_id": entity_id},
            quality=self._write_quality_signals(),
            explanation=f"Successfully deleted entity with ID '{entity_id}'.",
        )

    async def arun(
        self,
        action: str | None = None,
        entity_id: str | None = None,
        name: str | None = None,
        entity_type: str | None = None,
        attributes: dict[str, Any] | None = None,
        embedding: list[float] | None = None,
        **kwargs: Any,
    ) -> ToolResult:
        """Execute the entity CRUD tool asynchronously.

        Note: This method currently wraps the synchronous implementation.
        For true async support, use AsyncHyperX client.

        Args:
            action: The action to perform ("create", "update", or "delete").
            entity_id: The ID of the entity (required for update/delete).
            name: Human-readable name for the entity (required for create).
            entity_type: Type classification (required for create).
            attributes: Optional key-value attributes.
            embedding: Optional vector embedding (for create).
            **kwargs: Additional arguments (ignored).

        Returns:
            ToolResult containing the operation result and quality signals.
        """
        return self.run(
            action=action,
            entity_id=entity_id,
            name=name,
            entity_type=entity_type,
            attributes=attributes,
            embedding=embedding,
            **kwargs,
        )

    def to_openai_schema(self) -> dict[str, Any]:
        """Export tool definition as OpenAI function schema.

        Returns a dictionary conforming to OpenAI's function calling schema,
        suitable for use with the OpenAI API's `tools` parameter.

        Returns:
            Dictionary with OpenAI function calling schema.

        Example:
            >>> entity_tool = EntityCrudTool(client)
            >>> schema = entity_tool.to_openai_schema()
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
                        "action": {
                            "type": "string",
                            "description": (
                                "The action to perform: 'create' to make a new entity, "
                                "'update' to modify an existing entity, or 'delete' to "
                                "remove an entity."
                            ),
                            "enum": ["create", "update", "delete"],
                        },
                        "entity_id": {
                            "type": "string",
                            "description": (
                                "The ID of the entity to update or delete. "
                                "Required for 'update' and 'delete' actions. "
                                "Example: 'e:react' or 'e:uuid-...'."
                            ),
                        },
                        "name": {
                            "type": "string",
                            "description": (
                                "Human-readable name for the entity. "
                                "Required for 'create', optional for 'update'."
                            ),
                        },
                        "entity_type": {
                            "type": "string",
                            "description": (
                                "Type classification for the entity "
                                "(e.g., 'concept', 'person', 'document'). "
                                "Required for 'create', optional for 'update'."
                            ),
                        },
                        "attributes": {
                            "type": "object",
                            "description": (
                                "Optional key-value attributes for the entity. "
                                "Can be used with 'create' or 'update' actions."
                            ),
                        },
                        "embedding": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": (
                                "Optional vector embedding for the entity. "
                                "Only used with 'create' action."
                            ),
                        },
                    },
                    "required": ["action"],
                },
            },
        }

    def _write_quality_signals(self) -> QualitySignals:
        """Create quality signals for write operations.

        Write operations don't have retrieval quality to measure,
        so we return neutral/positive signals.
        """
        return QualitySignals(
            confidence=1.0,
            relevance_scores=[],
            coverage=1.0,
            diversity=0.0,
            should_retrieve_more=False,
            suggested_refinements=[],
            alternative_queries=[],
            missing_context_hints=[],
        )

    def _failed_result(
        self,
        explanation: str,
        suggested_refinements: list[str] | None = None,
        missing_hints: list[str] | None = None,
    ) -> ToolResult:
        """Create a failed ToolResult with appropriate quality signals."""
        return ToolResult(
            success=False,
            data=None,
            quality=QualitySignals(
                confidence=0.0,
                relevance_scores=[],
                coverage=0.0,
                diversity=0.0,
                should_retrieve_more=False,
                suggested_refinements=suggested_refinements or [],
                alternative_queries=[],
                missing_context_hints=missing_hints or [],
            ),
            explanation=explanation,
        )


class HyperedgeCrudTool:
    """CRUD tool for creating, updating, deprecating, and deleting hyperedges.

    HyperedgeCrudTool provides a unified interface for all hyperedge write
    operations. This is a "full" access level tool that allows AI agents to
    modify the knowledge graph by creating new relationships, updating existing
    ones, deprecating outdated relationships, or deleting them entirely.

    The tool uses an action-based interface where the 'action' parameter
    determines which operation to perform:
        - "create": Create a new hyperedge (requires description, participants)
        - "update": Update an existing hyperedge (requires hyperedge_id)
        - "deprecate": Mark a hyperedge as deprecated (requires hyperedge_id, reason)
        - "delete": Delete a hyperedge (requires hyperedge_id)

    Participants are specified as a list of dictionaries with 'entity_id' and
    'role' keys, defining which entities participate in the relationship and
    their semantic roles.

    Attributes:
        name: Unique identifier for the tool ("hyperx_hyperedge").
        description: Human-readable description for LLM function calling.

    Example:
        >>> from hyperx import HyperX
        >>> from hyperx.agents.tools import HyperedgeCrudTool
        >>>
        >>> client = HyperX(api_key="hx_sk_...")
        >>> edge_tool = HyperedgeCrudTool(client)
        >>>
        >>> # Create a hyperedge
        >>> result = edge_tool.run(
        ...     action="create",
        ...     description="React provides Hooks",
        ...     participants=[
        ...         {"entity_id": "e:react", "role": "subject"},
        ...         {"entity_id": "e:hooks", "role": "object"},
        ...     ]
        ... )
        >>> if result.success:
        ...     print(f"Created hyperedge: {result.data['id']}")
        >>>
        >>> # Update a hyperedge
        >>> result = edge_tool.run(
        ...     action="update",
        ...     hyperedge_id="h:react-hooks",
        ...     description="React framework provides Hooks API"
        ... )
        >>>
        >>> # Deprecate a hyperedge
        >>> result = edge_tool.run(
        ...     action="deprecate",
        ...     hyperedge_id="h:old-relation",
        ...     reason="Information is outdated"
        ... )
        >>>
        >>> # Delete a hyperedge
        >>> result = edge_tool.run(action="delete", hyperedge_id="h:obsolete")
    """

    VALID_ACTIONS = {"create", "update", "deprecate", "delete"}

    def __init__(self, client: HyperX) -> None:
        """Initialize the HyperedgeCrudTool.

        Args:
            client: HyperX client instance for API calls.
        """
        self._client = client

    @property
    def name(self) -> str:
        """Unique identifier for the tool."""
        return "hyperx_hyperedge"

    @property
    def description(self) -> str:
        """Human-readable description of what the tool does."""
        return (
            "Create, update, deprecate, or delete hyperedges (relationships) in the "
            "HyperX knowledge graph. Use action='create' with description and "
            "participants to create a new relationship. Use action='update' with "
            "hyperedge_id to modify. Use action='deprecate' with hyperedge_id and "
            "reason to mark as deprecated. Use action='delete' with hyperedge_id "
            "to remove."
        )

    def run(
        self,
        action: str | None = None,
        hyperedge_id: str | None = None,
        description: str | None = None,
        participants: list[dict[str, str]] | None = None,
        attributes: dict[str, Any] | None = None,
        reason: str | None = None,
        **kwargs: Any,
    ) -> ToolResult:
        """Execute the hyperedge CRUD tool synchronously.

        Args:
            action: The action to perform ("create", "update", "deprecate", "delete").
            hyperedge_id: The ID of the hyperedge (required for update/deprecate/delete).
            description: Human-readable description of the relationship (for create/update).
            participants: List of participant dicts with 'entity_id' and 'role' keys
                         (required for create, optional for update).
            attributes: Optional key-value attributes.
            reason: Reason for deprecation (required for deprecate action).
            **kwargs: Additional arguments (ignored).

        Returns:
            ToolResult containing:
                - success: Whether the operation completed successfully
                - data: Dictionary with the hyperedge data (for create/update/deprecate)
                        or None (for delete)
                - quality: QualitySignals (default for write operations)
                - explanation: Human-readable summary of the result
        """
        # Validate action
        if action is None:
            return self._failed_result("Missing required parameter: action")

        if action not in self.VALID_ACTIONS:
            return self._failed_result(
                f"Invalid action '{action}'. Must be one of: {', '.join(self.VALID_ACTIONS)}"
            )

        # Dispatch to appropriate handler
        try:
            if action == "create":
                return self._handle_create(description, participants, attributes)
            elif action == "update":
                return self._handle_update(
                    hyperedge_id, description, participants, attributes
                )
            elif action == "deprecate":
                return self._handle_deprecate(hyperedge_id, reason)
            else:  # delete
                return self._handle_delete(hyperedge_id)

        except NotFoundError:
            return self._failed_result(
                f"Hyperedge not found with ID '{hyperedge_id}'.",
                missing_hints=[f"No hyperedge found with ID '{hyperedge_id}'"],
            )
        except Exception as e:
            return self._failed_result(
                f"Operation failed: {e!s}",
                suggested_refinements=["Check network connectivity", "Verify API key"],
            )

    def _handle_create(
        self,
        description: str | None,
        participants: list[dict[str, str]] | None,
        attributes: dict[str, Any] | None,
    ) -> ToolResult:
        """Handle create action."""
        # Validate required fields
        if description is None:
            return self._failed_result(
                "Missing required parameter: description (for create)"
            )
        if participants is None or len(participants) == 0:
            return self._failed_result(
                "Missing required parameter: participants (for create)"
            )

        # Create the hyperedge
        hyperedge = self._client.hyperedges.create(
            description=description,
            members=participants,
            attributes=attributes,
        )

        return ToolResult(
            success=True,
            data=hyperedge.model_dump(),
            quality=self._write_quality_signals(),
            explanation=f"Created hyperedge '{description}' with ID {hyperedge.id}.",
        )

    def _handle_update(
        self,
        hyperedge_id: str | None,
        description: str | None,
        participants: list[dict[str, str]] | None,
        attributes: dict[str, Any] | None,
    ) -> ToolResult:
        """Handle update action."""
        # Validate required fields
        if hyperedge_id is None:
            return self._failed_result(
                "Missing required parameter: hyperedge_id (for update)"
            )

        # Update the hyperedge
        hyperedge = self._client.hyperedges.update(
            hyperedge_id=hyperedge_id,
            description=description,
            members=participants,
            attributes=attributes,
        )

        return ToolResult(
            success=True,
            data=hyperedge.model_dump(),
            quality=self._write_quality_signals(),
            explanation=f"Updated hyperedge (ID: {hyperedge.id}).",
        )

    def _handle_deprecate(
        self, hyperedge_id: str | None, reason: str | None
    ) -> ToolResult:
        """Handle deprecate action."""
        # Validate required fields
        if hyperedge_id is None:
            return self._failed_result(
                "Missing required parameter: hyperedge_id (for deprecate)"
            )
        if reason is None:
            return self._failed_result(
                "Missing required parameter: reason (for deprecate)"
            )

        # Deprecate the hyperedge
        hyperedge = self._client.hyperedges.deprecate(
            hyperedge_id=hyperedge_id,
            reason=reason,
        )

        return ToolResult(
            success=True,
            data=hyperedge.model_dump(),
            quality=self._write_quality_signals(),
            explanation=f"Successfully deprecated hyperedge (ID: {hyperedge_id}).",
        )

    def _handle_delete(self, hyperedge_id: str | None) -> ToolResult:
        """Handle delete action."""
        # Validate required fields
        if hyperedge_id is None:
            return self._failed_result(
                "Missing required parameter: hyperedge_id (for delete)"
            )

        # Delete the hyperedge
        self._client.hyperedges.delete(hyperedge_id)

        return ToolResult(
            success=True,
            data={"deleted": True, "hyperedge_id": hyperedge_id},
            quality=self._write_quality_signals(),
            explanation=f"Successfully deleted hyperedge with ID '{hyperedge_id}'.",
        )

    async def arun(
        self,
        action: str | None = None,
        hyperedge_id: str | None = None,
        description: str | None = None,
        participants: list[dict[str, str]] | None = None,
        attributes: dict[str, Any] | None = None,
        reason: str | None = None,
        **kwargs: Any,
    ) -> ToolResult:
        """Execute the hyperedge CRUD tool asynchronously.

        Note: This method currently wraps the synchronous implementation.
        For true async support, use AsyncHyperX client.

        Args:
            action: The action to perform ("create", "update", "deprecate", "delete").
            hyperedge_id: The ID of the hyperedge (required for update/deprecate/delete).
            description: Human-readable description of the relationship.
            participants: List of participant dicts with 'entity_id' and 'role' keys.
            attributes: Optional key-value attributes.
            reason: Reason for deprecation (required for deprecate action).
            **kwargs: Additional arguments (ignored).

        Returns:
            ToolResult containing the operation result and quality signals.
        """
        return self.run(
            action=action,
            hyperedge_id=hyperedge_id,
            description=description,
            participants=participants,
            attributes=attributes,
            reason=reason,
            **kwargs,
        )

    def to_openai_schema(self) -> dict[str, Any]:
        """Export tool definition as OpenAI function schema.

        Returns a dictionary conforming to OpenAI's function calling schema,
        suitable for use with the OpenAI API's `tools` parameter.

        Returns:
            Dictionary with OpenAI function calling schema.

        Example:
            >>> edge_tool = HyperedgeCrudTool(client)
            >>> schema = edge_tool.to_openai_schema()
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
                        "action": {
                            "type": "string",
                            "description": (
                                "The action to perform: 'create' to make a new hyperedge, "
                                "'update' to modify an existing hyperedge, 'deprecate' to "
                                "mark as deprecated with a reason, or 'delete' to remove."
                            ),
                            "enum": ["create", "update", "deprecate", "delete"],
                        },
                        "hyperedge_id": {
                            "type": "string",
                            "description": (
                                "The ID of the hyperedge to update, deprecate, or delete. "
                                "Required for 'update', 'deprecate', and 'delete' actions. "
                                "Example: 'h:react-hooks' or 'h:uuid-...'."
                            ),
                        },
                        "description": {
                            "type": "string",
                            "description": (
                                "Human-readable description of the relationship. "
                                "Required for 'create', optional for 'update'. "
                                "Example: 'React provides Hooks'."
                            ),
                        },
                        "participants": {
                            "type": "array",
                            "description": (
                                "List of entities participating in this relationship. "
                                "Required for 'create', optional for 'update'. "
                                "Each participant must have 'entity_id' and 'role'."
                            ),
                            "items": {
                                "type": "object",
                                "properties": {
                                    "entity_id": {
                                        "type": "string",
                                        "description": "The ID of the participating entity.",
                                    },
                                    "role": {
                                        "type": "string",
                                        "description": (
                                            "The semantic role of this entity in the relationship "
                                            "(e.g., 'subject', 'object', 'author', 'topic')."
                                        ),
                                    },
                                },
                                "required": ["entity_id", "role"],
                            },
                        },
                        "attributes": {
                            "type": "object",
                            "description": (
                                "Optional key-value attributes for the hyperedge. "
                                "Can be used with 'create' or 'update' actions."
                            ),
                        },
                        "reason": {
                            "type": "string",
                            "description": (
                                "Reason for deprecation. Required only for 'deprecate' action. "
                                "Example: 'Information is outdated'."
                            ),
                        },
                    },
                    "required": ["action"],
                },
            },
        }

    def _write_quality_signals(self) -> QualitySignals:
        """Create quality signals for write operations.

        Write operations don't have retrieval quality to measure,
        so we return neutral/positive signals.
        """
        return QualitySignals(
            confidence=1.0,
            relevance_scores=[],
            coverage=1.0,
            diversity=0.0,
            should_retrieve_more=False,
            suggested_refinements=[],
            alternative_queries=[],
            missing_context_hints=[],
        )

    def _failed_result(
        self,
        explanation: str,
        suggested_refinements: list[str] | None = None,
        missing_hints: list[str] | None = None,
    ) -> ToolResult:
        """Create a failed ToolResult with appropriate quality signals."""
        return ToolResult(
            success=False,
            data=None,
            quality=QualitySignals(
                confidence=0.0,
                relevance_scores=[],
                coverage=0.0,
                diversity=0.0,
                should_retrieve_more=False,
                suggested_refinements=suggested_refinements or [],
                alternative_queries=[],
                missing_context_hints=missing_hints or [],
            ),
            explanation=explanation,
        )
