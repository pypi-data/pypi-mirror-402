"""Tests for QualityAnalyzer self-correction signals."""

from __future__ import annotations

import pytest

from hyperx.agents.quality import QualityAnalyzer


class TestQualityAnalyzerEmpty:
    """Tests for empty result handling."""

    def test_empty_results_returns_low_confidence(self) -> None:
        """Empty results should return 0.0 confidence."""
        analyzer = QualityAnalyzer()
        signals = analyzer.analyze("test query", [], [])

        assert signals.confidence == 0.0

    def test_empty_results_should_retrieve_more(self) -> None:
        """Empty results should set should_retrieve_more to True."""
        analyzer = QualityAnalyzer()
        signals = analyzer.analyze("test query", [], [])

        assert signals.should_retrieve_more is True

    def test_empty_results_zero_coverage(self) -> None:
        """Empty results should have zero coverage."""
        analyzer = QualityAnalyzer()
        signals = analyzer.analyze("test query", [], [])

        assert signals.coverage == 0.0

    def test_empty_results_zero_diversity(self) -> None:
        """Empty results should have zero diversity."""
        analyzer = QualityAnalyzer()
        signals = analyzer.analyze("test query", [], [])

        assert signals.diversity == 0.0


class TestQualityAnalyzerConfidence:
    """Tests for confidence calculation."""

    def test_high_scores_return_high_confidence(self) -> None:
        """High scores should result in high confidence."""
        analyzer = QualityAnalyzer()
        results = [
            {"name": "Result 1", "description": "Description 1"},
            {"name": "Result 2", "description": "Description 2"},
        ]
        scores = [0.9, 0.85]

        signals = analyzer.analyze("test query", results, scores)

        assert signals.confidence == 0.875  # (0.9 + 0.85) / 2

    def test_high_scores_should_not_retrieve_more(self) -> None:
        """High scores should set should_retrieve_more to False."""
        analyzer = QualityAnalyzer()
        results = [
            {"name": "test query result", "description": "matches the query"},
        ]
        scores = [0.9]

        signals = analyzer.analyze("test query", results, scores)

        assert signals.should_retrieve_more is False

    def test_low_confidence_triggers_should_retrieve_more(self) -> None:
        """Low confidence should trigger should_retrieve_more."""
        analyzer = QualityAnalyzer(confidence_threshold=0.6)
        results = [{"name": "Result", "description": "Description"}]
        scores = [0.4]  # Below threshold

        signals = analyzer.analyze("test query", results, scores)

        assert signals.confidence == 0.4
        assert signals.should_retrieve_more is True

    def test_confidence_at_threshold_does_not_retrieve_more(self) -> None:
        """Confidence exactly at threshold should not retrieve more."""
        analyzer = QualityAnalyzer(confidence_threshold=0.6, coverage_threshold=0.0)
        results = [{"name": "test query", "description": "test query result"}]
        scores = [0.6]

        signals = analyzer.analyze("test query", results, scores)

        assert signals.confidence == 0.6
        assert signals.should_retrieve_more is False


class TestQualityAnalyzerRefinements:
    """Tests for suggested refinements generation."""

    def test_suggested_refinements_generated_for_low_scores(self) -> None:
        """Low average scores should generate refinement suggestions."""
        analyzer = QualityAnalyzer()
        results = [{"name": "Result", "description": "Description"}]
        scores = [0.3]  # Below 0.5

        signals = analyzer.analyze("test query", results, scores)

        assert len(signals.suggested_refinements) > 0
        assert "Try: more specific terms" in signals.suggested_refinements

    def test_no_refinements_for_high_scores(self) -> None:
        """High scores should not generate refinement suggestions."""
        analyzer = QualityAnalyzer()
        results = [{"name": "Result", "description": "Description"}]
        scores = [0.8]  # Above 0.5

        signals = analyzer.analyze("test query", results, scores)

        assert "Try: more specific terms" not in signals.suggested_refinements

    def test_no_refinements_for_empty_scores(self) -> None:
        """Empty scores should not generate refinement suggestions."""
        analyzer = QualityAnalyzer()
        signals = analyzer.analyze("test query", [], [])

        assert signals.suggested_refinements == []


class TestQualityAnalyzerAlternativeQueries:
    """Tests for alternative query generation."""

    def test_alternative_queries_from_entity_names(self) -> None:
        """Alternative queries should be generated from entity names."""
        analyzer = QualityAnalyzer()
        results = [
            {"name": "User", "description": "User entity"},
            {"name": "Account", "description": "Account entity"},
        ]
        scores = [0.7, 0.6]

        signals = analyzer.analyze("find", results, scores)

        assert len(signals.alternative_queries) >= 1
        assert any("User" in q for q in signals.alternative_queries)

    def test_alternative_queries_combine_with_original(self) -> None:
        """Alternative queries should combine original query with names."""
        analyzer = QualityAnalyzer()
        results = [{"name": "Customer", "description": "Customer record"}]
        scores = [0.7]

        signals = analyzer.analyze("find entity", results, scores)

        assert "find entity Customer" in signals.alternative_queries

    def test_no_alternative_queries_for_empty_results(self) -> None:
        """Empty results should not generate alternative queries."""
        analyzer = QualityAnalyzer()
        signals = analyzer.analyze("test query", [], [])

        assert signals.alternative_queries == []

    def test_no_duplicate_in_alternative_queries(self) -> None:
        """Entity names already in query should not be duplicated."""
        analyzer = QualityAnalyzer()
        results = [{"name": "user", "description": "User entity"}]
        scores = [0.7]

        signals = analyzer.analyze("find user", results, scores)

        # "user" is already in query, so no alternative should be generated
        assert not any("user" in q.lower().split()[-1] for q in signals.alternative_queries)


class TestQualityAnalyzerMissingContext:
    """Tests for missing context hints."""

    def test_missing_context_hints_identifies_unfetched_entities(self) -> None:
        """Missing context hints should identify unfetched referenced entities."""
        analyzer = QualityAnalyzer()
        results = [{"name": "Result", "description": "Description"}]
        scores = [0.7]
        referenced_ids = ["entity-1", "entity-2", "entity-3"]
        fetched_ids = ["entity-1"]

        signals = analyzer.analyze(
            "test query",
            results,
            scores,
            referenced_ids=referenced_ids,
            fetched_ids=fetched_ids,
        )

        assert "entity-2" in signals.missing_context_hints
        assert "entity-3" in signals.missing_context_hints
        assert "entity-1" not in signals.missing_context_hints

    def test_no_missing_context_when_all_fetched(self) -> None:
        """No missing context when all referenced entities are fetched."""
        analyzer = QualityAnalyzer()
        results = [{"name": "Result", "description": "Description"}]
        scores = [0.7]
        referenced_ids = ["entity-1", "entity-2"]
        fetched_ids = ["entity-1", "entity-2"]

        signals = analyzer.analyze(
            "test query",
            results,
            scores,
            referenced_ids=referenced_ids,
            fetched_ids=fetched_ids,
        )

        assert signals.missing_context_hints == []

    def test_missing_context_empty_when_no_references(self) -> None:
        """Missing context should be empty when no references provided."""
        analyzer = QualityAnalyzer()
        results = [{"name": "Result", "description": "Description"}]
        scores = [0.7]

        signals = analyzer.analyze("test query", results, scores)

        assert signals.missing_context_hints == []


class TestQualityAnalyzerCoverage:
    """Tests for coverage calculation."""

    def test_coverage_calculation_with_query_term_matching(self) -> None:
        """Coverage should reflect query term matching in results."""
        analyzer = QualityAnalyzer()
        results = [
            {"name": "user profile", "description": "Contains user data"},
        ]
        scores = [0.8]

        # Query "user data" - both terms should match
        signals = analyzer.analyze("user data", results, scores)

        assert signals.coverage == 1.0  # All terms match

    def test_partial_coverage_when_some_terms_match(self) -> None:
        """Coverage should be partial when only some terms match."""
        analyzer = QualityAnalyzer()
        results = [
            {"name": "user profile", "description": "Profile information"},
        ]
        scores = [0.8]

        # Query "user account" - only "user" matches
        signals = analyzer.analyze("user account", results, scores)

        assert signals.coverage == 0.5  # 1 of 2 terms match

    def test_zero_coverage_when_no_terms_match(self) -> None:
        """Coverage should be zero when no terms match."""
        analyzer = QualityAnalyzer()
        results = [
            {"name": "customer", "description": "Customer record"},
        ]
        scores = [0.8]

        # Query "product inventory" - no terms match
        signals = analyzer.analyze("product inventory", results, scores)

        assert signals.coverage == 0.0

    def test_low_coverage_triggers_should_retrieve_more(self) -> None:
        """Low coverage should trigger should_retrieve_more."""
        analyzer = QualityAnalyzer(confidence_threshold=0.0, coverage_threshold=0.5)
        results = [
            {"name": "xyz", "description": "Something unrelated"},
        ]
        scores = [0.9]  # High confidence

        # Query terms don't match results
        signals = analyzer.analyze("user account", results, scores)

        assert signals.coverage < 0.5
        assert signals.should_retrieve_more is True


class TestQualityAnalyzerDiversity:
    """Tests for diversity calculation."""

    def test_diversity_calculation_with_multiple_entity_types(self) -> None:
        """Diversity should reflect unique entity types."""
        analyzer = QualityAnalyzer()
        results = [
            {"name": "User 1", "entity_type": "User"},
            {"name": "Account 1", "entity_type": "Account"},
            {"name": "Product 1", "entity_type": "Product"},
        ]
        scores = [0.8, 0.7, 0.6]

        signals = analyzer.analyze("find entities", results, scores)

        assert signals.diversity == 1.0  # 3 types / 3 results

    def test_low_diversity_with_same_entity_types(self) -> None:
        """Diversity should be low when results have same entity type."""
        analyzer = QualityAnalyzer()
        results = [
            {"name": "User 1", "entity_type": "User"},
            {"name": "User 2", "entity_type": "User"},
            {"name": "User 3", "entity_type": "User"},
        ]
        scores = [0.8, 0.7, 0.6]

        signals = analyzer.analyze("find users", results, scores)

        # 1 unique type / 3 results = 0.333...
        assert abs(signals.diversity - (1 / 3)) < 0.001

    def test_diversity_with_mixed_entity_types(self) -> None:
        """Diversity should handle mixed entity types."""
        analyzer = QualityAnalyzer()
        results = [
            {"name": "User 1", "entity_type": "User"},
            {"name": "User 2", "entity_type": "User"},
            {"name": "Account 1", "entity_type": "Account"},
            {"name": "Product 1", "entity_type": "Product"},
        ]
        scores = [0.8, 0.7, 0.6, 0.5]

        signals = analyzer.analyze("find entities", results, scores)

        # 3 unique types / 4 results = 0.75
        assert signals.diversity == 0.75

    def test_diversity_with_no_entity_types(self) -> None:
        """Diversity calculation when no entity_type field is present."""
        analyzer = QualityAnalyzer()
        results = [
            {"name": "Result 1", "description": "Description 1"},
            {"name": "Result 2", "description": "Description 2"},
        ]
        scores = [0.8, 0.7]

        signals = analyzer.analyze("find stuff", results, scores)

        # No entity types means assume same type: 1/2 = 0.5
        assert signals.diversity == 0.5

    def test_diversity_single_result_no_entity_type(self) -> None:
        """Single result with no entity_type should have diversity 1.0."""
        analyzer = QualityAnalyzer()
        results = [{"name": "Result 1", "description": "Description 1"}]
        scores = [0.8]

        signals = analyzer.analyze("find", results, scores)

        assert signals.diversity == 1.0


class TestQualityAnalyzerThresholds:
    """Tests for custom threshold configuration."""

    def test_custom_confidence_threshold(self) -> None:
        """Custom confidence threshold should be respected."""
        analyzer = QualityAnalyzer(confidence_threshold=0.8, coverage_threshold=0.0)
        results = [{"name": "test query", "description": "matches query"}]
        scores = [0.7]  # Below 0.8

        signals = analyzer.analyze("test query", results, scores)

        assert signals.should_retrieve_more is True

    def test_custom_coverage_threshold(self) -> None:
        """Custom coverage threshold should be respected."""
        analyzer = QualityAnalyzer(confidence_threshold=0.0, coverage_threshold=0.8)
        results = [{"name": "user", "description": "user info"}]  # Only "user" matches
        scores = [0.9]

        # "user account" - only "user" matches = 50% coverage
        signals = analyzer.analyze("user account", results, scores)

        assert signals.coverage == 0.5
        assert signals.should_retrieve_more is True


class TestQualityAnalyzerRelevanceScores:
    """Tests for relevance_scores passthrough."""

    def test_relevance_scores_passed_through(self) -> None:
        """Relevance scores should be passed through to signals."""
        analyzer = QualityAnalyzer()
        results = [
            {"name": "Result 1"},
            {"name": "Result 2"},
            {"name": "Result 3"},
        ]
        scores = [0.9, 0.7, 0.5]

        signals = analyzer.analyze("query", results, scores)

        assert signals.relevance_scores == [0.9, 0.7, 0.5]

    def test_empty_relevance_scores(self) -> None:
        """Empty scores should result in empty relevance_scores."""
        analyzer = QualityAnalyzer()
        signals = analyzer.analyze("query", [], [])

        assert signals.relevance_scores == []
