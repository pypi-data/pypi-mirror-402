"""Tests for agent base classes."""

import pytest
from typing import Any


class TestQualitySignals:
    """Tests for QualitySignals dataclass."""

    def test_creation_with_all_fields(self):
        """Test QualitySignals can be created with all fields."""
        from hyperx.agents import QualitySignals

        signals = QualitySignals(
            confidence=0.85,
            relevance_scores=[0.9, 0.8, 0.75],
            coverage=0.7,
            diversity=0.6,
            should_retrieve_more=False,
            suggested_refinements=["add date filter", "narrow scope"],
            alternative_queries=["search by author", "search by topic"],
            missing_context_hints=["document version", "publication date"],
        )

        assert signals.confidence == 0.85
        assert signals.relevance_scores == [0.9, 0.8, 0.75]
        assert signals.coverage == 0.7
        assert signals.diversity == 0.6
        assert signals.should_retrieve_more is False
        assert signals.suggested_refinements == ["add date filter", "narrow scope"]
        assert signals.alternative_queries == ["search by author", "search by topic"]
        assert signals.missing_context_hints == ["document version", "publication date"]

    def test_default_classmethod(self):
        """Test QualitySignals.default() returns low-confidence defaults."""
        from hyperx.agents import QualitySignals

        signals = QualitySignals.default()

        # Low confidence defaults
        assert signals.confidence == 0.0
        assert signals.relevance_scores == []
        assert signals.coverage == 0.0
        assert signals.diversity == 0.0
        assert signals.should_retrieve_more is True  # Should suggest getting more data
        assert signals.suggested_refinements == []
        assert signals.alternative_queries == []
        assert signals.missing_context_hints == []

    def test_confidence_bounds(self):
        """Test confidence is within 0.0-1.0 range."""
        from hyperx.agents import QualitySignals

        # Valid confidence values
        low = QualitySignals(
            confidence=0.0,
            relevance_scores=[],
            coverage=0.0,
            diversity=0.0,
            should_retrieve_more=True,
            suggested_refinements=[],
            alternative_queries=[],
            missing_context_hints=[],
        )
        high = QualitySignals(
            confidence=1.0,
            relevance_scores=[],
            coverage=1.0,
            diversity=1.0,
            should_retrieve_more=False,
            suggested_refinements=[],
            alternative_queries=[],
            missing_context_hints=[],
        )

        assert low.confidence == 0.0
        assert high.confidence == 1.0


class TestToolResult:
    """Tests for ToolResult dataclass."""

    def test_success_result(self):
        """Test ToolResult for successful operation."""
        from hyperx.agents import QualitySignals, ToolResult

        signals = QualitySignals(
            confidence=0.95,
            relevance_scores=[0.98, 0.92],
            coverage=0.85,
            diversity=0.7,
            should_retrieve_more=False,
            suggested_refinements=[],
            alternative_queries=[],
            missing_context_hints=[],
        )

        result = ToolResult(
            success=True,
            data={"entities": ["e1", "e2"], "count": 2},
            quality=signals,
            explanation="Found 2 highly relevant entities.",
        )

        assert result.success is True
        assert result.data == {"entities": ["e1", "e2"], "count": 2}
        assert result.quality.confidence == 0.95
        assert result.explanation == "Found 2 highly relevant entities."

    def test_failure_result(self):
        """Test ToolResult for failed operation."""
        from hyperx.agents import QualitySignals, ToolResult

        signals = QualitySignals.default()

        result = ToolResult(
            success=False,
            data=None,
            quality=signals,
            explanation="Query returned no results. Try broadening search terms.",
        )

        assert result.success is False
        assert result.data is None
        assert result.quality.confidence == 0.0
        assert result.quality.should_retrieve_more is True
        assert "no results" in result.explanation

    def test_data_can_be_any_type(self):
        """Test ToolResult data field accepts any type."""
        from hyperx.agents import QualitySignals, ToolResult

        signals = QualitySignals.default()

        # Test with list
        result_list = ToolResult(
            success=True,
            data=["item1", "item2"],
            quality=signals,
            explanation="List data",
        )
        assert result_list.data == ["item1", "item2"]

        # Test with string
        result_str = ToolResult(
            success=True,
            data="plain text response",
            quality=signals,
            explanation="String data",
        )
        assert result_str.data == "plain text response"

        # Test with complex nested structure
        result_complex = ToolResult(
            success=True,
            data={
                "paths": [
                    {"from": "e1", "to": "e2", "hops": 2},
                    {"from": "e1", "to": "e3", "hops": 3},
                ],
                "metadata": {"query_time_ms": 42},
            },
            quality=signals,
            explanation="Complex data",
        )
        assert result_complex.data["paths"][0]["hops"] == 2


class TestToolError:
    """Tests for ToolError exception."""

    def test_error_creation(self):
        """Test ToolError can be created with required fields."""
        from hyperx.agents import ToolError

        error = ToolError(
            tool_name="search_entities",
            message="Connection timeout while querying database",
        )

        assert error.tool_name == "search_entities"
        assert error.message == "Connection timeout while querying database"
        assert error.recoverable is True  # Default

    def test_error_with_recoverable_false(self):
        """Test ToolError with recoverable=False."""
        from hyperx.agents import ToolError

        error = ToolError(
            tool_name="delete_entity",
            message="Entity is referenced by other hyperedges",
            recoverable=False,
        )

        assert error.tool_name == "delete_entity"
        assert error.recoverable is False

    def test_error_can_be_raised(self):
        """Test ToolError can be raised and caught."""
        from hyperx.agents import ToolError

        with pytest.raises(ToolError) as exc_info:
            raise ToolError(
                tool_name="traverse_path",
                message="Maximum depth exceeded",
                recoverable=True,
            )

        assert exc_info.value.tool_name == "traverse_path"
        assert "Maximum depth exceeded" in str(exc_info.value)

    def test_error_is_exception(self):
        """Test ToolError inherits from Exception."""
        from hyperx.agents import ToolError

        error = ToolError(tool_name="test", message="test error")
        assert isinstance(error, Exception)


class TestBaseTool:
    """Tests for BaseTool Protocol."""

    def test_protocol_is_runtime_checkable(self):
        """Test BaseTool Protocol is runtime_checkable."""
        from typing import runtime_checkable
        from hyperx.agents import BaseTool

        # Protocol should be importable and work with isinstance
        # (though we're just checking it's defined correctly)
        assert hasattr(BaseTool, "__protocol_attrs__") or hasattr(
            BaseTool, "_is_protocol"
        )

    def test_implementing_class_matches_protocol(self):
        """Test that a class implementing all methods matches BaseTool."""
        from hyperx.agents import BaseTool, QualitySignals, ToolResult

        class MockTool:
            """A mock tool that implements BaseTool interface."""

            @property
            def name(self) -> str:
                return "mock_tool"

            @property
            def description(self) -> str:
                return "A mock tool for testing"

            def run(self, **kwargs) -> ToolResult:
                return ToolResult(
                    success=True,
                    data=kwargs,
                    quality=QualitySignals.default(),
                    explanation="Mock run",
                )

            async def arun(self, **kwargs) -> ToolResult:
                return ToolResult(
                    success=True,
                    data=kwargs,
                    quality=QualitySignals.default(),
                    explanation="Mock async run",
                )

            def to_openai_schema(self) -> dict:
                return {
                    "type": "function",
                    "function": {
                        "name": self.name,
                        "description": self.description,
                        "parameters": {"type": "object", "properties": {}},
                    },
                }

        tool = MockTool()

        # Verify it passes isinstance check
        assert isinstance(tool, BaseTool)

    def test_non_implementing_class_fails_protocol(self):
        """Test that a class missing methods does not match BaseTool."""
        from hyperx.agents import BaseTool

        class IncompleteTool:
            """A tool missing required methods."""

            @property
            def name(self) -> str:
                return "incomplete"

            # Missing: description, run, arun, to_openai_schema

        tool = IncompleteTool()

        # Should fail isinstance check
        assert not isinstance(tool, BaseTool)


class TestExports:
    """Tests for module exports."""

    def test_all_classes_importable_from_agents(self):
        """Test all required classes are importable from hyperx.agents."""
        from hyperx.agents import BaseTool, QualitySignals, ToolError, ToolResult

        assert QualitySignals is not None
        assert ToolResult is not None
        assert ToolError is not None
        assert BaseTool is not None

    def test_classes_in_all(self):
        """Test all required classes are in __all__."""
        from hyperx import agents

        expected = ["QualitySignals", "ToolResult", "ToolError", "BaseTool"]
        for name in expected:
            assert name in agents.__all__, f"{name} not in agents.__all__"
