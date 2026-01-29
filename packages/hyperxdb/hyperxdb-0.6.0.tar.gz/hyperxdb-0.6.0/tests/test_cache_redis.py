"""Tests for Redis cache backend with mocked Redis client."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest


class TestRedisCacheInit:
    """Tests for RedisCache initialization."""

    def test_default_initialization(self):
        """RedisCache should initialize with default values."""
        with patch("redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_from_url.return_value = mock_client

            from hyperx.cache.redis import RedisCache

            cache = RedisCache()

            mock_from_url.assert_called_once_with("redis://localhost:6379")
            assert cache._prefix == "hyperx:"
            assert cache._default_ttl == 300

    def test_custom_initialization(self):
        """RedisCache should accept custom initialization parameters."""
        with patch("redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_from_url.return_value = mock_client

            from hyperx.cache.redis import RedisCache

            cache = RedisCache(
                url="redis://custom:6380",
                prefix="myapp:",
                ttl=600,
            )

            mock_from_url.assert_called_with("redis://custom:6380")
            assert cache._prefix == "myapp:"
            assert cache._default_ttl == 600


class TestRedisCacheKeyPrefixing:
    """Tests for key prefixing."""

    def test_make_key_adds_prefix(self):
        """_make_key should add the configured prefix."""
        with patch("redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_from_url.return_value = mock_client

            from hyperx.cache.redis import RedisCache

            cache = RedisCache(prefix="test:")
            assert cache._make_key("mykey") == "test:mykey"

    def test_make_key_with_default_prefix(self):
        """_make_key should use default prefix."""
        with patch("redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_from_url.return_value = mock_client

            from hyperx.cache.redis import RedisCache

            cache = RedisCache()
            assert cache._make_key("mykey") == "hyperx:mykey"


class TestRedisCacheGet:
    """Tests for get operation."""

    def test_get_existing_key(self):
        """Getting an existing key should return the deserialized value."""
        with patch("redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_from_url.return_value = mock_client

            from hyperx.cache.redis import RedisCache

            cache = RedisCache()
            mock_client.get.return_value = json.dumps({"data": 123}).encode()

            result = cache.get("mykey")

            mock_client.get.assert_called_once_with("hyperx:mykey")
            assert result == {"data": 123}

    def test_get_nonexistent_key(self):
        """Getting a non-existent key should return None."""
        with patch("redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_from_url.return_value = mock_client

            from hyperx.cache.redis import RedisCache

            cache = RedisCache()
            mock_client.get.return_value = None

            result = cache.get("nonexistent")

            mock_client.get.assert_called_once_with("hyperx:nonexistent")
            assert result is None

    def test_get_complex_value(self):
        """Get should handle complex values like nested dicts and lists."""
        with patch("redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_from_url.return_value = mock_client

            from hyperx.cache.redis import RedisCache

            cache = RedisCache()
            complex_value = {"nested": {"a": [1, 2, 3]}, "items": ["x", "y"]}
            mock_client.get.return_value = json.dumps(complex_value).encode()

            result = cache.get("complex")

            assert result == complex_value


class TestRedisCacheSet:
    """Tests for set operation."""

    def test_set_with_default_ttl(self):
        """Setting a value should use default TTL."""
        with patch("redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_from_url.return_value = mock_client

            from hyperx.cache.redis import RedisCache

            cache = RedisCache(ttl=300)
            cache.set("mykey", {"data": 123})

            mock_client.setex.assert_called_once_with(
                "hyperx:mykey",
                300,
                json.dumps({"data": 123}),
            )

    def test_set_with_custom_ttl(self):
        """Setting a value with custom TTL should use that TTL."""
        with patch("redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_from_url.return_value = mock_client

            from hyperx.cache.redis import RedisCache

            cache = RedisCache(ttl=300)
            cache.set("mykey", "value", ttl=60)

            mock_client.setex.assert_called_once_with(
                "hyperx:mykey",
                60,
                json.dumps("value"),
            )

    def test_set_with_ttl_none_uses_default(self):
        """Setting with ttl=None should use default TTL."""
        with patch("redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_from_url.return_value = mock_client

            from hyperx.cache.redis import RedisCache

            cache = RedisCache(ttl=120)
            cache.set("mykey", "value", ttl=None)

            mock_client.setex.assert_called_once_with(
                "hyperx:mykey",
                120,
                json.dumps("value"),
            )

    def test_set_complex_value(self):
        """Set should handle complex values."""
        with patch("redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_from_url.return_value = mock_client

            from hyperx.cache.redis import RedisCache

            cache = RedisCache()
            complex_value = {"nested": {"a": [1, 2, 3]}, "items": ["x", "y"]}
            cache.set("complex", complex_value)

            mock_client.setex.assert_called_once()
            call_args = mock_client.setex.call_args
            assert call_args[0][0] == "hyperx:complex"
            assert json.loads(call_args[0][2]) == complex_value


class TestRedisCacheDelete:
    """Tests for delete operation."""

    def test_delete_existing_key(self):
        """Deleting an existing key should return True."""
        with patch("redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_from_url.return_value = mock_client

            from hyperx.cache.redis import RedisCache

            cache = RedisCache()
            mock_client.delete.return_value = 1  # Redis returns count of deleted keys

            result = cache.delete("mykey")

            mock_client.delete.assert_called_once_with("hyperx:mykey")
            assert result is True

    def test_delete_nonexistent_key(self):
        """Deleting a non-existent key should return False."""
        with patch("redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_from_url.return_value = mock_client

            from hyperx.cache.redis import RedisCache

            cache = RedisCache()
            mock_client.delete.return_value = 0  # No keys deleted

            result = cache.delete("nonexistent")

            mock_client.delete.assert_called_once_with("hyperx:nonexistent")
            assert result is False


class TestRedisCacheClear:
    """Tests for clear operation."""

    def test_clear_removes_prefixed_keys(self):
        """Clear should remove all keys with our prefix."""
        with patch("redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_from_url.return_value = mock_client

            from hyperx.cache.redis import RedisCache

            cache = RedisCache(prefix="test:")

            # Simulate scan returning keys in batches
            mock_client.scan.side_effect = [
                (123, [b"test:key1", b"test:key2"]),  # First batch
                (0, [b"test:key3"]),  # Last batch (cursor=0)
            ]

            cache.clear()

            # Verify scan was called with correct pattern
            assert mock_client.scan.call_count == 2
            mock_client.scan.assert_any_call(0, match="test:*")
            mock_client.scan.assert_any_call(123, match="test:*")

            # Verify delete was called for each batch
            assert mock_client.delete.call_count == 2
            mock_client.delete.assert_any_call(b"test:key1", b"test:key2")
            mock_client.delete.assert_any_call(b"test:key3")

    def test_clear_with_no_keys(self):
        """Clear should handle case when no keys exist."""
        with patch("redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_from_url.return_value = mock_client

            from hyperx.cache.redis import RedisCache

            cache = RedisCache()

            # Simulate scan returning no keys
            mock_client.scan.return_value = (0, [])

            cache.clear()  # Should not raise

            mock_client.scan.assert_called_once_with(0, match="hyperx:*")
            mock_client.delete.assert_not_called()

    def test_clear_single_batch(self):
        """Clear should work when all keys fit in one scan."""
        with patch("redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_from_url.return_value = mock_client

            from hyperx.cache.redis import RedisCache

            cache = RedisCache()

            # All keys returned in one batch
            mock_client.scan.return_value = (0, [b"hyperx:a", b"hyperx:b"])

            cache.clear()

            mock_client.scan.assert_called_once_with(0, match="hyperx:*")
            mock_client.delete.assert_called_once_with(b"hyperx:a", b"hyperx:b")


class TestRedisCacheProtocol:
    """Tests for Cache protocol compliance."""

    def test_redis_cache_implements_protocol(self):
        """RedisCache should implement the Cache protocol."""
        with patch("redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_from_url.return_value = mock_client

            from hyperx.cache import Cache
            from hyperx.cache.redis import RedisCache

            cache = RedisCache()
            assert isinstance(cache, Cache)


class TestRedisCacheEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_empty_string_key(self):
        """Empty string should work as a key."""
        with patch("redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_from_url.return_value = mock_client

            from hyperx.cache.redis import RedisCache

            cache = RedisCache()
            cache.set("", "value")

            mock_client.setex.assert_called_once_with(
                "hyperx:",
                300,
                json.dumps("value"),
            )

    def test_special_characters_in_key(self):
        """Keys with special characters should work."""
        with patch("redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_from_url.return_value = mock_client

            from hyperx.cache.redis import RedisCache

            cache = RedisCache()
            cache.set("key:with:colons", "value")

            mock_client.setex.assert_called_once_with(
                "hyperx:key:with:colons",
                300,
                json.dumps("value"),
            )

    def test_unicode_key(self):
        """Unicode keys should work."""
        with patch("redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_from_url.return_value = mock_client

            from hyperx.cache.redis import RedisCache

            cache = RedisCache()
            cache.set("日本語キー", "value")

            mock_client.setex.assert_called_once_with(
                "hyperx:日本語キー",
                300,
                json.dumps("value"),
            )

    def test_null_value(self):
        """Null values should be serializable."""
        with patch("redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_from_url.return_value = mock_client

            from hyperx.cache.redis import RedisCache

            cache = RedisCache()
            cache.set("nullkey", None)

            mock_client.setex.assert_called_once_with(
                "hyperx:nullkey",
                300,
                json.dumps(None),
            )

    def test_get_returns_deserialized_null(self):
        """Getting a null value should return None (distinguishable from not found)."""
        with patch("redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_from_url.return_value = mock_client

            from hyperx.cache.redis import RedisCache

            cache = RedisCache()
            # Redis returns the JSON encoded null
            mock_client.get.return_value = json.dumps(None).encode()

            result = cache.get("nullkey")

            # Result should be None (the deserialized value)
            assert result is None


class TestRedisCacheConditionalExport:
    """Tests for conditional export in __init__.py."""

    def test_redis_cache_available_in_all_when_installed(self):
        """RedisCache should be in __all__ when redis is installed."""
        from hyperx.cache import __all__

        assert "RedisCache" in __all__

    def test_redis_cache_importable_from_package(self):
        """RedisCache should be importable from hyperx.cache."""
        with patch("redis.from_url"):
            from hyperx.cache import RedisCache

            assert RedisCache is not None
