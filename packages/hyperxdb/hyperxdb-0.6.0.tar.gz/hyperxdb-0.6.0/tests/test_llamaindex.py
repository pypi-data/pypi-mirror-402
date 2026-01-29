"""Tests for LlamaIndex integration."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

# Skip if llama-index not installed
pytest.importorskip("llama_index")

from hyperx import Entity, Hyperedge, HyperedgeMember, SearchResult
from hyperx.integrations.llamaindex import HyperXKnowledgeGraph, HyperXRetriever


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


def test_knowledge_graph_init(mock_client):
    """Test HyperXKnowledgeGraph initialization."""
    kg = HyperXKnowledgeGraph(
        client=mock_client,
        include_embeddings=True,
    )

    assert kg.client == mock_client
    assert kg.include_embeddings is True


def test_knowledge_graph_as_retriever(mock_client):
    """Test using HyperXKnowledgeGraph as a retriever."""
    kg = HyperXKnowledgeGraph(client=mock_client)
    retriever = kg.as_retriever(similarity_top_k=5)

    from llama_index.core.schema import QueryBundle
    query = QueryBundle(query_str="React hooks")
    nodes = retriever._retrieve(query)

    assert len(nodes) >= 1
    assert "React provides Hooks" in nodes[0].node.text
    mock_client.search.assert_called_once()


def test_retriever_node_metadata(mock_client):
    """Test that node metadata is properly populated."""
    kg = HyperXKnowledgeGraph(client=mock_client)
    retriever = kg.as_retriever(similarity_top_k=5)

    from llama_index.core.schema import QueryBundle
    query = QueryBundle(query_str="test")
    nodes = retriever._retrieve(query)

    assert nodes[0].node.metadata["id"] == "h:1"
    assert nodes[0].node.metadata["source"] == "hyperx"
    assert "members" in nodes[0].node.metadata


def test_retriever_modes(mock_client):
    """Test different retriever modes."""
    kg = HyperXKnowledgeGraph(client=mock_client)

    # Hybrid mode (default)
    retriever = kg.as_retriever(retriever_mode="hybrid")
    assert retriever._retriever_mode == "hybrid"

    # Keyword mode
    retriever = kg.as_retriever(retriever_mode="keyword")
    assert retriever._retriever_mode == "keyword"


def test_retriever_keyword_mode(mock_client):
    """Test retriever with keyword mode uses text search."""
    # Set up mock for text search
    now = datetime.now(timezone.utc)
    mock_client.search.text.return_value = SearchResult(
        entities=[],
        hyperedges=[
            Hyperedge(
                id="h:text",
                description="Text search result",
                members=[
                    HyperedgeMember(entity_id="e:test", role="subject"),
                ],
                attributes={},
                created_at=now,
                updated_at=now,
            )
        ],
    )

    kg = HyperXKnowledgeGraph(client=mock_client)
    retriever = kg.as_retriever(similarity_top_k=5, retriever_mode="keyword")

    from llama_index.core.schema import QueryBundle
    query = QueryBundle(query_str="test query")
    nodes = retriever._retrieve(query)

    assert len(nodes) == 1
    assert nodes[0].node.text == "Text search result"
    mock_client.search.text.assert_called_once_with("test query", limit=5)


def test_retriever_empty_results():
    """Test retriever handles empty search results."""
    client = MagicMock()
    client.search.return_value = SearchResult(entities=[], hyperedges=[])

    kg = HyperXKnowledgeGraph(client=client)
    retriever = kg.as_retriever(similarity_top_k=5)

    from llama_index.core.schema import QueryBundle
    query = QueryBundle(query_str="nonexistent")
    nodes = retriever._retrieve(query)

    assert nodes == []


def test_retriever_score_calculation(mock_client):
    """Test that scores are calculated correctly."""
    now = datetime.now(timezone.utc)
    mock_client.search.return_value = SearchResult(
        entities=[],
        hyperedges=[
            Hyperedge(
                id="h:1",
                description="First result",
                members=[HyperedgeMember(entity_id="e:a", role="subject")],
                attributes={},
                created_at=now,
                updated_at=now,
            ),
            Hyperedge(
                id="h:2",
                description="Second result",
                members=[HyperedgeMember(entity_id="e:b", role="subject")],
                attributes={},
                created_at=now,
                updated_at=now,
            ),
        ],
    )

    kg = HyperXKnowledgeGraph(client=mock_client)
    retriever = kg.as_retriever(similarity_top_k=10)

    from llama_index.core.schema import QueryBundle
    query = QueryBundle(query_str="test")
    nodes = retriever._retrieve(query)

    assert len(nodes) == 2
    # First result should have higher score
    assert nodes[0].score > nodes[1].score
    # Scores should be between 0 and 1
    assert all(0 <= n.score <= 1 for n in nodes)


def test_retriever_temporal_metadata(mock_client):
    """Test that temporal metadata is included when present."""
    now = datetime.now(timezone.utc)
    mock_client.search.return_value = SearchResult(
        entities=[],
        hyperedges=[
            Hyperedge(
                id="h:temporal",
                description="Temporal hyperedge",
                members=[HyperedgeMember(entity_id="e:a", role="subject")],
                attributes={},
                created_at=now,
                updated_at=now,
                valid_from=now,
                valid_until=None,
            )
        ],
    )

    kg = HyperXKnowledgeGraph(client=mock_client)
    retriever = kg.as_retriever(similarity_top_k=5)

    from llama_index.core.schema import QueryBundle
    query = QueryBundle(query_str="test")
    nodes = retriever._retrieve(query)

    assert "valid_from" in nodes[0].node.metadata
    assert nodes[0].node.metadata["valid_from"] == now.isoformat()
