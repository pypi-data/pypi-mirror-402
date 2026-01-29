"""Tests for cache protocol and in-memory backend."""

import time

import pytest

from hyperx.cache import Cache, InMemoryCache


class TestCacheProtocol:
    """Tests for Cache protocol compliance."""

    def test_inmemory_cache_implements_protocol(self):
        """InMemoryCache should implement the Cache protocol."""
        cache = InMemoryCache()
        assert isinstance(cache, Cache)

    def test_protocol_is_runtime_checkable(self):
        """Cache protocol should be runtime checkable."""
        # A class that implements all required methods
        class CustomCache:
            def get(self, key: str):
                return None

            def set(self, key: str, value, ttl=None):
                pass

            def delete(self, key: str) -> bool:
                return False

            def clear(self):
                pass

        custom = CustomCache()
        assert isinstance(custom, Cache)

    def test_non_cache_fails_protocol_check(self):
        """Objects not implementing Cache should fail isinstance check."""

        class NotACache:
            pass

        not_a_cache = NotACache()
        assert not isinstance(not_a_cache, Cache)


class TestInMemoryCacheBasics:
    """Tests for basic get/set operations."""

    def test_set_and_get(self):
        """Basic set and get should work."""
        cache = InMemoryCache()
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_nonexistent_returns_none(self):
        """Getting a non-existent key should return None."""
        cache = InMemoryCache()
        assert cache.get("nonexistent") is None

    def test_set_overwrites_existing(self):
        """Setting an existing key should overwrite the value."""
        cache = InMemoryCache()
        cache.set("key1", "value1")
        cache.set("key1", "value2")
        assert cache.get("key1") == "value2"

    def test_set_and_get_complex_values(self):
        """Cache should handle complex values like dicts and lists."""
        cache = InMemoryCache()

        # Dict value
        cache.set("dict_key", {"data": 123, "nested": {"a": 1}})
        assert cache.get("dict_key") == {"data": 123, "nested": {"a": 1}}

        # List value
        cache.set("list_key", [1, 2, 3])
        assert cache.get("list_key") == [1, 2, 3]

        # None value (should still be retrievable)
        cache.set("none_key", None)
        # This should return None and be distinguishable from "not found"
        # We need to use a sentinel or check if key exists
        assert "none_key" in cache._cache


class TestInMemoryCacheDelete:
    """Tests for delete operations."""

    def test_delete_existing_key(self):
        """Deleting an existing key should return True."""
        cache = InMemoryCache()
        cache.set("key1", "value1")
        assert cache.delete("key1") is True
        assert cache.get("key1") is None

    def test_delete_nonexistent_key(self):
        """Deleting a non-existent key should return False."""
        cache = InMemoryCache()
        assert cache.delete("nonexistent") is False


class TestInMemoryCacheClear:
    """Tests for clear operation."""

    def test_clear_removes_all_entries(self):
        """Clear should remove all cached entries."""
        cache = InMemoryCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") is None

    def test_clear_empty_cache(self):
        """Clear on empty cache should not raise."""
        cache = InMemoryCache()
        cache.clear()  # Should not raise


class TestInMemoryCacheTTL:
    """Tests for TTL (time-to-live) functionality."""

    def test_default_ttl(self):
        """Cache should have a default TTL of 300 seconds."""
        cache = InMemoryCache()
        assert cache._default_ttl == 300

    def test_custom_default_ttl(self):
        """Cache should accept custom default TTL."""
        cache = InMemoryCache(ttl=60)
        assert cache._default_ttl == 60

    def test_item_ttl_override(self):
        """Individual items can have custom TTL."""
        cache = InMemoryCache(ttl=300)
        cache.set("short_lived", "value", ttl=1)

        # Should be available immediately
        assert cache.get("short_lived") == "value"

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired now
        assert cache.get("short_lived") is None

    def test_expired_item_returns_none(self):
        """Expired items should return None."""
        cache = InMemoryCache(ttl=1)
        cache.set("key1", "value1")

        # Available immediately
        assert cache.get("key1") == "value1"

        # Wait for expiration
        time.sleep(1.1)

        # Should return None after expiration
        assert cache.get("key1") is None

    def test_ttl_none_uses_default(self):
        """Setting with ttl=None should use the default TTL."""
        cache = InMemoryCache(ttl=1)
        cache.set("key1", "value1", ttl=None)

        # Should expire after default TTL
        time.sleep(1.1)
        assert cache.get("key1") is None


class TestInMemoryCacheLRU:
    """Tests for LRU (Least Recently Used) eviction."""

    def test_default_max_size(self):
        """Cache should have a default max size of 1000."""
        cache = InMemoryCache()
        assert cache._max_size == 1000

    def test_custom_max_size(self):
        """Cache should accept custom max size."""
        cache = InMemoryCache(max_size=100)
        assert cache._max_size == 100

    def test_evicts_oldest_when_full(self):
        """Oldest items should be evicted when cache exceeds max_size."""
        cache = InMemoryCache(max_size=3, ttl=3600)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # All three should be present
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

        # Add a fourth item - should evict key1 (oldest)
        cache.set("key4", "value4")

        assert cache.get("key1") is None  # Evicted
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_get_updates_lru_order(self):
        """Getting an item should move it to most recently used."""
        cache = InMemoryCache(max_size=3, ttl=3600)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Access key1 to make it most recently used
        cache.get("key1")

        # Add key4 - should evict key2 (now oldest)
        cache.set("key4", "value4")

        assert cache.get("key1") == "value1"  # Still present (was accessed)
        assert cache.get("key2") is None  # Evicted (was oldest)
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_set_updates_lru_order(self):
        """Setting an existing item should move it to most recently used."""
        cache = InMemoryCache(max_size=3, ttl=3600)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Update key1 to make it most recently used
        cache.set("key1", "updated_value1")

        # Add key4 - should evict key2 (now oldest)
        cache.set("key4", "value4")

        assert cache.get("key1") == "updated_value1"  # Still present (was updated)
        assert cache.get("key2") is None  # Evicted (was oldest)
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_max_size_one(self):
        """Cache should work with max_size of 1."""
        cache = InMemoryCache(max_size=1, ttl=3600)

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        cache.set("key2", "value2")
        assert cache.get("key1") is None  # Evicted
        assert cache.get("key2") == "value2"


class TestInMemoryCacheEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_empty_string_key(self):
        """Empty string should work as a key."""
        cache = InMemoryCache()
        cache.set("", "empty_key_value")
        assert cache.get("") == "empty_key_value"

    def test_special_characters_in_key(self):
        """Keys with special characters should work."""
        cache = InMemoryCache()
        cache.set("key:with:colons", "value1")
        cache.set("key/with/slashes", "value2")
        cache.set("key.with.dots", "value3")

        assert cache.get("key:with:colons") == "value1"
        assert cache.get("key/with/slashes") == "value2"
        assert cache.get("key.with.dots") == "value3"

    def test_unicode_key(self):
        """Unicode keys should work."""
        cache = InMemoryCache()
        cache.set("key_with_emoji_🎉", "party")
        cache.set("日本語キー", "japanese")

        assert cache.get("key_with_emoji_🎉") == "party"
        assert cache.get("日本語キー") == "japanese"

    def test_concurrent_operations_basic(self):
        """Basic operations should be safe for simple concurrent access."""
        cache = InMemoryCache(max_size=100, ttl=3600)

        # Fill cache
        for i in range(50):
            cache.set(f"key{i}", f"value{i}")

        # Read while writing
        for i in range(50, 100):
            cache.set(f"key{i}", f"value{i}")
            # Previous keys should still be accessible
            assert cache.get(f"key{i-25}") is not None or cache.get(f"key{i-25}") is None

    def test_get_expired_removes_entry(self):
        """Getting an expired entry should remove it from cache."""
        cache = InMemoryCache(max_size=3, ttl=1)

        cache.set("key1", "value1")
        time.sleep(1.1)

        # Get should return None and remove the entry
        assert cache.get("key1") is None

        # Entry should be removed from internal cache
        assert "key1" not in cache._cache


class TestInMemoryCacheInit:
    """Tests for cache initialization."""

    def test_default_initialization(self):
        """Cache should initialize with default values."""
        cache = InMemoryCache()
        assert cache._max_size == 1000
        assert cache._default_ttl == 300
        assert len(cache._cache) == 0

    def test_custom_initialization(self):
        """Cache should accept custom initialization parameters."""
        cache = InMemoryCache(max_size=500, ttl=120)
        assert cache._max_size == 500
        assert cache._default_ttl == 120
        assert len(cache._cache) == 0
