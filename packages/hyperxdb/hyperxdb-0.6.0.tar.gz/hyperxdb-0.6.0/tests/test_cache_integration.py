"""Tests for cache integration with client and resources."""

from unittest.mock import MagicMock, patch

import pytest

from hyperx import HyperX, AsyncHyperX
from hyperx.cache import Cache, InMemoryCache


class TestClientCacheParameter:
    """Tests for cache parameter on HyperX client."""

    def test_client_accepts_cache_parameter(self):
        """HyperX client should accept a cache parameter."""
        cache = InMemoryCache()
        with patch("hyperx.http.HTTPClient"):
            client = HyperX(api_key="hx_sk_test", cache=cache)
            assert client._cache is cache

    def test_client_without_cache_has_none(self):
        """HyperX client without cache should have None."""
        with patch("hyperx.http.HTTPClient"):
            client = HyperX(api_key="hx_sk_test")
            assert client._cache is None

    def test_client_passes_cache_to_paths(self):
        """HyperX client should pass cache to paths resource."""
        cache = InMemoryCache()
        with patch("hyperx.http.HTTPClient"):
            client = HyperX(api_key="hx_sk_test", cache=cache)
            assert client.paths._cache is cache

    def test_client_passes_cache_to_search(self):
        """HyperX client should pass cache to search resource."""
        cache = InMemoryCache()
        with patch("hyperx.http.HTTPClient"):
            client = HyperX(api_key="hx_sk_test", cache=cache)
            assert client.search._cache is cache

    def test_client_accepts_server_cache_hint(self):
        """HyperX client should accept server_cache parameter."""
        with patch("hyperx.http.HTTPClient"):
            client = HyperX(api_key="hx_sk_test", server_cache=True)
            assert client._server_cache is True


class TestAsyncClientCacheParameter:
    """Tests for cache parameter on AsyncHyperX client."""

    def test_async_client_accepts_cache_parameter(self):
        """AsyncHyperX client should accept a cache parameter."""
        cache = InMemoryCache()
        with patch("hyperx.http.AsyncHTTPClient"):
            client = AsyncHyperX(api_key="hx_sk_test", cache=cache)
            assert client._cache is cache

    def test_async_client_passes_cache_to_paths(self):
        """AsyncHyperX client should pass cache to paths resource."""
        cache = InMemoryCache()
        with patch("hyperx.http.AsyncHTTPClient"):
            client = AsyncHyperX(api_key="hx_sk_test", cache=cache)
            assert client.paths._cache is cache

    def test_async_client_passes_cache_to_search(self):
        """AsyncHyperX client should pass cache to search resource."""
        cache = InMemoryCache()
        with patch("hyperx.http.AsyncHTTPClient"):
            client = AsyncHyperX(api_key="hx_sk_test", cache=cache)
            assert client.search._cache is cache


class TestPathsCacheIntegration:
    """Tests for cache integration with PathsAPI."""

    def test_paths_find_uses_cache_when_provided(self):
        """paths.find() should use cache when client has cache."""
        cache = InMemoryCache()
        mock_http = MagicMock()
        mock_http.post.return_value = {
            "paths": [
                {"hyperedges": ["he:1", "he:2"], "bridges": [["e:bridge"]], "cost": 1.5}
            ]
        }

        with patch("hyperx.client.HTTPClient", return_value=mock_http):
            client = HyperX(api_key="hx_sk_test", cache=cache)
            # Replace the _http that was created with our mock
            client.paths._http = mock_http

            # First call should hit the API
            result1 = client.paths.find("e:start", "e:end")
            assert mock_http.post.call_count == 1
            assert len(result1) == 1

            # Second call should use cache
            result2 = client.paths.find("e:start", "e:end")
            assert mock_http.post.call_count == 1  # No additional API call
            assert len(result2) == 1

    def test_paths_find_cache_key_includes_params(self):
        """paths.find() cache key should include all parameters."""
        cache = InMemoryCache()
        mock_http = MagicMock()
        mock_http.post.return_value = {"paths": []}

        with patch("hyperx.client.HTTPClient", return_value=mock_http):
            client = HyperX(api_key="hx_sk_test", cache=cache)
            client.paths._http = mock_http

            # Call with default params
            client.paths.find("e:start", "e:end")
            # Call with different max_hops
            client.paths.find("e:start", "e:end", max_hops=6)

            # Both should hit API (different params = different cache keys)
            assert mock_http.post.call_count == 2

    def test_paths_find_cache_bypass_with_false(self):
        """paths.find(cache=False) should bypass cache."""
        cache = InMemoryCache()
        mock_http = MagicMock()
        mock_http.post.return_value = {"paths": []}

        with patch("hyperx.client.HTTPClient", return_value=mock_http):
            client = HyperX(api_key="hx_sk_test", cache=cache)
            client.paths._http = mock_http

            # First call populates cache
            client.paths.find("e:start", "e:end")
            assert mock_http.post.call_count == 1

            # Second call with cache=False should bypass
            client.paths.find("e:start", "e:end", cache=False)
            assert mock_http.post.call_count == 2

    def test_paths_find_cache_enable_with_true(self):
        """paths.find(cache=True) should use cache even if client has no default."""
        cache = InMemoryCache()
        mock_http = MagicMock()
        mock_http.post.return_value = {"paths": []}

        with patch("hyperx.client.HTTPClient", return_value=mock_http):
            # Client created without cache
            client = HyperX(api_key="hx_sk_test")
            client.paths._http = mock_http
            # Manually set cache for this test
            client.paths._cache = cache

            # First call
            client.paths.find("e:start", "e:end", cache=True)
            assert mock_http.post.call_count == 1

            # Second call should hit cache
            client.paths.find("e:start", "e:end", cache=True)
            assert mock_http.post.call_count == 1

    def test_paths_find_sends_cache_hint(self):
        """paths.find(cache_hint='long') should send hint to server."""
        mock_http = MagicMock()
        mock_http.post.return_value = {"paths": []}

        with patch("hyperx.client.HTTPClient", return_value=mock_http):
            client = HyperX(api_key="hx_sk_test")
            client.paths._http = mock_http
            client.paths.find("e:start", "e:end", cache_hint="long")

            # Verify cache_hint was sent in payload
            call_args = mock_http.post.call_args
            assert call_args[1]["json"]["cache_hint"] == "long"


class TestSearchCacheIntegration:
    """Tests for cache integration with SearchAPI."""

    def test_search_uses_cache_when_provided(self):
        """search() should use cache when client has cache."""
        cache = InMemoryCache()
        mock_http = MagicMock()
        mock_http.post.return_value = {"entities": [], "hyperedges": []}

        with patch("hyperx.client.HTTPClient", return_value=mock_http):
            client = HyperX(api_key="hx_sk_test", cache=cache)
            client.search._http = mock_http

            # First call should hit the API
            result1 = client.search("react hooks")
            assert mock_http.post.call_count == 1

            # Second call should use cache
            result2 = client.search("react hooks")
            assert mock_http.post.call_count == 1  # No additional API call

    def test_search_cache_key_includes_limit(self):
        """search() cache key should include limit parameter."""
        cache = InMemoryCache()
        mock_http = MagicMock()
        mock_http.post.return_value = {"entities": [], "hyperedges": []}

        with patch("hyperx.client.HTTPClient", return_value=mock_http):
            client = HyperX(api_key="hx_sk_test", cache=cache)
            client.search._http = mock_http

            # Call with default limit
            client.search("react hooks")
            # Call with different limit
            client.search("react hooks", limit=20)

            # Both should hit API (different params)
            assert mock_http.post.call_count == 2

    def test_search_cache_bypass_with_false(self):
        """search(cache=False) should bypass cache."""
        cache = InMemoryCache()
        mock_http = MagicMock()
        mock_http.post.return_value = {"entities": [], "hyperedges": []}

        with patch("hyperx.client.HTTPClient", return_value=mock_http):
            client = HyperX(api_key="hx_sk_test", cache=cache)
            client.search._http = mock_http

            # First call populates cache
            client.search("react hooks")
            assert mock_http.post.call_count == 1

            # Second call with cache=False should bypass
            client.search("react hooks", cache=False)
            assert mock_http.post.call_count == 2

    def test_search_vector_uses_cache(self):
        """search.vector() should use cache when enabled."""
        cache = InMemoryCache()
        mock_http = MagicMock()
        mock_http.post.return_value = {"entities": [], "hyperedges": []}

        with patch("hyperx.client.HTTPClient", return_value=mock_http):
            client = HyperX(api_key="hx_sk_test", cache=cache)
            client.search._http = mock_http

            embedding = [0.1, 0.2, 0.3]
            # First call
            client.search.vector(embedding)
            assert mock_http.post.call_count == 1

            # Second call should use cache
            client.search.vector(embedding)
            assert mock_http.post.call_count == 1

    def test_search_text_uses_cache(self):
        """search.text() should use cache when enabled."""
        cache = InMemoryCache()
        mock_http = MagicMock()
        mock_http.post.return_value = {"entities": [], "hyperedges": []}

        with patch("hyperx.client.HTTPClient", return_value=mock_http):
            client = HyperX(api_key="hx_sk_test", cache=cache)
            client.search._http = mock_http

            # First call
            client.search.text("react state")
            assert mock_http.post.call_count == 1

            # Second call should use cache
            client.search.text("react state")
            assert mock_http.post.call_count == 1


class TestAsyncPathsCacheIntegration:
    """Tests for cache integration with AsyncPathsAPI."""

    @pytest.mark.asyncio
    async def test_async_paths_find_uses_cache(self):
        """async paths.find() should use cache when client has cache."""
        cache = InMemoryCache()
        mock_http = MagicMock()

        # Make post return a coroutine
        async def mock_post(*args, **kwargs):
            return {"paths": []}

        mock_http.post = MagicMock(side_effect=mock_post)

        with patch("hyperx.async_client.AsyncHTTPClient", return_value=mock_http):
            client = AsyncHyperX(api_key="hx_sk_test", cache=cache)
            client.paths._http = mock_http

            # First call should hit the API
            await client.paths.find("e:start", "e:end")
            assert mock_http.post.call_count == 1

            # Second call should use cache
            await client.paths.find("e:start", "e:end")
            assert mock_http.post.call_count == 1


class TestAsyncSearchCacheIntegration:
    """Tests for cache integration with AsyncSearchAPI."""

    @pytest.mark.asyncio
    async def test_async_search_uses_cache(self):
        """async search() should use cache when client has cache."""
        cache = InMemoryCache()
        mock_http = MagicMock()

        async def mock_post(*args, **kwargs):
            return {"entities": [], "hyperedges": []}

        mock_http.post = MagicMock(side_effect=mock_post)

        with patch("hyperx.async_client.AsyncHTTPClient", return_value=mock_http):
            client = AsyncHyperX(api_key="hx_sk_test", cache=cache)
            client.search._http = mock_http

            # First call should hit the API
            await client.search("react hooks")
            assert mock_http.post.call_count == 1

            # Second call should use cache
            await client.search("react hooks")
            assert mock_http.post.call_count == 1


class TestCacheMissThenHit:
    """Tests for cache miss then hit behavior."""

    def test_paths_cache_miss_then_hit(self):
        """First call misses cache, second hits cache."""
        cache = InMemoryCache()
        mock_http = MagicMock()
        mock_http.post.return_value = {
            "paths": [
                {"hyperedges": ["he:1"], "bridges": [[]], "cost": 1.0}
            ]
        }

        with patch("hyperx.client.HTTPClient", return_value=mock_http):
            client = HyperX(api_key="hx_sk_test", cache=cache)
            client.paths._http = mock_http

            # Cache miss - should call API
            result1 = client.paths.find("e:a", "e:b")
            assert len(result1) == 1
            assert result1[0].cost == 1.0

            # Cache hit - should NOT call API
            result2 = client.paths.find("e:a", "e:b")
            assert len(result2) == 1
            assert result2[0].cost == 1.0

            # API should only be called once
            assert mock_http.post.call_count == 1

    def test_search_cache_miss_then_hit(self):
        """First search misses cache, second hits cache."""
        cache = InMemoryCache()
        mock_http = MagicMock()
        mock_http.post.return_value = {
            "entities": [
                {
                    "id": "e:1",
                    "name": "React",
                    "entity_type": "framework",
                    "attributes": {},
                    "confidence": 1.0,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                }
            ],
            "hyperedges": [],
        }

        with patch("hyperx.client.HTTPClient", return_value=mock_http):
            client = HyperX(api_key="hx_sk_test", cache=cache)
            client.search._http = mock_http

            # Cache miss
            result1 = client.search("react")
            assert len(result1.entities) == 1
            assert result1.entities[0].name == "React"

            # Cache hit
            result2 = client.search("react")
            assert len(result2.entities) == 1
            assert result2.entities[0].name == "React"

            # API should only be called once
            assert mock_http.post.call_count == 1
