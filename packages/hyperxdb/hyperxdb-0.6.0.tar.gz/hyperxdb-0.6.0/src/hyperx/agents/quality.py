"""Quality analyzer for generating self-correction signals.

This module provides the QualityAnalyzer class which analyzes retrieval
results and generates quality signals to help agents decide whether to
retrieve more information or refine their queries.
"""

from __future__ import annotations

import re
from typing import Any

from hyperx.agents.base import QualitySignals


class QualityAnalyzer:
    """Analyzer for generating self-correction signals from retrieval results.

    QualityAnalyzer examines retrieval results and computes various quality
    metrics to help agents make informed decisions about whether to retrieve
    more data, refine queries, or proceed with current results.

    Attributes:
        confidence_threshold: Minimum confidence score before suggesting more retrieval.
        coverage_threshold: Minimum coverage score before suggesting more retrieval.

    Example:
        >>> analyzer = QualityAnalyzer(confidence_threshold=0.6, coverage_threshold=0.5)
        >>> results = [{"name": "User entity", "description": "A user record"}]
        >>> scores = [0.85]
        >>> signals = analyzer.analyze("find user", results, scores)
        >>> signals.confidence
        0.85
        >>> signals.should_retrieve_more
        False
    """

    def __init__(
        self,
        confidence_threshold: float = 0.6,
        coverage_threshold: float = 0.5,
    ) -> None:
        """Initialize the QualityAnalyzer.

        Args:
            confidence_threshold: Minimum confidence score (0.0-1.0) before
                suggesting more retrieval. Defaults to 0.6.
            coverage_threshold: Minimum coverage score (0.0-1.0) before
                suggesting more retrieval. Defaults to 0.5.
        """
        self.confidence_threshold = confidence_threshold
        self.coverage_threshold = coverage_threshold

    def analyze(
        self,
        query: str,
        results: list[dict[str, Any]],
        scores: list[float],
        *,
        referenced_ids: list[str] | None = None,
        fetched_ids: list[str] | None = None,
    ) -> QualitySignals:
        """Analyze retrieval results and generate quality signals.

        Examines the query, results, and scores to compute confidence,
        coverage, diversity, and other quality metrics that help agents
        decide on next actions.

        Args:
            query: The original search query.
            results: List of result dictionaries, each containing at least
                'name' and optionally 'description' and 'entity_type' fields.
            scores: List of relevance scores corresponding to each result.
            referenced_ids: Optional list of entity IDs referenced in the context.
            fetched_ids: Optional list of entity IDs that have been fetched.

        Returns:
            QualitySignals containing all computed quality metrics.
        """
        referenced_ids = referenced_ids or []
        fetched_ids = fetched_ids or []

        # Compute confidence as average of scores
        confidence = self._compute_confidence(scores)

        # Compute coverage based on query term matching
        coverage = self._compute_coverage(query, results)

        # Compute diversity based on unique entity types
        diversity = self._compute_diversity(results)

        # Determine if more retrieval is needed
        should_retrieve_more = (
            confidence < self.confidence_threshold
            or coverage < self.coverage_threshold
        )

        # Generate suggested refinements for low scores
        suggested_refinements = self._generate_refinements(scores)

        # Generate alternative queries from entity names
        alternative_queries = self._generate_alternative_queries(query, results)

        # Identify missing context (referenced but not fetched)
        missing_context_hints = self._compute_missing_context(
            referenced_ids, fetched_ids
        )

        return QualitySignals(
            confidence=confidence,
            relevance_scores=list(scores),
            coverage=coverage,
            diversity=diversity,
            should_retrieve_more=should_retrieve_more,
            suggested_refinements=suggested_refinements,
            alternative_queries=alternative_queries,
            missing_context_hints=missing_context_hints,
        )

    def _compute_confidence(self, scores: list[float]) -> float:
        """Compute confidence as average of scores.

        Args:
            scores: List of relevance scores.

        Returns:
            Average score, or 0.0 if empty.
        """
        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    def _compute_coverage(
        self, query: str, results: list[dict[str, Any]]
    ) -> float:
        """Compute coverage based on query term matching.

        Calculates what fraction of query terms appear in the result
        names and descriptions.

        Args:
            query: The search query.
            results: List of result dictionaries.

        Returns:
            Coverage score from 0.0 to 1.0.
        """
        if not query or not results:
            return 0.0

        # Extract query terms (lowercase, alphanumeric only)
        query_terms = set(
            term.lower()
            for term in re.findall(r"\b\w+\b", query)
            if len(term) > 1  # Skip single-char terms
        )

        if not query_terms:
            return 0.0

        # Collect all text from results
        result_text = ""
        for result in results:
            name = result.get("name", "")
            description = result.get("description", "")
            result_text += f" {name} {description}"

        result_text_lower = result_text.lower()

        # Count matching terms
        matching_terms = sum(
            1 for term in query_terms if term in result_text_lower
        )

        return matching_terms / len(query_terms)

    def _compute_diversity(self, results: list[dict[str, Any]]) -> float:
        """Compute diversity based on unique entity types.

        Args:
            results: List of result dictionaries.

        Returns:
            Diversity score from 0.0 to 1.0.
        """
        if not results:
            return 0.0

        entity_types = set()
        for result in results:
            entity_type = result.get("entity_type")
            if entity_type:
                entity_types.add(entity_type)

        # If no entity types found, assume all results are same type
        if not entity_types:
            return 1.0 / len(results) if len(results) > 1 else 1.0

        return len(entity_types) / len(results)

    def _generate_refinements(self, scores: list[float]) -> list[str]:
        """Generate suggested refinements for low-scoring results.

        Args:
            scores: List of relevance scores.

        Returns:
            List of suggested refinement strings.
        """
        if not scores:
            return []

        avg_score = sum(scores) / len(scores)

        refinements = []
        if avg_score < 0.5:
            refinements.append("Try: more specific terms")

        return refinements

    def _generate_alternative_queries(
        self, query: str, results: list[dict[str, Any]]
    ) -> list[str]:
        """Generate alternative queries by combining query with entity names.

        Args:
            query: The original search query.
            results: List of result dictionaries.

        Returns:
            List of alternative query strings.
        """
        if not results:
            return []

        alternative_queries = []
        # Use top results (up to 3) to generate alternatives
        for result in results[:3]:
            name = result.get("name", "")
            if name and name.lower() not in query.lower():
                alternative_query = f"{query} {name}"
                alternative_queries.append(alternative_query)

        return alternative_queries

    def _compute_missing_context(
        self, referenced_ids: list[str], fetched_ids: list[str]
    ) -> list[str]:
        """Identify IDs that are referenced but not fetched.

        Args:
            referenced_ids: List of entity IDs referenced in context.
            fetched_ids: List of entity IDs that have been fetched.

        Returns:
            List of missing entity IDs.
        """
        fetched_set = set(fetched_ids)
        return [
            ref_id
            for ref_id in referenced_ids
            if ref_id not in fetched_set
        ]
