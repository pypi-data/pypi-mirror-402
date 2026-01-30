"""Cache module - simple cache creation without factory patterns."""

from __future__ import annotations

from enum import Enum
from typing import Any

from yitool.yi_cache._abc import AbcYiCache
from yitool.yi_cache.yi_cache_memory import YiCacheMemory
from yitool.yi_cache.yi_cache_redis import YiCacheRedis
from yitool.yi_cache.yi_cache_ttl import YiCacheTTL
from yitool.yi_cache.yi_redis import YiRedis

__all__ = [
    "AbcYiCache",
    "YiCacheMemory",
    "YiCacheRedis",
    "YiCacheTTL",
    "YiRedis",
    "YiCacheFactory",
    "YiCacheType",
    "YiCacheManager",
]


class YiCacheType(Enum):
    """Cache type enumeration."""

    MEMORY = "memory"
    TTL = "ttl"
    REDIS = "redis"


class YiCacheFactory:
    """Factory for creating cache instances."""

    @staticmethod
    def create(cache_type: YiCacheType | str, config: dict[str, Any] | None = None) -> AbcYiCache:
        """Create a cache instance.

        Args:
            cache_type: Type of cache to create
            config: Configuration for the cache

        Returns:
            Cache instance
        """
        if isinstance(cache_type, str):
            cache_type = YiCacheType(cache_type)

        config = config or {}

        if cache_type == YiCacheType.MEMORY:
            return YiCacheMemory(
                max_size=config.get("maxsize", config.get("max_size", 1000)),
                strategy=config.get("strategy", "LRU"),
                enable_events=config.get("enable_events", False)
            )
        elif cache_type == YiCacheType.TTL:
            return YiCacheTTL(
                maxsize=config.get("maxsize", config.get("max_size", 1000)),
                ttl=config.get("ttl", config.get("ttl_seconds", 3600)),
                name=config.get("name", "ttl"),
                enable_events=config.get("enable_events", False)
            )
        elif cache_type == YiCacheType.REDIS:
            return YiCacheRedis(
                host=config.get("host", "localhost"),
                port=config.get("port", 6379),
                db=config.get("db", 0),
                password=config.get("password"),
                enable_events=config.get("enable_events", False)
            )
        else:
            raise ValueError(f"Unsupported cache type: {cache_type}")


class YiCacheManager:
    """Manager for multiple cache instances."""

    def __init__(self):
        self._caches: dict[str, AbcYiCache] = {}
        self._default_cache = YiCacheFactory.create(YiCacheType.MEMORY)

    def register(self, name: str, cache: AbcYiCache):
        """Register a cache instance.

        Args:
            name: Name for the cache
            cache: Cache instance
        """
        self._caches[name] = cache

    def unregister(self, name: str):
        """Unregister a cache instance.

        Args:
            name: Name of the cache to unregister
        """
        if name in self._caches:
            del self._caches[name]

    def get_cache(self, name: str = "default") -> AbcYiCache:
        """Get a cache instance.

        Args:
            name: Name of the cache

        Returns:
            Cache instance

        Raises:
            KeyError: If cache not found
        """
        if name == "default":
            return self._default_cache
        if name not in self._caches:
            raise KeyError(f"Cache '{name}' not found")
        return self._caches[name]

    def set(self, key: str, value: Any, name: str = "default", expire: int | None = None):
        """Set a value in a cache.

        Args:
            key: Cache key
            value: Value to cache
            name: Name of the cache
            expire: Expiration time in seconds
        """
        cache = self.get_cache(name)
        cache.set(key, value, expire=expire)

    def get(self, key: str, name: str = "default", default: Any = None) -> Any:
        """Get a value from a cache.

        Args:
            key: Cache key
            name: Name of the cache
            default: Default value if key not found

        Returns:
            Cached value or default
        """
        cache = self.get_cache(name)
        return cache.get(key, default=default)

    def get_all_caches(self) -> dict[str, AbcYiCache]:
        """Get all registered caches.

        Returns:
            Dictionary of cache names to cache instances
        """
        return {"default": self._default_cache, **self._caches}


def memory_cache(maxsize: int = 1000, strategy: str = "LRU") -> YiCacheMemory:
    """Create in-memory cache."""
    return YiCacheMemory(max_size=maxsize, strategy=strategy)


def redis_cache(host: str = "localhost", port: int = 6379, db: int = 0) -> YiCacheRedis:
    """Create Redis cache."""
    return YiCacheRedis(host=host, port=port, db=db)


def ttl_cache(maxsize: int = 1000, ttl_seconds: int = 3600, *, name: str = "ttl") -> YiCacheTTL:
    """Create TTL wrapper for any cache."""
    return YiCacheTTL(maxsize=maxsize, ttl=ttl_seconds, name=name)
