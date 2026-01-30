from __future__ import annotations

from yitool.yi_cache._abc import AbcYiCache
from yitool.yi_cache.yi_cache import YiCacheFactory, YiCacheType
from yitool.yi_cache.yi_cache_manager import YiCacheManager, yi_cache_manager
from yitool.yi_cache.yi_cache_memory import YiCacheMemory
from yitool.yi_cache.yi_cache_redis import YiCacheRedis
from yitool.yi_cache.yi_cache_ttl import YiCacheTTL
from yitool.yi_cache.yi_redis import YiRedis

__all__ = [
    # 缓存基类
    "AbcYiCache",
    # 内存缓存
    "YiCacheMemory",
    # Redis缓存
    "YiCacheRedis",
    # TTL缓存
    "YiCacheTTL",
    # 缓存类型枚举
    "YiCacheType",
    # 缓存工厂
    "YiCacheFactory",
    # 缓存管理器
    "YiCacheManager",
    # 全局缓存管理器实例
    "yi_cache_manager",
    # Redis工具类
    "YiRedis"
]
