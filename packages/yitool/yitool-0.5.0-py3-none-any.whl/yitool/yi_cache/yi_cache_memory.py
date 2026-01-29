from __future__ import annotations

import time
from collections import OrderedDict, deque
from typing import Any

from yitool.yi_cache._abc import AbcYiCache

# 尝试导入cachetools库，如果没有安装则使用内置实现
CACHETOOLS_AVAILABLE = False
try:
    from cachetools import FIFOCache, LFUCache, LRUCache, TTLCache
    CACHETOOLS_AVAILABLE = True
except ImportError:
    pass


class YiCacheMemory(AbcYiCache):
    """内存缓存实现，支持多种缓存策略"""

    # 支持的缓存策略
    SUPPORTED_STRATEGIES = ["LRU", "LFU", "FIFO", "TTL"]

    def __init__(self, max_size: int = 1000, strategy: str = "LRU", ttl: int | None = None, enable_events: bool = False):
        """初始化内存缓存

        Args:
            max_size: 缓存最大容量
            strategy: 缓存策略，支持 LRU, LFU, FIFO, TTL
            ttl: 过期时间（秒），仅TTL策略有效
            enable_events: 是否启用事件监听机制，默认不启用
        """
        super().__init__(enable_events=enable_events)
        self.max_size = max_size
        self.strategy = strategy.upper()
        self.ttl = ttl

        if self.strategy not in YiCacheMemory.SUPPORTED_STRATEGIES:
            raise ValueError(f"Unsupported strategy: {strategy}. Supported strategies: {', '.join(YiCacheMemory.SUPPORTED_STRATEGIES)}")

        # 创建缓存实例
        self.cache = self._create_cache()
        # 存储每个键的过期时间
        self.expire_times = {}

    def _create_cache(self):
        """根据策略创建缓存实例

        Returns:
            缓存实例
        """
        if CACHETOOLS_AVAILABLE:
            # 使用cachetools库实现
            if self.strategy == "LRU":
                return LRUCache(maxsize=self.max_size)
            elif self.strategy == "LFU":
                return LFUCache(maxsize=self.max_size)
            elif self.strategy == "FIFO":
                return FIFOCache(maxsize=self.max_size)
            elif self.strategy == "TTL":
                return TTLCache(maxsize=self.max_size, ttl=self.ttl or 3600)
        else:
            # 使用内置实现
            if self.strategy == "LRU":
                return OrderedDict()
            elif self.strategy == "FIFO":
                # 优化：使用字典+双向链表的方式实现FIFO，避免线性查找
                return {
                    "items": deque(maxlen=self.max_size),
                    "index": {}
                }
            elif self.strategy == "LFU":
                # 优化：使用更高效的LFU实现，维护访问次数和频率映射
                return {
                    "items": {},  # key: {"value": value, "count": count}
                    "freq": {},   # count: set of keys
                    "min_freq": 0
                }
            elif self.strategy == "TTL":
                return {}

    def _is_expired(self, key: str) -> bool:
        """检查键是否过期

        Args:
            key: 缓存键

        Returns:
            是否过期
        """
        if key not in self.expire_times:
            return False

        expire_time = self.expire_times[key]
        return expire_time is not None and time.time() > expire_time

    def _clean_expired(self):
        """清理过期的键"""
        if self.strategy == "TTL" and not CACHETOOLS_AVAILABLE:
            # 优化：使用更高效的方式清理过期键
            current_time = time.time()
            expired_keys = []
            for key, expire_time in self.expire_times.items():
                if expire_time is not None and current_time > expire_time:
                    expired_keys.append(key)

            for key in expired_keys:
                if key in self.cache:
                    del self.cache[key]
                    del self.expire_times[key]
                    # 触发delete事件
                    self._emit("delete", key)

    def get(self, key: str, default: Any = None) -> Any:
        """获取缓存值"""
        self._clean_expired()

        value = default

        if CACHETOOLS_AVAILABLE:
            value = self.cache.get(key, default)
        else:
            if self.strategy == "LRU":
                if key in self.cache:
                    # 移动到末尾表示最近使用
                    self.cache.move_to_end(key)
                    value = self.cache[key]
            elif self.strategy == "FIFO":
                if key in self.cache["index"]:
                    value = self.cache["index"][key]
            elif self.strategy == "LFU":
                if key in self.cache["items"]:
                    item = self.cache["items"][key]
                    value = item["value"]
                    # 更新访问频率
                    count = item["count"]
                    self.cache["freq"][count].remove(key)
                    if not self.cache["freq"][count]:
                        del self.cache["freq"][count]
                        if count == self.cache["min_freq"]:
                            self.cache["min_freq"] += 1

                    new_count = count + 1
                    if new_count not in self.cache["freq"]:
                        self.cache["freq"][new_count] = set()
                    self.cache["freq"][new_count].add(key)
                    item["count"] = new_count
            elif self.strategy == "TTL":
                if key in self.cache and not self._is_expired(key):
                    value = self.cache[key]

        # 触发get事件
        self._emit("get", key, value)
        return value

    def set(self, key: str, value: Any, expire: int | None = None) -> bool:
        """设置缓存值"""
        self._clean_expired()

        if CACHETOOLS_AVAILABLE:
            self.cache[key] = value
        else:
            if self.strategy == "LRU":
                if key in self.cache:
                    # 先删除旧键，避免容量问题
                    del self.cache[key]
                elif len(self.cache) >= self.max_size:
                    # 删除最旧的项
                    self.cache.popitem(last=False)
                self.cache[key] = value
                # 移动到末尾表示最近使用
                self.cache.move_to_end(key)
            elif self.strategy == "FIFO":
                cache = self.cache
                if key in cache["index"]:
                    # 先删除旧键
                    old_item = (key, cache["index"][key])
                    cache["items"].remove(old_item)
                elif len(cache["items"]) >= self.max_size:
                    # 删除最旧的项
                    old_key, old_value = cache["items"].popleft()
                    del cache["index"][old_key]
                # 添加新键
                cache["items"].append((key, value))
                cache["index"][key] = value
            elif self.strategy == "LFU":
                cache = self.cache
                if key in cache["items"]:
                    # 更新现有键
                    item = cache["items"][key]
                    old_count = item["count"]
                    # 从旧频率集合中移除
                    cache["freq"][old_count].remove(key)
                    if not cache["freq"][old_count]:
                        del cache["freq"][old_count]
                        if old_count == cache["min_freq"]:
                            cache["min_freq"] += 1
                    # 更新值和频率
                    item["value"] = value
                    new_count = old_count + 1
                    if new_count not in cache["freq"]:
                        cache["freq"][new_count] = set()
                    cache["freq"][new_count].add(key)
                    item["count"] = new_count
                else:
                    # 添加新键
                    if len(cache["items"]) >= self.max_size:
                        # 删除访问频率最低的键
                        min_freq_keys = cache["freq"][cache["min_freq"]]
                        if min_freq_keys:
                            least_used_key = min_freq_keys.pop()
                            del cache["items"][least_used_key]
                            if not min_freq_keys:
                                del cache["freq"][cache["min_freq"]]
                    # 添加新键
                    count = 1
                    cache["items"][key] = {"value": value, "count": count}
                    if count not in cache["freq"]:
                        cache["freq"][count] = set()
                    cache["freq"][count].add(key)
                    cache["min_freq"] = 1
            elif self.strategy == "TTL":
                self.cache[key] = value
                if expire is not None:
                    self.expire_times[key] = time.time() + expire
                else:
                    self.expire_times[key] = None

        # 触发set事件
        self._emit("set", key, value, expire)
        return True

    def delete(self, key: str) -> bool:
        """删除缓存值"""
        try:
            success = False
            if CACHETOOLS_AVAILABLE:
                if key in self.cache:
                    del self.cache[key]
                    success = True
            else:
                if self.strategy == "LRU":
                    if key in self.cache:
                        del self.cache[key]
                        success = True
                elif self.strategy == "FIFO":
                    cache = self.cache
                    if key in cache["index"]:
                        value = cache["index"][key]
                        cache["items"].remove((key, value))
                        del cache["index"][key]
                        success = True
                elif self.strategy == "LFU":
                    cache = self.cache
                    if key in cache["items"]:
                        item = cache["items"][key]
                        count = item["count"]
                        # 从频率集合中移除
                        cache["freq"][count].remove(key)
                        if not cache["freq"][count]:
                            del cache["freq"][count]
                            if count == cache["min_freq"]:
                                cache["min_freq"] += 1
                        del cache["items"][key]
                        success = True
                elif self.strategy == "TTL":
                    if key in self.cache:
                        del self.cache[key]
                        if key in self.expire_times:
                            del self.expire_times[key]
                        success = True

            if success:
                # 触发delete事件
                self._emit("delete", key)
            return success
        except Exception:
            return False

    def clear(self) -> bool:
        """清空缓存"""
        try:
            if CACHETOOLS_AVAILABLE:
                self.cache.clear()
            else:
                if self.strategy == "LRU":
                    self.cache.clear()
                elif self.strategy == "FIFO":
                    self.cache["items"].clear()
                    self.cache["index"].clear()
                elif self.strategy == "LFU":
                    self.cache["items"].clear()
                    self.cache["freq"].clear()
                    self.cache["min_freq"] = 0
                elif self.strategy == "TTL":
                    self.cache.clear()
                    self.expire_times.clear()

            # 触发clear事件
            self._emit("clear")
            return True
        except Exception:
            return False

    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        self._clean_expired()

        if CACHETOOLS_AVAILABLE:
            return key in self.cache
        else:
            if self.strategy == "LRU":
                return key in self.cache
            elif self.strategy == "FIFO":
                return key in self.cache["index"]
            elif self.strategy == "LFU":
                return key in self.cache["items"]
            elif self.strategy == "TTL":
                return key in self.cache and not self._is_expired(key)

    def incr(self, key: str, delta: int = 1) -> int | None:
        """递增缓存值"""
        self._clean_expired()

        current = self.get(key)
        if current is None:
            current = 0

        if not isinstance(current, (int, float)):
            return None

        new_value = current + delta
        self.set(key, new_value)
        return new_value

    def decr(self, key: str, delta: int = 1) -> int | None:
        """递减缓存值"""
        return self.incr(key, -delta)

    def get_size(self) -> int:
        """获取缓存大小"""
        self._clean_expired()

        if CACHETOOLS_AVAILABLE:
            return len(self.cache)
        else:
            if self.strategy == "LRU":
                return len(self.cache)
            elif self.strategy == "FIFO":
                return len(self.cache["items"])
            elif self.strategy == "LFU":
                return len(self.cache["items"])
            elif self.strategy == "TTL":
                return len(self.cache)

    def mget(self, keys: list[str]) -> dict[str, Any]:
        """批量获取缓存值

        Args:
            keys: 缓存键列表

        Returns:
            键值对字典
        """
        self._clean_expired()
        result = {}

        for key in keys:
            result[key] = self.get(key)

        return result

    def mset(self, items: dict[str, Any], expire: int | None = None) -> bool:
        """批量设置缓存值

        Args:
            items: 键值对字典
            expire: 过期时间（秒），对所有键生效

        Returns:
            是否成功
        """
        self._clean_expired()

        for key, value in items.items():
            if not self.set(key, value, expire):
                return False

        return True

    def mdelete(self, keys: list[str]) -> int:
        """批量删除缓存值

        Args:
            keys: 缓存键列表

        Returns:
            删除成功的数量
        """
        count = 0
        for key in keys:
            if self.delete(key):
                count += 1
        return count
