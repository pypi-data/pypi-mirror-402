"""Tests for EntityCrudTool and HyperedgeCrudTool agents.

These tools provide "full" access level functionality for creating,
updating, and deleting entities and hyperedges in the knowledge graph.
"""

import pytest
from pytest_httpx import HTTPXMock

from hyperx import HyperX
from hyperx.agents import BaseTool, QualitySignals, ToolResult
from hyperx.agents.tools import EntityCrudTool, HyperedgeCrudTool


# Test constants
TEST_API_KEY = "hx_sk_test_12345678"
TEST_BASE_URL = "http://localhost:8080"


@pytest.fixture
def client() -> HyperX:
    """Create a HyperX client for testing."""
    c = HyperX(api_key=TEST_API_KEY, base_url=TEST_BASE_URL)
    yield c
    c.close()


def make_entity(
    id: str = "e:test",
    name: str = "Test Entity",
    entity_type: str = "concept",
    attributes: dict | None = None,
    confidence: float = 0.9,
) -> dict:
    """Helper to create mock entity."""
    return {
        "id": id,
        "name": name,
        "entity_type": entity_type,
        "attributes": attributes or {},
        "confidence": confidence,
        "created_at": "2026-01-15T00:00:00Z",
        "updated_at": "2026-01-15T00:00:00Z",
    }


def make_hyperedge(
    id: str = "h:test",
    description: str = "Test relationship",
    members: list[dict] | None = None,
    attributes: dict | None = None,
    confidence: float = 0.85,
) -> dict:
    """Helper to create mock hyperedge."""
    return {
        "id": id,
        "description": description,
        "members": members or [{"entity_id": "e:test", "role": "subject"}],
        "attributes": attributes or {},
        "confidence": confidence,
        "created_at": "2026-01-15T00:00:00Z",
        "updated_at": "2026-01-15T00:00:00Z",
    }


# =============================================================================
# EntityCrudTool Tests
# =============================================================================


class TestEntityCrudToolCreation:
    """Tests for EntityCrudTool initialization."""

    def test_creation(self, client: HyperX):
        """Test EntityCrudTool creation."""
        tool = EntityCrudTool(client)

        assert tool.name == "hyperx_entity"
        assert "entity" in tool.description.lower()
        assert "create" in tool.description.lower()
        assert "update" in tool.description.lower()
        assert "delete" in tool.description.lower()

    def test_implements_base_tool_protocol(self, client: HyperX):
        """Test EntityCrudTool implements BaseTool Protocol."""
        tool = EntityCrudTool(client)
        assert isinstance(tool, BaseTool)


class TestEntityCrudToolCreateAction:
    """Tests for EntityCrudTool create action."""

    def test_create_entity(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test creating an entity."""
        entity_data = make_entity(id="e:new", name="React", entity_type="framework")
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/entities",
            json=entity_data,
        )

        tool = EntityCrudTool(client)
        result = tool.run(
            action="create",
            name="React",
            entity_type="framework",
        )

        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.data is not None
        assert result.data["id"] == "e:new"
        assert result.data["name"] == "React"
        assert result.data["entity_type"] == "framework"

    def test_create_entity_with_attributes(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test creating an entity with attributes."""
        entity_data = make_entity(
            id="e:new",
            name="React",
            entity_type="framework",
            attributes={"version": "18.2"},
        )
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/entities",
            json=entity_data,
        )

        tool = EntityCrudTool(client)
        result = tool.run(
            action="create",
            name="React",
            entity_type="framework",
            attributes={"version": "18.2"},
        )

        assert result.success is True
        assert result.data["attributes"] == {"version": "18.2"}

    def test_create_entity_with_embedding(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test creating an entity with embedding."""
        entity_data = make_entity(id="e:new", name="React", entity_type="framework")
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/entities",
            json=entity_data,
        )

        tool = EntityCrudTool(client)
        embedding = [0.1, 0.2, 0.3]
        result = tool.run(
            action="create",
            name="React",
            entity_type="framework",
            embedding=embedding,
        )

        assert result.success is True
        # Verify embedding was sent in request
        request = httpx_mock.get_requests()[0]
        import json

        body = json.loads(request.content)
        assert body["embedding"] == embedding

    def test_create_entity_missing_required_fields(self, client: HyperX):
        """Test create returns error when required fields are missing."""
        tool = EntityCrudTool(client)

        # Missing name
        result = tool.run(action="create", entity_type="framework")
        assert result.success is False
        assert "name" in result.explanation.lower()

        # Missing entity_type
        result = tool.run(action="create", name="React")
        assert result.success is False
        assert "entity_type" in result.explanation.lower()

    def test_create_entity_quality_signals(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test create returns appropriate quality signals."""
        entity_data = make_entity(id="e:new", name="React", entity_type="framework")
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/entities",
            json=entity_data,
        )

        tool = EntityCrudTool(client)
        result = tool.run(action="create", name="React", entity_type="framework")

        assert isinstance(result.quality, QualitySignals)
        # Write operations use default quality signals
        assert result.quality.should_retrieve_more is False


class TestEntityCrudToolUpdateAction:
    """Tests for EntityCrudTool update action."""

    def test_update_entity(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test updating an entity."""
        entity_data = make_entity(id="e:123", name="React Updated", entity_type="framework")
        httpx_mock.add_response(
            method="PUT",
            url=f"{TEST_BASE_URL}/v1/entities/e:123",
            json=entity_data,
        )

        tool = EntityCrudTool(client)
        result = tool.run(
            action="update",
            entity_id="e:123",
            name="React Updated",
        )

        assert result.success is True
        assert result.data["name"] == "React Updated"

    def test_update_entity_with_attributes(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test updating entity attributes."""
        entity_data = make_entity(
            id="e:123",
            name="React",
            entity_type="framework",
            attributes={"version": "19.0"},
        )
        httpx_mock.add_response(
            method="PUT",
            url=f"{TEST_BASE_URL}/v1/entities/e:123",
            json=entity_data,
        )

        tool = EntityCrudTool(client)
        result = tool.run(
            action="update",
            entity_id="e:123",
            attributes={"version": "19.0"},
        )

        assert result.success is True
        assert result.data["attributes"] == {"version": "19.0"}

    def test_update_entity_missing_entity_id(self, client: HyperX):
        """Test update returns error when entity_id is missing."""
        tool = EntityCrudTool(client)
        result = tool.run(action="update", name="New Name")

        assert result.success is False
        assert "entity_id" in result.explanation.lower()

    def test_update_entity_not_found(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test update handles not found."""
        httpx_mock.add_response(
            method="PUT",
            url=f"{TEST_BASE_URL}/v1/entities/e:nonexistent",
            status_code=404,
            json={"error": "Entity not found"},
        )

        tool = EntityCrudTool(client)
        result = tool.run(action="update", entity_id="e:nonexistent", name="New")

        assert result.success is False
        assert "not found" in result.explanation.lower()


class TestEntityCrudToolDeleteAction:
    """Tests for EntityCrudTool delete action."""

    def test_delete_entity(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test deleting an entity."""
        httpx_mock.add_response(
            method="DELETE",
            url=f"{TEST_BASE_URL}/v1/entities/e:123",
            status_code=204,
        )

        tool = EntityCrudTool(client)
        result = tool.run(action="delete", entity_id="e:123")

        assert result.success is True
        assert "deleted" in result.explanation.lower()

    def test_delete_entity_missing_entity_id(self, client: HyperX):
        """Test delete returns error when entity_id is missing."""
        tool = EntityCrudTool(client)
        result = tool.run(action="delete")

        assert result.success is False
        assert "entity_id" in result.explanation.lower()

    def test_delete_entity_not_found(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test delete handles not found."""
        httpx_mock.add_response(
            method="DELETE",
            url=f"{TEST_BASE_URL}/v1/entities/e:nonexistent",
            status_code=404,
            json={"error": "Entity not found"},
        )

        tool = EntityCrudTool(client)
        result = tool.run(action="delete", entity_id="e:nonexistent")

        assert result.success is False
        assert "not found" in result.explanation.lower()


class TestEntityCrudToolInvalidAction:
    """Tests for EntityCrudTool with invalid actions."""

    def test_invalid_action(self, client: HyperX):
        """Test invalid action returns error."""
        tool = EntityCrudTool(client)
        result = tool.run(action="invalid_action")

        assert result.success is False
        assert "action" in result.explanation.lower()
        assert "invalid" in result.explanation.lower()

    def test_missing_action(self, client: HyperX):
        """Test missing action returns error."""
        tool = EntityCrudTool(client)
        result = tool.run(name="Test")

        assert result.success is False
        assert "action" in result.explanation.lower()


class TestEntityCrudToolOpenAISchema:
    """Tests for EntityCrudTool OpenAI schema generation."""

    def test_to_openai_schema_structure(self, client: HyperX):
        """Test to_openai_schema() returns valid OpenAI function schema."""
        tool = EntityCrudTool(client)
        schema = tool.to_openai_schema()

        # Required top-level structure
        assert schema["type"] == "function"
        assert "function" in schema

        func = schema["function"]
        assert func["name"] == "hyperx_entity"
        assert "description" in func
        assert "parameters" in func

        # Parameters structure
        params = func["parameters"]
        assert params["type"] == "object"
        assert "properties" in params
        assert "required" in params

    def test_schema_has_action_as_required(self, client: HyperX):
        """Test schema has action as required parameter."""
        tool = EntityCrudTool(client)
        schema = tool.to_openai_schema()

        params = schema["function"]["parameters"]
        assert "action" in params["required"]
        assert "action" in params["properties"]

    def test_schema_action_has_enum(self, client: HyperX):
        """Test action parameter has enum values."""
        tool = EntityCrudTool(client)
        schema = tool.to_openai_schema()

        action_prop = schema["function"]["parameters"]["properties"]["action"]
        assert "enum" in action_prop
        assert set(action_prop["enum"]) == {"create", "update", "delete"}

    def test_schema_has_entity_fields(self, client: HyperX):
        """Test schema has entity field parameters."""
        tool = EntityCrudTool(client)
        schema = tool.to_openai_schema()

        props = schema["function"]["parameters"]["properties"]
        assert "name" in props
        assert "entity_type" in props
        assert "entity_id" in props
        assert "attributes" in props
        assert "embedding" in props


class TestEntityCrudToolAsync:
    """Tests for EntityCrudTool async arun() method."""

    @pytest.mark.asyncio
    async def test_arun_create(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test arun() create action."""
        entity_data = make_entity(id="e:new", name="React", entity_type="framework")
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/entities",
            json=entity_data,
        )

        tool = EntityCrudTool(client)
        result = await tool.arun(action="create", name="React", entity_type="framework")

        assert isinstance(result, ToolResult)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_arun_update(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test arun() update action."""
        entity_data = make_entity(id="e:123", name="Updated", entity_type="framework")
        httpx_mock.add_response(
            method="PUT",
            url=f"{TEST_BASE_URL}/v1/entities/e:123",
            json=entity_data,
        )

        tool = EntityCrudTool(client)
        result = await tool.arun(action="update", entity_id="e:123", name="Updated")

        assert result.success is True

    @pytest.mark.asyncio
    async def test_arun_delete(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test arun() delete action."""
        httpx_mock.add_response(
            method="DELETE",
            url=f"{TEST_BASE_URL}/v1/entities/e:123",
            status_code=204,
        )

        tool = EntityCrudTool(client)
        result = await tool.arun(action="delete", entity_id="e:123")

        assert result.success is True


class TestEntityCrudToolErrorHandling:
    """Tests for EntityCrudTool error handling."""

    def test_api_error_returns_failed_tool_result(
        self, client: HyperX, httpx_mock: HTTPXMock
    ):
        """Test API error returns failed ToolResult."""
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/entities",
            status_code=500,
            json={"error": "Internal server error"},
        )

        tool = EntityCrudTool(client)
        result = tool.run(action="create", name="Test", entity_type="concept")

        assert result.success is False
        assert "failed" in result.explanation.lower()

    def test_network_error_returns_failed_tool_result(
        self, client: HyperX, httpx_mock: HTTPXMock
    ):
        """Test network error returns failed ToolResult."""
        import httpx

        httpx_mock.add_exception(httpx.ConnectError("Connection refused"))

        tool = EntityCrudTool(client)
        result = tool.run(action="create", name="Test", entity_type="concept")

        assert result.success is False
        assert "failed" in result.explanation.lower()


# =============================================================================
# HyperedgeCrudTool Tests
# =============================================================================


class TestHyperedgeCrudToolCreation:
    """Tests for HyperedgeCrudTool initialization."""

    def test_creation(self, client: HyperX):
        """Test HyperedgeCrudTool creation."""
        tool = HyperedgeCrudTool(client)

        assert tool.name == "hyperx_hyperedge"
        assert "hyperedge" in tool.description.lower()
        assert "create" in tool.description.lower()
        assert "update" in tool.description.lower()
        assert "delete" in tool.description.lower()
        assert "deprecate" in tool.description.lower()

    def test_implements_base_tool_protocol(self, client: HyperX):
        """Test HyperedgeCrudTool implements BaseTool Protocol."""
        tool = HyperedgeCrudTool(client)
        assert isinstance(tool, BaseTool)


class TestHyperedgeCrudToolCreateAction:
    """Tests for HyperedgeCrudTool create action."""

    def test_create_hyperedge(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test creating a hyperedge."""
        members = [
            {"entity_id": "e:react", "role": "subject"},
            {"entity_id": "e:hooks", "role": "object"},
        ]
        hyperedge_data = make_hyperedge(
            id="h:new",
            description="React provides Hooks",
            members=members,
        )
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/hyperedges",
            json=hyperedge_data,
        )

        tool = HyperedgeCrudTool(client)
        result = tool.run(
            action="create",
            description="React provides Hooks",
            participants=members,
        )

        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.data is not None
        assert result.data["id"] == "h:new"
        assert result.data["description"] == "React provides Hooks"
        assert len(result.data["members"]) == 2

    def test_create_hyperedge_with_attributes(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test creating a hyperedge with attributes."""
        members = [
            {"entity_id": "e:react", "role": "subject"},
            {"entity_id": "e:hooks", "role": "object"},
        ]
        hyperedge_data = make_hyperedge(
            id="h:new",
            description="React provides Hooks",
            members=members,
            attributes={"strength": 0.9},
        )
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/hyperedges",
            json=hyperedge_data,
        )

        tool = HyperedgeCrudTool(client)
        result = tool.run(
            action="create",
            description="React provides Hooks",
            participants=members,
            attributes={"strength": 0.9},
        )

        assert result.success is True
        assert result.data["attributes"] == {"strength": 0.9}

    def test_create_hyperedge_missing_required_fields(self, client: HyperX):
        """Test create returns error when required fields are missing."""
        tool = HyperedgeCrudTool(client)

        # Missing description
        result = tool.run(
            action="create",
            participants=[{"entity_id": "e:test", "role": "subject"}],
        )
        assert result.success is False
        assert "description" in result.explanation.lower()

        # Missing participants
        result = tool.run(action="create", description="Test relationship")
        assert result.success is False
        assert "participant" in result.explanation.lower()

    def test_create_hyperedge_quality_signals(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test create returns appropriate quality signals."""
        members = [{"entity_id": "e:test", "role": "subject"}]
        hyperedge_data = make_hyperedge(id="h:new", description="Test", members=members)
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/hyperedges",
            json=hyperedge_data,
        )

        tool = HyperedgeCrudTool(client)
        result = tool.run(action="create", description="Test", participants=members)

        assert isinstance(result.quality, QualitySignals)
        assert result.quality.should_retrieve_more is False


class TestHyperedgeCrudToolUpdateAction:
    """Tests for HyperedgeCrudTool update action."""

    def test_update_hyperedge(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test updating a hyperedge."""
        hyperedge_data = make_hyperedge(
            id="h:123",
            description="Updated description",
        )
        httpx_mock.add_response(
            method="PUT",
            url=f"{TEST_BASE_URL}/v1/hyperedges/h:123",
            json=hyperedge_data,
        )

        tool = HyperedgeCrudTool(client)
        result = tool.run(
            action="update",
            hyperedge_id="h:123",
            description="Updated description",
        )

        assert result.success is True
        assert result.data["description"] == "Updated description"

    def test_update_hyperedge_with_members(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test updating hyperedge members."""
        new_members = [
            {"entity_id": "e:new1", "role": "subject"},
            {"entity_id": "e:new2", "role": "object"},
        ]
        hyperedge_data = make_hyperedge(id="h:123", members=new_members)
        httpx_mock.add_response(
            method="PUT",
            url=f"{TEST_BASE_URL}/v1/hyperedges/h:123",
            json=hyperedge_data,
        )

        tool = HyperedgeCrudTool(client)
        result = tool.run(action="update", hyperedge_id="h:123", participants=new_members)

        assert result.success is True
        assert len(result.data["members"]) == 2

    def test_update_hyperedge_missing_hyperedge_id(self, client: HyperX):
        """Test update returns error when hyperedge_id is missing."""
        tool = HyperedgeCrudTool(client)
        result = tool.run(action="update", description="New description")

        assert result.success is False
        assert "hyperedge_id" in result.explanation.lower()


class TestHyperedgeCrudToolDeprecateAction:
    """Tests for HyperedgeCrudTool deprecate action."""

    def test_deprecate_hyperedge(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test deprecating a hyperedge."""
        hyperedge_data = make_hyperedge(id="h:123")
        hyperedge_data["state"] = "deprecated"
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/hyperedges/h:123/deprecate",
            json=hyperedge_data,
        )

        tool = HyperedgeCrudTool(client)
        result = tool.run(
            action="deprecate",
            hyperedge_id="h:123",
            reason="No longer accurate",
        )

        assert result.success is True
        assert "deprecated" in result.explanation.lower()

    def test_deprecate_hyperedge_missing_hyperedge_id(self, client: HyperX):
        """Test deprecate returns error when hyperedge_id is missing."""
        tool = HyperedgeCrudTool(client)
        result = tool.run(action="deprecate", reason="Test reason")

        assert result.success is False
        assert "hyperedge_id" in result.explanation.lower()

    def test_deprecate_hyperedge_missing_reason(self, client: HyperX):
        """Test deprecate returns error when reason is missing."""
        tool = HyperedgeCrudTool(client)
        result = tool.run(action="deprecate", hyperedge_id="h:123")

        assert result.success is False
        assert "reason" in result.explanation.lower()


class TestHyperedgeCrudToolDeleteAction:
    """Tests for HyperedgeCrudTool delete action."""

    def test_delete_hyperedge(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test deleting a hyperedge."""
        httpx_mock.add_response(
            method="DELETE",
            url=f"{TEST_BASE_URL}/v1/hyperedges/h:123",
            status_code=204,
        )

        tool = HyperedgeCrudTool(client)
        result = tool.run(action="delete", hyperedge_id="h:123")

        assert result.success is True
        assert "deleted" in result.explanation.lower()

    def test_delete_hyperedge_missing_hyperedge_id(self, client: HyperX):
        """Test delete returns error when hyperedge_id is missing."""
        tool = HyperedgeCrudTool(client)
        result = tool.run(action="delete")

        assert result.success is False
        assert "hyperedge_id" in result.explanation.lower()


class TestHyperedgeCrudToolInvalidAction:
    """Tests for HyperedgeCrudTool with invalid actions."""

    def test_invalid_action(self, client: HyperX):
        """Test invalid action returns error."""
        tool = HyperedgeCrudTool(client)
        result = tool.run(action="invalid_action")

        assert result.success is False
        assert "action" in result.explanation.lower()
        assert "invalid" in result.explanation.lower()

    def test_missing_action(self, client: HyperX):
        """Test missing action returns error."""
        tool = HyperedgeCrudTool(client)
        result = tool.run(description="Test")

        assert result.success is False
        assert "action" in result.explanation.lower()


class TestHyperedgeCrudToolOpenAISchema:
    """Tests for HyperedgeCrudTool OpenAI schema generation."""

    def test_to_openai_schema_structure(self, client: HyperX):
        """Test to_openai_schema() returns valid OpenAI function schema."""
        tool = HyperedgeCrudTool(client)
        schema = tool.to_openai_schema()

        # Required top-level structure
        assert schema["type"] == "function"
        assert "function" in schema

        func = schema["function"]
        assert func["name"] == "hyperx_hyperedge"
        assert "description" in func
        assert "parameters" in func

        # Parameters structure
        params = func["parameters"]
        assert params["type"] == "object"
        assert "properties" in params
        assert "required" in params

    def test_schema_has_action_as_required(self, client: HyperX):
        """Test schema has action as required parameter."""
        tool = HyperedgeCrudTool(client)
        schema = tool.to_openai_schema()

        params = schema["function"]["parameters"]
        assert "action" in params["required"]
        assert "action" in params["properties"]

    def test_schema_action_has_enum(self, client: HyperX):
        """Test action parameter has enum values."""
        tool = HyperedgeCrudTool(client)
        schema = tool.to_openai_schema()

        action_prop = schema["function"]["parameters"]["properties"]["action"]
        assert "enum" in action_prop
        assert set(action_prop["enum"]) == {"create", "update", "deprecate", "delete"}

    def test_schema_has_hyperedge_fields(self, client: HyperX):
        """Test schema has hyperedge field parameters."""
        tool = HyperedgeCrudTool(client)
        schema = tool.to_openai_schema()

        props = schema["function"]["parameters"]["properties"]
        assert "description" in props
        assert "hyperedge_id" in props
        assert "participants" in props
        assert "attributes" in props
        assert "reason" in props


class TestHyperedgeCrudToolAsync:
    """Tests for HyperedgeCrudTool async arun() method."""

    @pytest.mark.asyncio
    async def test_arun_create(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test arun() create action."""
        members = [{"entity_id": "e:test", "role": "subject"}]
        hyperedge_data = make_hyperedge(id="h:new", description="Test", members=members)
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/hyperedges",
            json=hyperedge_data,
        )

        tool = HyperedgeCrudTool(client)
        result = await tool.arun(
            action="create",
            description="Test",
            participants=members,
        )

        assert isinstance(result, ToolResult)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_arun_update(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test arun() update action."""
        hyperedge_data = make_hyperedge(id="h:123", description="Updated")
        httpx_mock.add_response(
            method="PUT",
            url=f"{TEST_BASE_URL}/v1/hyperedges/h:123",
            json=hyperedge_data,
        )

        tool = HyperedgeCrudTool(client)
        result = await tool.arun(
            action="update",
            hyperedge_id="h:123",
            description="Updated",
        )

        assert result.success is True

    @pytest.mark.asyncio
    async def test_arun_deprecate(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test arun() deprecate action."""
        hyperedge_data = make_hyperedge(id="h:123")
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/hyperedges/h:123/deprecate",
            json=hyperedge_data,
        )

        tool = HyperedgeCrudTool(client)
        result = await tool.arun(
            action="deprecate",
            hyperedge_id="h:123",
            reason="No longer valid",
        )

        assert result.success is True

    @pytest.mark.asyncio
    async def test_arun_delete(self, client: HyperX, httpx_mock: HTTPXMock):
        """Test arun() delete action."""
        httpx_mock.add_response(
            method="DELETE",
            url=f"{TEST_BASE_URL}/v1/hyperedges/h:123",
            status_code=204,
        )

        tool = HyperedgeCrudTool(client)
        result = await tool.arun(action="delete", hyperedge_id="h:123")

        assert result.success is True


class TestHyperedgeCrudToolErrorHandling:
    """Tests for HyperedgeCrudTool error handling."""

    def test_api_error_returns_failed_tool_result(
        self, client: HyperX, httpx_mock: HTTPXMock
    ):
        """Test API error returns failed ToolResult."""
        httpx_mock.add_response(
            method="POST",
            url=f"{TEST_BASE_URL}/v1/hyperedges",
            status_code=500,
            json={"error": "Internal server error"},
        )

        tool = HyperedgeCrudTool(client)
        result = tool.run(
            action="create",
            description="Test",
            participants=[{"entity_id": "e:test", "role": "subject"}],
        )

        assert result.success is False
        assert "failed" in result.explanation.lower()

    def test_network_error_returns_failed_tool_result(
        self, client: HyperX, httpx_mock: HTTPXMock
    ):
        """Test network error returns failed ToolResult."""
        import httpx

        httpx_mock.add_exception(httpx.ConnectError("Connection refused"))

        tool = HyperedgeCrudTool(client)
        result = tool.run(
            action="create",
            description="Test",
            participants=[{"entity_id": "e:test", "role": "subject"}],
        )

        assert result.success is False
        assert "failed" in result.explanation.lower()


# =============================================================================
# Module Export Tests
# =============================================================================


class TestCrudToolExports:
    """Tests for module exports."""

    def test_entitycrudtool_importable_from_agents(self):
        """Test EntityCrudTool is importable from hyperx.agents."""
        from hyperx.agents import EntityCrudTool

        assert EntityCrudTool is not None

    def test_hyperedgecrudtool_importable_from_agents(self):
        """Test HyperedgeCrudTool is importable from hyperx.agents."""
        from hyperx.agents import HyperedgeCrudTool

        assert HyperedgeCrudTool is not None

    def test_entitycrudtool_importable_from_agents_tools(self):
        """Test EntityCrudTool is importable from hyperx.agents.tools."""
        from hyperx.agents.tools import EntityCrudTool

        assert EntityCrudTool is not None

    def test_hyperedgecrudtool_importable_from_agents_tools(self):
        """Test HyperedgeCrudTool is importable from hyperx.agents.tools."""
        from hyperx.agents.tools import HyperedgeCrudTool

        assert HyperedgeCrudTool is not None

    def test_entitycrudtool_in_agents_all(self):
        """Test EntityCrudTool is in hyperx.agents.__all__."""
        from hyperx import agents

        assert "EntityCrudTool" in agents.__all__

    def test_hyperedgecrudtool_in_agents_all(self):
        """Test HyperedgeCrudTool is in hyperx.agents.__all__."""
        from hyperx import agents

        assert "HyperedgeCrudTool" in agents.__all__
