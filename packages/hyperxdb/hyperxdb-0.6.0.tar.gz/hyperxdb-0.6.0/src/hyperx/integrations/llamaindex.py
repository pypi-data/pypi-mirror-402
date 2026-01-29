"""LlamaIndex integration for HyperX.

Install: pip install hyperx[llamaindex]

Example:
    >>> from hyperx import HyperX
    >>> from hyperx.integrations.llamaindex import HyperXKnowledgeGraph
    >>>
    >>> db = HyperX(api_key="hx_sk_...")
    >>> kg = HyperXKnowledgeGraph(client=db)
    >>> retriever = kg.as_retriever(similarity_top_k=10)
    >>> nodes = retriever.retrieve("React state management")
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

try:
    from llama_index.core.retrievers import BaseRetriever as LlamaBaseRetriever
    from llama_index.core.schema import NodeWithScore, TextNode, QueryBundle
except ImportError as e:
    raise ImportError(
        "LlamaIndex integration requires llama-index-core. "
        "Install with: pip install hyperx[llamaindex]"
    ) from e

if TYPE_CHECKING:
    from hyperx import HyperX, AsyncHyperX

__all__ = ["HyperXKnowledgeGraph", "HyperXRetriever"]


class HyperXRetriever(LlamaBaseRetriever):
    """LlamaIndex retriever backed by HyperX.

    Internal class used by HyperXKnowledgeGraph.as_retriever().
    """

    def __init__(
        self,
        client: Any,
        similarity_top_k: int = 10,
        retriever_mode: Literal["hybrid", "vector", "keyword"] = "hybrid",
    ):
        super().__init__()
        self._client = client
        self._similarity_top_k = similarity_top_k
        self._retriever_mode = retriever_mode

    def _retrieve(self, query_bundle: QueryBundle) -> list[NodeWithScore]:
        """Retrieve nodes from HyperX."""
        query = query_bundle.query_str

        # Use appropriate search method based on mode
        if self._retriever_mode == "keyword":
            result = self._client.search.text(query, limit=self._similarity_top_k)
        else:
            # hybrid and vector both use the main search endpoint
            result = self._client.search(query, limit=self._similarity_top_k)

        # Convert hyperedges to nodes
        nodes = []
        for i, edge in enumerate(result.hyperedges):
            metadata = {
                "id": edge.id,
                "members": [
                    {"entity_id": m.entity_id, "role": m.role}
                    for m in edge.members
                ],
                "source": "hyperx",
            }
            if hasattr(edge, "valid_from") and edge.valid_from:
                metadata["valid_from"] = edge.valid_from.isoformat()
            if hasattr(edge, "valid_until") and edge.valid_until:
                metadata["valid_until"] = edge.valid_until.isoformat()

            node = TextNode(
                text=edge.description,
                id_=edge.id,
                metadata=metadata,
            )
            # Score decreases with position (simple ranking)
            score = 1.0 - (i / max(len(result.hyperedges), 1))
            nodes.append(NodeWithScore(node=node, score=score))

        return nodes


class HyperXKnowledgeGraph:
    """LlamaIndex knowledge graph backed by HyperX hypergraph database.

    Provides retriever interface for use in LlamaIndex RAG pipelines.

    Args:
        client: HyperX client instance
        include_embeddings: Whether to use vector search (default: True)

    Example:
        >>> kg = HyperXKnowledgeGraph(client=db)
        >>> retriever = kg.as_retriever(similarity_top_k=10)
        >>> nodes = retriever.retrieve("How does React handle state?")
    """

    def __init__(
        self,
        client: Any,
        include_embeddings: bool = True,
    ):
        self.client = client
        self.include_embeddings = include_embeddings

    def as_retriever(
        self,
        similarity_top_k: int = 10,
        retriever_mode: Literal["hybrid", "vector", "keyword"] = "hybrid",
    ) -> HyperXRetriever:
        """Get a retriever for this knowledge graph.

        Args:
            similarity_top_k: Number of results to return
            retriever_mode: "hybrid", "vector", or "keyword"

        Returns:
            LlamaIndex-compatible retriever
        """
        return HyperXRetriever(
            client=self.client,
            similarity_top_k=similarity_top_k,
            retriever_mode=retriever_mode,
        )
