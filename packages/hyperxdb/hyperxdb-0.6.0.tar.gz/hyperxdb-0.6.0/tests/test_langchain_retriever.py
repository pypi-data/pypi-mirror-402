"""Tests for LangChain integration."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from hyperx import Entity, Hyperedge, HyperedgeMember, PathResult, SearchResult
from hyperx.integrations.langchain import HyperXRetriever, HyperXRetrievalPipeline


@pytest.fixture
def mock_client():
    """Create a mock HyperX client."""
    client = MagicMock()
    now = datetime.now(timezone.utc)
    client.search.return_value = SearchResult(
        entities=[
            Entity(
                id="e:react",
                name="React",
                entity_type="technology",
                attributes={},
                created_at=now,
                updated_at=now,
            )
        ],
        hyperedges=[
            Hyperedge(
                id="h:1",
                description="React provides Hooks for state management",
                members=[
                    HyperedgeMember(entity_id="e:react", role="subject"),
                    HyperedgeMember(entity_id="e:hooks", role="object"),
                ],
                attributes={},
                created_at=now,
                updated_at=now,
            )
        ],
    )
    return client


def test_retriever_search_strategy(mock_client):
    """Test retriever with simple search strategy."""
    retriever = HyperXRetriever(client=mock_client, strategy="search", k=5)

    docs = retriever.invoke("React state management")

    assert len(docs) == 1
    assert "React provides Hooks" in docs[0].page_content
    assert docs[0].metadata["id"] == "h:1"
    mock_client.search.assert_called_once_with("React state management", limit=5)


def test_retriever_default_strategy(mock_client):
    """Test retriever defaults to search strategy."""
    retriever = HyperXRetriever(client=mock_client, k=10)

    docs = retriever.invoke("test query")

    assert len(docs) == 1
    mock_client.search.assert_called_once()


def test_retriever_document_metadata(mock_client):
    """Test that document metadata is properly populated."""
    retriever = HyperXRetriever(client=mock_client, strategy="search", k=5)

    docs = retriever.invoke("test")

    assert docs[0].metadata["id"] == "h:1"
    assert docs[0].metadata["source"] == "hyperx"
    assert docs[0].metadata["distance"] == 0
    assert "members" in docs[0].metadata


def test_retriever_invalid_strategy(mock_client):
    """Test that invalid strategy raises ValidationError at construction."""
    with pytest.raises(ValidationError, match="Input should be 'search' or 'graph'"):
        HyperXRetriever(client=mock_client, strategy="invalid", k=5)


@pytest.fixture
def mock_client_with_paths():
    """Create a mock HyperX client with path finding."""
    client = MagicMock()
    now = datetime.now(timezone.utc)

    # Initial search returns two entities and one hyperedge
    # (need at least 2 entities for path finding between them)
    client.search.return_value = SearchResult(
        entities=[
            Entity(
                id="e:react",
                name="React",
                entity_type="technology",
                attributes={},
                created_at=now,
                updated_at=now,
            ),
            Entity(
                id="e:hooks",
                name="Hooks",
                entity_type="feature",
                attributes={},
                created_at=now,
                updated_at=now,
            ),
        ],
        hyperedges=[
            Hyperedge(
                id="h:1",
                description="React provides Hooks",
                members=[
                    HyperedgeMember(entity_id="e:react", role="subject"),
                    HyperedgeMember(entity_id="e:hooks", role="object"),
                ],
                attributes={},
                created_at=now,
                updated_at=now,
            )
        ],
    )

    # Path finding returns paths with hyperedge IDs
    client.paths.find.return_value = [
        PathResult(
            hyperedges=["h:2"],
            bridges=[],
            cost=0.5,
        )
    ]

    # Mock hyperedges.get to return full hyperedge objects
    def get_hyperedge(hyperedge_id: str) -> Hyperedge:
        hyperedges = {
            "h:2": Hyperedge(
                id="h:2",
                description="React often pairs with Redux for state",
                members=[
                    HyperedgeMember(entity_id="e:react", role="subject"),
                    HyperedgeMember(entity_id="e:redux", role="object"),
                ],
                attributes={},
                created_at=now,
                updated_at=now,
            ),
        }
        return hyperedges.get(hyperedge_id)

    client.hyperedges.get.side_effect = get_hyperedge

    return client


def test_retriever_graph_strategy_expands(mock_client_with_paths):
    """Test that graph strategy expands search results via paths."""
    retriever = HyperXRetriever(
        client=mock_client_with_paths,
        strategy="graph",
        k=10,
        max_hops=2,
    )

    docs = retriever.invoke("React")

    # Should include both direct match and expanded results
    assert len(docs) >= 1
    descriptions = [d.page_content for d in docs]
    # Direct match from search
    assert any("Hooks" in d for d in descriptions)
    # Expanded from path finding
    assert any("Redux" in d for d in descriptions)
    # Verify path finding was called
    mock_client_with_paths.paths.find.assert_called()


def test_retriever_graph_strategy_deduplicates(mock_client_with_paths):
    """Test that graph strategy deduplicates hyperedges."""
    now = datetime.now(timezone.utc)

    # Make path finding return the same hyperedge ID as search
    mock_client_with_paths.paths.find.return_value = [
        PathResult(
            hyperedges=["h:1"],  # Same ID as search result
            bridges=[],
            cost=0.3,
        )
    ]

    # Mock hyperedges.get to return the same hyperedge
    mock_client_with_paths.hyperedges.get.return_value = Hyperedge(
        id="h:1",
        description="React provides Hooks",
        members=[
            HyperedgeMember(entity_id="e:react", role="subject"),
            HyperedgeMember(entity_id="e:hooks", role="object"),
        ],
        attributes={},
        created_at=now,
        updated_at=now,
    )

    retriever = HyperXRetriever(
        client=mock_client_with_paths,
        strategy="graph",
        k=10,
        max_hops=2,
    )

    docs = retriever.invoke("React")

    # Should not have duplicates
    ids = [d.metadata["id"] for d in docs]
    assert len(ids) == len(set(ids))


def test_retriever_empty_results():
    """Test retriever handles empty search results."""
    client = MagicMock()
    client.search.return_value = SearchResult(entities=[], hyperedges=[])

    retriever = HyperXRetriever(client=client, strategy="search", k=5)
    docs = retriever.invoke("nonexistent")

    assert docs == []


# =============================================================================
# HyperXRetrievalPipeline Tests
# =============================================================================


def test_pipeline_basic(mock_client):
    """Test basic pipeline without reranking."""
    pipeline = HyperXRetrievalPipeline(
        client=mock_client,
        vector_weight=0.7,
        text_weight=0.3,
        k=5,
    )

    docs = pipeline.invoke("React hooks")

    assert len(docs) >= 1
    assert docs[0].metadata["source"] == "hyperx"


def test_pipeline_with_reranker(mock_client):
    """Test pipeline with custom reranker."""
    def simple_reranker(query: str, docs: list) -> list:
        # Reverse order as simple reranking
        return list(reversed(docs))

    pipeline = HyperXRetrievalPipeline(
        client=mock_client,
        vector_weight=0.7,
        text_weight=0.3,
        k=5,
        reranker=simple_reranker,
    )

    docs = pipeline.invoke("React hooks")

    assert len(docs) >= 1


def test_pipeline_weight_validation():
    """Test that weights must sum to 1.0."""
    with pytest.raises(ValueError, match="must equal 1.0"):
        HyperXRetrievalPipeline(
            client=MagicMock(),
            vector_weight=0.5,
            text_weight=0.3,  # Sums to 0.8, not 1.0
            k=5,
        )


def test_pipeline_with_graph_expansion(mock_client_with_paths):
    """Test pipeline with graph expansion enabled."""
    pipeline = HyperXRetrievalPipeline(
        client=mock_client_with_paths,
        vector_weight=0.7,
        text_weight=0.3,
        expand_graph=True,
        max_hops=2,
        k=10,
    )

    docs = pipeline.invoke("React")

    # Should include expanded results
    assert len(docs) >= 1
