from __future__ import annotations

from typing import Any

from yitool.log import logger
from yitool.yi_cache._abc import AbcYiCache
from yitool.yi_cache.yi_cache_memory import YiCacheMemory


class YiCacheManager:
    """缓存管理器，用于统一管理多个缓存实例"""

    def __init__(self) -> None:
        """初始化缓存管理器"""
        self.caches: dict[str, AbcYiCache] = {}
        # 创建默认的内存缓存实例
        self.register("default", YiCacheMemory())

    def register(self, name: str, cache: AbcYiCache) -> None:
        """注册缓存实例

        Args:
            name: 缓存名称
            cache: 缓存实例
        """
        if not isinstance(cache, AbcYiCache):
            raise TypeError(f"cache must be an instance of Cache, got {type(cache).__name__}")

        self.caches[name] = cache
        logger.info(f"Cache registered: {name}")

    def unregister(self, name: str) -> bool:
        """注销缓存实例

        Args:
            name: 缓存名称

        Returns:
            是否注销成功
        """
        if name in self.caches:
            del self.caches[name]
            logger.info(f"Cache unregistered: {name}")
            return True
        return False

    def get_cache(self, name: str = "default") -> AbcYiCache:
        """获取缓存实例

        Args:
            name: 缓存名称

        Returns:
            缓存实例

        Raises:
            KeyError: 如果缓存实例不存在
        """
        if name not in self.caches:
            raise KeyError(f"Cache not found: {name}")
        return self.caches[name]

    def get(self, key: str, default: Any = None, name: str = "default") -> Any:
        """获取缓存值

        Args:
            key: 缓存键
            default: 默认值
            name: 缓存名称

        Returns:
            缓存值或默认值
        """
        return self.get_cache(name).get(key, default)

    def set(self, key: str, value: Any, expire: int | None = None, name: str = "default") -> bool:
        """设置缓存值

        Args:
            name: 缓存名称
            key: 缓存键
            value: 缓存值
            expire: 过期时间（秒）

        Returns:
            是否设置成功
        """
        return self.get_cache(name).set(key, value, expire)

    def delete(self, key: str, name: str = "default") -> bool:
        """删除缓存值

        Args:
            name: 缓存名称
            key: 缓存键

        Returns:
            是否删除成功
        """
        return self.get_cache(name).delete(key)

    def clear(self, name: str = "default") -> bool:
        """清空缓存

        Args:
            name: 缓存名称

        Returns:
            是否清空成功
        """
        return self.get_cache(name).clear()

    def exists(self, key: str, name: str = "default") -> bool:
        """检查缓存是否存在

        Args:
            name: 缓存名称
            key: 缓存键

        Returns:
            缓存是否存在
        """
        return self.get_cache(name).exists(key)

    def incr(self, key: str, delta: int = 1, name: str = "default") -> int | None:
        """递增缓存值

        Args:
            name: 缓存名称
            key: 缓存键
            delta: 递增步长

        Returns:
            递增后的值，或None如果键不存在或不是数值类型
        """
        return self.get_cache(name).incr(key, delta)

    def decr(self, key: str, delta: int = 1, name: str = "default") -> int | None:
        """递减缓存值

        Args:
            name: 缓存名称
            key: 缓存键
            delta: 递减步长

        Returns:
            递减后的值，或None如果键不存在或不是数值类型
        """
        return self.get_cache(name).decr(key, delta)

    def get_size(self, name: str = "default") -> int:
        """获取缓存大小

        Args:
            name: 缓存名称

        Returns:
            缓存中的键值对数量
        """
        return self.get_cache(name).get_size()

    def get_all_caches(self) -> dict[str, AbcYiCache]:
        """获取所有缓存实例

        Returns:
            所有缓存实例的字典
        """
        return self.caches.copy()

    def clear_all(self) -> None:
        """清空所有缓存"""
        for name in list(self.caches.keys()):
            self.clear(name)
        logger.info("All caches cleared")


# 创建全局的缓存管理器实例
yi_cache_manager = YiCacheManager()
