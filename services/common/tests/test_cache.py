"""Tests for xianyuflow_common.cache module."""
import time

import pytest

from xianyuflow_common.cache import CacheConfig, L1MemoryCache


class TestL1MemoryCache:
    """Tests for L1MemoryCache (LRU + TTL)."""

    @pytest.mark.asyncio
    async def test_set_and_get(self) -> None:
        """Basic set and get operations should work."""
        cache = L1MemoryCache()
        await cache.set("key1", "value1")
        result = await cache.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self) -> None:
        """Getting a non-existent key should return None."""
        cache = L1MemoryCache()
        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self) -> None:
        """Deleting a key should remove it from cache."""
        cache = L1MemoryCache()
        await cache.set("key1", "value1")
        await cache.delete("key1")
        result = await cache.get("key1")
        assert result is None

    @pytest.mark.asyncio
    async def test_clear(self) -> None:
        """Clear should remove all entries."""
        cache = L1MemoryCache()
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.clear()
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    @pytest.mark.asyncio
    async def test_lru_eviction_when_full(self) -> None:
        """Cache should evict least recently used entry when at max size."""
        cache = L1MemoryCache(max_size=3)
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")
        # LRU order: key1, key2, key3

        await cache.set("key4", "value4")
        # key1 should be evicted (oldest)

        assert await cache.get("key1") is None
        assert await cache.get("key2") == "value2"
        assert await cache.get("key3") == "value3"
        assert await cache.get("key4") == "value4"

    @pytest.mark.asyncio
    async def test_lru_access_updates_order(self) -> None:
        """Accessing a key should update its LRU position."""
        cache = L1MemoryCache(max_size=3)
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")
        # LRU order: key1, key2, key3

        # Access key1 to move it to the most recent position
        _ = await cache.get("key1")

        # Now add key4, which should evict key2 (oldest after key1 was accessed)
        await cache.set("key4", "value4")

        assert await cache.get("key1") == "value1"  # Should NOT be evicted
        assert await cache.get("key2") is None  # Should be evicted
        assert await cache.get("key3") == "value3"
        assert await cache.get("key4") == "value4"

    @pytest.mark.asyncio
    async def test_ttl_expiry(self) -> None:
        """Entry should expire after TTL."""
        cache = L1MemoryCache()
        # Set with very short TTL
        await cache.set("key1", "value1", ttl_seconds=0.05)
        # Should be available immediately
        assert await cache.get("key1") == "value1"
        # Wait for expiry
        time.sleep(0.1)
        result = await cache.get("key1")
        assert result is None

    @pytest.mark.asyncio
    async def test_ttl_no_expiry_within_window(self) -> None:
        """Entry should not expire before TTL."""
        cache = L1MemoryCache()
        await cache.set("key1", "value1", ttl_seconds=5.0)
        time.sleep(0.05)
        result = await cache.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_stats(self) -> None:
        """get_stats should return correct size and max_size."""
        cache = L1MemoryCache(max_size=10)
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        stats = cache.get_stats()
        assert stats["size"] == 2
        assert stats["max_size"] == 10

    @pytest.mark.asyncio
    async def test_update_existing_key_does_not_trigger_eviction(self) -> None:
        """Updating an existing key should not trigger eviction even if at max size."""
        cache = L1MemoryCache(max_size=2)
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        # Update existing key
        await cache.set("key1", "new_value1")
        # Add another key
        await cache.set("key3", "value3")
        # Both key1 (updated) and key3 should exist
        assert await cache.get("key1") == "new_value1"
        assert await cache.get("key2") is None  # key2 was evicted
        assert await cache.get("key3") == "value3"


class TestCacheConfig:
    """Tests for CacheConfig dataclass."""

    def test_cache_config_defaults(self) -> None:
        """Default config should have sensible values."""
        config = CacheConfig()
        assert config.l1_ttl_seconds == 60
        assert config.l2_ttl_seconds == 300
        assert config.l1_max_size == 1000
        assert config.cache_key_prefix == "xianyu"
        assert config.enable_l1 is True
        assert config.enable_l2 is True

    def test_cache_config_custom_values(self) -> None:
        """Custom config values should be set correctly."""
        config = CacheConfig(
            l1_ttl_seconds=30,
            l2_ttl_seconds=60,
            l1_max_size=500,
            cache_key_prefix="custom",
            enable_l1=False,
            enable_l2=False,
        )
        assert config.l1_ttl_seconds == 30
        assert config.l2_ttl_seconds == 60
        assert config.l1_max_size == 500
        assert config.cache_key_prefix == "custom"
        assert config.enable_l1 is False
        assert config.enable_l2 is False
