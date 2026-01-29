"""
Async Client Example
====================

This example demonstrates async operations with HyperX:
- Async context manager
- Concurrent operations
- Async iteration
- Integration with async frameworks
"""

import asyncio
from hyperx import AsyncHyperX

# ===================
# Basic Async Usage
# ===================

async def basic_example():
    """Basic async client usage."""

    async with AsyncHyperX("https://api.hyperxdb.dev", api_key="your-api-key") as client:

        # Create entity (async)
        entity = await client.entities.create(
            label="Async Entity",
            entity_type="Concept",
            description="Created asynchronously"
        )
        print(f"Created: {entity.label}")

        # Get entity
        retrieved = await client.entities.get(entity.id)
        print(f"Retrieved: {retrieved.label}")

        # Search
        results = await client.search.hybrid(
            query="machine learning",
            limit=10
        )
        print(f"Found: {len(results.items)} results")

asyncio.run(basic_example())

# ===================
# Concurrent Operations
# ===================

async def concurrent_example():
    """Run multiple operations concurrently."""

    async with AsyncHyperX("https://api.hyperxdb.dev", api_key="your-api-key") as client:

        # Create multiple entities concurrently
        labels = ["Entity A", "Entity B", "Entity C", "Entity D", "Entity E"]

        tasks = [
            client.entities.create(
                label=label,
                entity_type="Concept",
                description=f"Concurrent entity: {label}"
            )
            for label in labels
        ]

        # Wait for all to complete
        entities = await asyncio.gather(*tasks)

        print(f"\n=== Concurrent Creation ===")
        print(f"Created {len(entities)} entities concurrently")
        for entity in entities:
            print(f"  - {entity.label} ({entity.id})")

        # Concurrent searches
        queries = [
            "machine learning",
            "deep learning",
            "neural networks",
            "transformers"
        ]

        search_tasks = [
            client.search.hybrid(query=q, limit=5)
            for q in queries
        ]

        search_results = await asyncio.gather(*search_tasks)

        print(f"\n=== Concurrent Searches ===")
        for query, results in zip(queries, search_results):
            print(f"  '{query}': {len(results.items)} results")

asyncio.run(concurrent_example())

# ===================
# Async Iteration
# ===================

async def pagination_example():
    """Async pagination through large result sets."""

    async with AsyncHyperX("https://api.hyperxdb.dev", api_key="your-api-key") as client:

        print("\n=== Async Pagination ===")

        offset = 0
        limit = 100
        total_processed = 0

        while True:
            page = await client.entities.list(
                entity_type="Concept",
                limit=limit,
                offset=offset
            )

            if not page.items:
                break

            for entity in page.items:
                # Process each entity
                total_processed += 1

            print(f"  Processed page: {offset // limit + 1} ({len(page.items)} items)")
            offset += limit

            if offset >= page.total:
                break

        print(f"  Total processed: {total_processed}")

asyncio.run(pagination_example())

# ===================
# Async Context Manager Pattern
# ===================

async def context_manager_example():
    """Proper resource management with async context manager."""

    # Client is automatically closed when exiting the context
    async with AsyncHyperX("https://api.hyperxdb.dev", api_key="your-api-key") as client:

        # Operations here...
        result = await client.search.hybrid(query="test", limit=5)
        print(f"Results: {len(result.items)}")

    # Client connection is now closed

# ===================
# Error Handling
# ===================

async def error_handling_example():
    """Async error handling."""

    from hyperx.exceptions import NotFoundError, RateLimitError, HyperXError

    async with AsyncHyperX("https://api.hyperxdb.dev", api_key="your-api-key") as client:

        try:
            # Try to get non-existent entity
            entity = await client.entities.get("non-existent-id")

        except NotFoundError:
            print("Entity not found (expected)")

        except RateLimitError as e:
            print(f"Rate limited. Retry after: {e.retry_after}s")
            await asyncio.sleep(e.retry_after)
            # Retry...

        except HyperXError as e:
            print(f"API error: {e}")

asyncio.run(error_handling_example())

# ===================
# With FastAPI
# ===================

"""
Example FastAPI integration:

from fastapi import FastAPI, Depends
from hyperx import AsyncHyperX

app = FastAPI()
client = AsyncHyperX("https://api.hyperxdb.dev", api_key="your-api-key")

@app.on_event("startup")
async def startup():
    await client.connect()

@app.on_event("shutdown")
async def shutdown():
    await client.close()

@app.get("/search")
async def search(query: str, limit: int = 10):
    results = await client.search.hybrid(query=query, limit=limit)
    return {"results": [r.entity.dict() for r in results.items]}

@app.get("/entity/{entity_id}")
async def get_entity(entity_id: str):
    entity = await client.entities.get(entity_id)
    return entity.dict()
"""

# ===================
# With aiohttp Session
# ===================

async def custom_session_example():
    """Use a custom aiohttp session for connection pooling."""

    import aiohttp

    # Create custom session with connection pooling
    connector = aiohttp.TCPConnector(limit=100, limit_per_host=20)
    session = aiohttp.ClientSession(connector=connector)

    try:
        client = AsyncHyperX(
            "https://api.hyperxdb.dev",
            api_key="your-api-key",
            session=session  # Pass custom session
        )

        # Use client...
        result = await client.search.hybrid(query="test", limit=5)
        print(f"Results: {len(result.items)}")

    finally:
        await session.close()

# asyncio.run(custom_session_example())

# ===================
# Timeout Handling
# ===================

async def timeout_example():
    """Handle timeouts properly."""

    async with AsyncHyperX(
        "https://api.hyperxdb.dev",
        api_key="your-api-key",
        timeout=30.0  # 30 second timeout
    ) as client:

        try:
            # Operation with timeout
            async with asyncio.timeout(10.0):  # 10 second limit
                results = await client.search.hybrid(
                    query="complex query",
                    limit=100
                )

        except asyncio.TimeoutError:
            print("Operation timed out")

asyncio.run(timeout_example())

# ===================
# Semaphore for Rate Limiting
# ===================

async def rate_limited_example():
    """Client-side rate limiting with semaphore."""

    async with AsyncHyperX("https://api.hyperxdb.dev", api_key="your-api-key") as client:

        # Limit to 10 concurrent requests
        semaphore = asyncio.Semaphore(10)

        async def limited_search(query: str):
            async with semaphore:
                return await client.search.hybrid(query=query, limit=5)

        # Many queries, but only 10 concurrent
        queries = [f"query {i}" for i in range(100)]

        tasks = [limited_search(q) for q in queries]
        results = await asyncio.gather(*tasks)

        print(f"\n=== Rate Limited Requests ===")
        print(f"Completed {len(results)} searches with max 10 concurrent")

asyncio.run(rate_limited_example())
