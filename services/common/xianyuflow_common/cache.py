"""
Multi-level caching implementation
Phase 4: Performance optimization
"""

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

import redis.asyncio as redis
import structlog

logger = structlog.get_logger()

T = TypeVar("T")


class CacheLevel(Enum):
    """缓存级别"""
    L1_MEMORY = "l1_memory"      # 进程内内存缓存
    L2_REDIS = "l2_redis"        # Redis 缓存
    L3_DATABASE = "l3_database"  # 数据库（fallback）


@dataclass
class CacheConfig:
    """缓存配置"""
    l1_ttl_seconds: float = 60          # L1 缓存 TTL
    l2_ttl_seconds: float = 300         # L2 缓存 TTL
    l1_max_size: int = 1000             # L1 最大条目数
    cache_key_prefix: str = "xianyu"    # 缓存键前缀
    enable_l1: bool = True              # 启用 L1 缓存
    enable_l2: bool = True              # 启用 L2 缓存


class L1MemoryCache:
    """L1: 进程内内存缓存（LRU）"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: dict[str, Any] = {}
        self._ttl: dict[str, float] = {}
        self._access_order: list[str] = []
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        async with self._lock:
            if key not in self._cache:
                return None

            # 检查 TTL
            if time.time() > self._ttl.get(key, 0):
                await self._remove(key)
                return None

            # 更新访问顺序
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)

            return self._cache[key]

    async def set(
        self, key: str, value: Any, ttl_seconds: float = 60
    ) -> None:
        """设置缓存值"""
        async with self._lock:
            # 检查是否需要淘汰
            if len(self._cache) >= self.max_size and key not in self._cache:
                await self._evict_oldest()

            # 设置值
            self._cache[key] = value
            self._ttl[key] = time.time() + ttl_seconds

            # 更新访问顺序
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)

    async def delete(self, key: str) -> None:
        """删除缓存值"""
        async with self._lock:
            await self._remove(key)

    async def clear(self) -> None:
        """清空缓存"""
        async with self._lock:
            self._cache.clear()
            self._ttl.clear()
            self._access_order.clear()

    async def _remove(self, key: str) -> None:
        """内部删除方法"""
        self._cache.pop(key, None)
        self._ttl.pop(key, None)
        if key in self._access_order:
            self._access_order.remove(key)

    async def _evict_oldest(self) -> None:
        """淘汰最久未使用的条目"""
        if self._access_order:
            oldest = self._access_order.pop(0)
            await self._remove(oldest)

    def get_stats(self) -> dict[str, int]:
        """获取缓存统计"""
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
        }


class MultiLevelCache:
    """多级缓存管理器"""

    def __init__(
        self,
        config: CacheConfig,
        redis_client: Optional[redis.Redis] = None,
    ):
        self.config = config
        self._l1 = L1MemoryCache(max_size=config.l1_max_size) if config.enable_l1 else None
        self._l2 = redis_client
        self._lock = asyncio.Lock()

    def _make_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        hash_key = hashlib.md5(key_data.encode()).hexdigest()
        return f"{self.config.cache_key_prefix}:{hash_key}"

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存（L1 -> L2 -> None）"""
        # 尝试 L1
        if self._l1:
            value = await self._l1.get(key)
            if value is not None:
                logger.debug("L1 cache hit", key=key)
                return value

        # 尝试 L2
        if self._l2 and self.config.enable_l2:
            data = await self._l2.get(key)
            if data:
                value = json.loads(data)
                logger.debug("L2 cache hit", key=key)

                # 回填 L1
                if self._l1:
                    await self._l1.set(key, value, self.config.l1_ttl_seconds)

                return value

        return None

    async def set(
        self, key: str, value: Any, l2_ttl: Optional[float] = None
    ) -> None:
        """设置缓存"""
        # 设置 L1
        if self._l1:
            await self._l1.set(key, value, self.config.l1_ttl_seconds)

        # 设置 L2
        if self._l2 and self.config.enable_l2:
            ttl = l2_ttl or self.config.l2_ttl_seconds
            await self._l2.setex(key, int(ttl), json.dumps(value))

    async def delete(self, key: str) -> None:
        """删除缓存"""
        if self._l1:
            await self._l1.delete(key)
        if self._l2:
            await self._l2.delete(key)

    async def invalidate_pattern(self, pattern: str) -> int:
        """按模式删除缓存（仅 Redis）"""
        if not self._l2:
            return 0

        # 查找匹配的键
        keys = []
        async for key in self._l2.scan_iter(match=f"{self.config.cache_key_prefix}:{pattern}"):
            keys.append(key)

        if keys:
            await self._l2.delete(*keys)

        return len(keys)

    def cached(
        self,
        ttl_seconds: Optional[float] = None,
        key_func: Optional[Callable] = None,
    ):
        """装饰器：缓存函数结果"""
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            async def async_wrapper(*args, **kwargs) -> T:
                # 生成缓存键
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = self._make_key(func.__name__, *args, **kwargs)

                # 尝试获取缓存
                cached_value = await self.get(cache_key)
                if cached_value is not None:
                    return cached_value

                # 执行函数
                result = await func(*args, **kwargs)

                # 缓存结果
                await self.set(cache_key, result, ttl_seconds)

                return result

            @wraps(func)
            def sync_wrapper(*args, **kwargs) -> T:
                # 同步函数使用线程池
                import asyncio
                return asyncio.run(async_wrapper(*args, **kwargs))

            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

        return decorator


class CacheWarmer:
    """缓存预热器"""

    def __init__(self, cache: MultiLevelCache):
        self.cache = cache
        self._warmup_tasks: list[Callable] = []

    def register(self, key: str, data_loader: Callable[[], Any]) -> None:
        """注册预热任务"""
        self._warmup_tasks.append((key, data_loader))

    async def warm_up(self) -> dict[str, bool]:
        """执行预热"""
        results = {}

        for key, loader in self._warmup_tasks:
            try:
                data = await loader() if asyncio.iscoroutinefunction(loader) else loader()
                await self.cache.set(key, data)
                results[key] = True
                logger.info("Cache warmed up", key=key)
            except Exception as e:
                results[key] = False
                logger.error("Cache warm up failed", key=key, error=str(e))

        return results


# 常用缓存实例
_quote_cache_config = CacheConfig(
    l1_ttl_seconds=30,      # 报价变化快，L1 缓存短
    l2_ttl_seconds=60,      # L2 缓存也短
    cache_key_prefix="quote",
)

_user_cache_config = CacheConfig(
    l1_ttl_seconds=300,     # 用户数据变化慢，可以缓存久一点
    l2_ttl_seconds=3600,
    cache_key_prefix="user",
)
