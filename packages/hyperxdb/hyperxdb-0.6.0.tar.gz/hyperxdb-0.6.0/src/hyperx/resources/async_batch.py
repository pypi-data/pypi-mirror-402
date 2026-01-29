"""Async Batch API resource for bulk operations."""

from __future__ import annotations

from typing import Any

from hyperx.batch import (
    BatchItemResult,
    BatchResult,
    EntityCreate,
    EntityDelete,
    HyperedgeCreate,
    HyperedgeDelete,
)
from hyperx.http import AsyncHTTPClient

# Type alias for batch operations
BatchOperation = EntityCreate | HyperedgeCreate | EntityDelete | HyperedgeDelete


class AsyncBatchAPI:
    """Async API for executing batch operations.

    The AsyncBatchAPI allows you to execute multiple create/delete operations
    in a single API call, improving performance and ensuring atomicity.

    Example:
        >>> from hyperx import AsyncHyperX
        >>> from hyperx.batch import EntityCreate, HyperedgeCreate
        >>> async with AsyncHyperX(api_key="hx_sk_...") as db:
        ...     result = await db.batch.execute([
        ...         EntityCreate(name="React", entity_type="library"),
        ...         EntityCreate(name="Vue", entity_type="library"),
        ...         HyperedgeCreate(
        ...             description="React competes with Vue",
        ...             members=[
        ...                 {"entity_id": "e:react", "role": "subject"},
        ...                 {"entity_id": "e:vue", "role": "object"},
        ...             ],
        ...         ),
        ...     ])
        ...     print(f"Created {result.succeeded} items")
    """

    def __init__(self, http: AsyncHTTPClient):
        """Initialize AsyncBatchAPI.

        Args:
            http: Async HTTP client for making API requests.
        """
        self._http = http

    async def execute(
        self,
        operations: list[BatchOperation],
        *,
        atomic: bool = True,
    ) -> BatchResult:
        """Execute batch operations asynchronously.

        Args:
            operations: List of BatchOperation objects (EntityCreate,
                HyperedgeCreate, EntityDelete, HyperedgeDelete).
            atomic: If True (default), all operations succeed or all fail.
                If False, operations are executed in best-effort mode where
                individual failures don't affect other operations.

        Returns:
            BatchResult containing details about the batch execution including
            success status, counts, and individual item results.

        Example:
            >>> # Atomic mode (default) - all or nothing
            >>> result = await db.batch.execute([
            ...     EntityCreate(name="E1", entity_type="concept"),
            ...     EntityCreate(name="E2", entity_type="concept"),
            ... ])
            >>>
            >>> # Best-effort mode - continue on individual failures
            >>> result = await db.batch.execute([
            ...     EntityCreate(name="E1", entity_type="concept"),
            ...     EntityCreate(name="E2", entity_type="concept"),
            ... ], atomic=False)
            >>> if not result.all_succeeded:
            ...     for item in result.failed_items:
            ...         print(f"Operation {item.index} failed: {item.error}")
        """
        # Serialize operations to dictionaries
        serialized_operations = [op.to_dict() for op in operations]

        # Build request payload
        payload: dict[str, Any] = {
            "operations": serialized_operations,
            "atomic": atomic,
        }

        # Make API request
        data = await self._http.post("/v1/batch", json=payload)

        # Parse response into BatchResult
        return self._parse_result(data)

    def _parse_result(self, data: dict[str, Any]) -> BatchResult:
        """Parse API response into BatchResult.

        Args:
            data: Raw API response dictionary.

        Returns:
            Parsed BatchResult object.
        """
        results = [
            BatchItemResult(
                success=item["success"],
                index=item["index"],
                error=item.get("error"),
            )
            for item in data.get("results", [])
        ]

        return BatchResult(
            success=data["success"],
            total=data["total"],
            succeeded=data["succeeded"],
            failed=data["failed"],
            results=results,
        )
