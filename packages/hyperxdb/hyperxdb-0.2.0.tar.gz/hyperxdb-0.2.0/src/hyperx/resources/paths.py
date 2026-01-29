"""Paths API resource - the hero feature.

Multi-hop reasoning paths across hypergraph relationships.
This is HyperX's key differentiator from vector databases.
"""

from hyperx.http import HTTPClient
from hyperx.models import PathResult, PathsResponse


class PathsAPI:
    """API for finding multi-hop paths between entities.

    This is HyperX's differentiating feature - intersection-constrained
    pathfinding across hypergraph relationships enables reasoning that
    vector databases cannot perform.

    Example:
        >>> paths = db.paths.find(
        ...     from_entity="e:useState",
        ...     to_entity="e:redux",
        ...     max_hops=4
        ... )
        >>> for path in paths:
        ...     print(f"Cost: {path.cost}, Hops: {len(path.hyperedges)}")
    """

    def __init__(self, http: HTTPClient):
        self._http = http

    def find(
        self,
        from_entity: str,
        to_entity: str,
        max_hops: int = 4,
        intersection_size: int = 1,
        k_paths: int = 3,
    ) -> list[PathResult]:
        """Find multi-hop paths between two entities.

        This implements intersection-constrained pathfinding inspired by
        the HOG-DB paper from ETH Zurich. Paths traverse through hyperedges
        that share bridge entities.

        Args:
            from_entity: Starting entity ID
            to_entity: Target entity ID
            max_hops: Maximum number of hyperedge hops (default: 4)
            intersection_size: Minimum bridge size between hyperedges (default: 1)
            k_paths: Number of paths to return (default: 3)

        Returns:
            List of PathResult objects, each containing:
            - hyperedges: Ordered list of hyperedge IDs in the path
            - bridges: Entity IDs that connect adjacent hyperedges
            - cost: Total path cost (lower is better)

        Example:
            >>> # Find how useState relates to Redux
            >>> paths = db.paths.find(
            ...     from_entity="e:useState",
            ...     to_entity="e:redux",
            ...     max_hops=4,
            ...     k_paths=5
            ... )
            >>> for path in paths:
            ...     print(f"Path via: {' -> '.join(path.hyperedges)}")
        """
        payload = {
            "from": from_entity,
            "to": to_entity,
            "constraints": {
                "max_hops": max_hops,
                "intersection_size": intersection_size,
                "k_paths": k_paths,
            },
        }
        data = self._http.post("/v1/paths", json=payload)
        response = PathsResponse.model_validate(data)
        return response.paths
