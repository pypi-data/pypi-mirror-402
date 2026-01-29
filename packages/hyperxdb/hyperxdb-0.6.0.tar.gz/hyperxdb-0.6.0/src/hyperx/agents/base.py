"""Base classes for HyperX agent tools.

This module provides the foundational classes for building agentic RAG
tools that integrate with LLM frameworks like OpenAI, LangChain, and others.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class QualitySignals:
    """Quality signals for agentic RAG retrieval results.

    Provides detailed feedback about retrieval quality to help agents
    decide whether to retrieve more information or refine their queries.

    Attributes:
        confidence: Overall confidence score from 0.0 to 1.0.
        relevance_scores: Individual relevance scores for each result.
        coverage: Estimated coverage of the query topic (0.0-1.0).
        diversity: Diversity of the result set (0.0-1.0).
        should_retrieve_more: Whether the agent should retrieve more data.
        suggested_refinements: Suggested query refinements.
        alternative_queries: Alternative queries to try.
        missing_context_hints: Hints about missing context.
    """

    confidence: float
    relevance_scores: list[float]
    coverage: float
    diversity: float
    should_retrieve_more: bool
    suggested_refinements: list[str]
    alternative_queries: list[str]
    missing_context_hints: list[str]

    @classmethod
    def default(cls) -> QualitySignals:
        """Create a QualitySignals instance with low-confidence defaults.

        Returns a QualitySignals with minimal confidence values,
        suggesting that more retrieval may be needed.

        Returns:
            QualitySignals with default low-confidence values.
        """
        return cls(
            confidence=0.0,
            relevance_scores=[],
            coverage=0.0,
            diversity=0.0,
            should_retrieve_more=True,
            suggested_refinements=[],
            alternative_queries=[],
            missing_context_hints=[],
        )


@dataclass
class ToolResult:
    """Result from a tool execution.

    Encapsulates the outcome of a tool execution including the data,
    quality signals, and a human-readable explanation.

    Attributes:
        success: Whether the tool execution succeeded.
        data: The result data (can be any type).
        quality: Quality signals for the result.
        explanation: Human-readable explanation of the result.
    """

    success: bool
    data: Any
    quality: QualitySignals
    explanation: str


class ToolError(Exception):
    """Exception raised when a tool execution fails.

    Provides structured error information for tool failures,
    including whether the error is recoverable.

    Attributes:
        tool_name: Name of the tool that failed.
        message: Error message describing the failure.
        recoverable: Whether the error can be recovered from.
    """

    def __init__(
        self,
        tool_name: str,
        message: str,
        recoverable: bool = True,
    ) -> None:
        """Initialize ToolError.

        Args:
            tool_name: Name of the tool that failed.
            message: Error message describing the failure.
            recoverable: Whether the error can be recovered from.
        """
        super().__init__(f"{tool_name}: {message}")
        self.tool_name = tool_name
        self.message = message
        self.recoverable = recoverable


@runtime_checkable
class BaseTool(Protocol):
    """Protocol defining the interface for HyperX agent tools.

    Tools implementing this protocol can be used with LLM frameworks
    that support function calling (OpenAI, Anthropic, etc.).

    All implementations must provide:
        - name: Unique identifier for the tool
        - description: Human-readable description
        - run(): Synchronous execution method
        - arun(): Asynchronous execution method
        - to_openai_schema(): OpenAI function schema export
    """

    @property
    def name(self) -> str:
        """Unique identifier for the tool."""
        ...

    @property
    def description(self) -> str:
        """Human-readable description of what the tool does."""
        ...

    def run(self, **kwargs: Any) -> ToolResult:
        """Execute the tool synchronously.

        Args:
            **kwargs: Tool-specific arguments.

        Returns:
            ToolResult containing the execution outcome.

        Raises:
            ToolError: If the tool execution fails.
        """
        ...

    async def arun(self, **kwargs: Any) -> ToolResult:
        """Execute the tool asynchronously.

        Args:
            **kwargs: Tool-specific arguments.

        Returns:
            ToolResult containing the execution outcome.

        Raises:
            ToolError: If the tool execution fails.
        """
        ...

    def to_openai_schema(self) -> dict[str, Any]:
        """Export tool definition as OpenAI function schema.

        Returns:
            Dictionary conforming to OpenAI's function calling schema.
        """
        ...
