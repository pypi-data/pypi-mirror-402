from __future__ import annotations

import json
import threading
from typing import Any, TypeVar

import cachetools

from yitool.log import logger
from yitool.yi_cache._abc import AbcYiCache
from yitool.yi_cache.yi_redis import YiRedis

KT = TypeVar("KT")
VT = TypeVar("VT")

# 尝试导入更高效的序列化库
MSGPACK_AVAILABLE = False
try:
    import msgpack
    MSGPACK_AVAILABLE = True
except ImportError:
    pass

PICKLE_AVAILABLE = False
try:
    import pickle
    PICKLE_AVAILABLE = True
except ImportError:
    pass

class YiCacheTTL[KT, VT](cachetools.TTLCache, AbcYiCache):
    """带过期时间的缓存类，支持本地内存缓存和Redis持久化"""

    def __init__(self, maxsize: int, ttl: int, name: str, redis: YiRedis | None = None, enable_events: bool = False,
                 serializer: str = "json", lazy_load: bool = False):
        """初始化缓存

        Args:
            maxsize: 缓存最大容量
            ttl: 缓存过期时间（秒）
            name: 缓存名称，用于Redis键前缀
            redis: YiRedis实例，用于持久化缓存
            enable_events: 是否启用事件监听机制，默认不启用
            serializer: 序列化器类型，支持json、msgpack、pickle，默认json
            lazy_load: 是否延迟从Redis加载数据，默认False
        """
        # 先调用AbcYiCache的__init__来初始化_listeners
        AbcYiCache.__init__(self, enable_events=enable_events)
        # 再调用cachetools.TTLCache的__init__
        cachetools.TTLCache.__init__(self, maxsize, ttl)
        self._name = name
        self._redis = redis
        self._serializer = serializer.lower()
        self._lazy_load = lazy_load

        # 优化锁设计，使用更细粒度的锁
        self._local_lock = threading.RLock()  # 本地缓存操作锁
        self._redis_lock = threading.RLock()  # Redis操作锁

        # 设置序列化/反序列化函数
        self._setup_serializers()

        # 初始化时从Redis加载已有数据，或延迟加载
        if self.has_redis and not self._lazy_load:
            try:
                self._load_from_redis()
            except Exception as e:
                logger.error(f"Failed to load cache from Redis: {e}")

    def _setup_serializers(self):
        """设置序列化和反序列化函数"""
        if self._serializer == "msgpack" and MSGPACK_AVAILABLE:
            self._serialize = msgpack.packb
            self._deserialize = msgpack.unpackb
        elif self._serializer == "pickle" and PICKLE_AVAILABLE:
            self._serialize = pickle.dumps
            self._deserialize = pickle.loads
        else:
            # 默认使用json
            self._serialize = json.dumps
            self._deserialize = json.loads

    @property
    def name(self) -> str:
        return self._name

    @property
    def has_redis(self) -> bool:
        return self._redis is not None and isinstance(self._redis, YiRedis)

    def _redis_key(self, key: KT) -> str:
        """生成Redis中的键名"""
        return f"{self.name}:{key}"

    def _serialize_value(self, value: VT) -> Any:
        """序列化值以便存储到Redis"""
        try:
            return self._serialize(value)
        except Exception as e:
            logger.warning(f"Failed to serialize value: {value}, error: {e}")
            # 降级到字符串序列化
            return str(value)

    def _deserialize_value(self, value: Any) -> VT:
        """反序列化Redis中的值"""
        if value is None:
            return None

        if isinstance(value, bytes):
            try:
                return self._deserialize(value)
            except Exception:
                # 尝试解码为字符串后再反序列化
                value = value.decode("utf-8")

        try:
            return self._deserialize(value)
        except Exception:
            # 降级处理
            return value

    def _load_from_redis(self) -> None:
        """从Redis加载缓存数据，优化为批量加载和更细粒度的锁"""
        if not self.has_redis:
            return

        pattern = f"{self.name}:*"
        cursor = 0

        # 先批量获取所有键，减少Redis交互次数
        all_keys = []
        while True:
            cursor, keys = self._redis.scan(cursor=cursor, match=pattern, count=1000)  # 增加每次扫描的数量
            all_keys.extend(keys)
            if cursor == 0:
                break

        if not all_keys:
            return

        # 批量获取所有值，减少Redis交互次数
        try:
            with self._redis_lock:
                pipe = self._redis.pipeline()
                for key in all_keys:
                    pipe.get(key)
                values = pipe.execute()

            # 批量加载到本地缓存，减少锁持有时间
            with self._local_lock:
                # 使用 strict=True 确保 all_keys 和 values 长度匹配
                for key, value in zip(all_keys, values, strict=True):
                    if value is not None:
                        try:
                            original_key = key.decode("utf-8").replace(f"{self.name}:", "", 1)
                            super().__setitem__(original_key, self._deserialize_value(value))
                        except Exception as e:
                            logger.error(f"Failed to load key {key} from Redis: {e}")
        except Exception as e:
            logger.error(f"Failed to batch load from Redis: {e}")

    def _lazy_load_key(self, key: KT) -> VT | None:
        """延迟加载单个键，仅在需要时从Redis获取"""
        if not self.has_redis:
            return None

        try:
            with self._redis_lock:
                redis_key = self._redis_key(key)
                value = self._redis.get(redis_key)

            if value is not None:
                deserialized_value = self._deserialize_value(value)
                with self._local_lock:
                    super().__setitem__(key, deserialized_value)
                return deserialized_value
        except Exception as e:
            logger.error(f"Failed to lazy load key {key} from Redis: {e}")

        return None

    def __setitem__(self, key: KT, value: VT) -> None:
        # 先更新本地缓存
        with self._local_lock:
            super().__setitem__(key, value)

        # 异步更新Redis，减少锁持有时间
        if self.has_redis:
            try:
                with self._redis_lock:
                    redis_key = self._redis_key(key)
                    serialized_value = self._serialize_value(value)
                    self._redis.set(redis_key, serialized_value, ex=self.ttl)
            except Exception as e:
                logger.error(f"Failed to set cache to Redis for key {key}: {e}")

    def __getitem__(self, key: KT) -> VT:
        # 先尝试从本地缓存获取，使用细粒度锁
        try:
            with self._local_lock:
                return super().__getitem__(key)
        except KeyError:
            # 本地缓存不存在，尝试延迟加载
            if self.has_redis:
                value = self._lazy_load_key(key)
                if value is not None:
                    return value
            # 都不存在，抛出KeyError
            raise

    def __delitem__(self, key: KT) -> None:
        # 先删除本地缓存
        with self._local_lock:
            super().__delitem__(key)

        # 异步删除Redis中的值，减少锁持有时间
        if self.has_redis:
            try:
                with self._redis_lock:
                    redis_key = self._redis_key(key)
                    self._redis.delete(redis_key)
            except Exception as e:
                logger.error(f"Failed to delete cache from Redis for key {key}: {e}")

    def __contains__(self, key: object) -> bool:
        # 先检查本地缓存
        with self._local_lock:
            if super().__contains__(key):
                return True

        # 本地缓存不存在，检查Redis
        if self.has_redis:
            try:
                with self._redis_lock:
                    redis_key = self._redis_key(key)
                    return self._redis.exists(redis_key)
            except Exception as e:
                logger.error(f"Failed to check cache existence in Redis for key {key}: {e}")
                return False

        return False

    def get(self, key: str, default: Any = None) -> Any:
        """获取缓存值"""
        try:
            with self._local_lock:
                value = super().__getitem__(key)
            self._emit("get", key, value)
            return value
        except KeyError:
            # 尝试延迟加载
            if self.has_redis:
                value = self._lazy_load_key(key)
                if value is not None:
                    self._emit("get", key, value)
                    return value
            self._emit("get", key, default)
            return default

    def set(self, key: str, value: Any, expire: int | None = None) -> bool:
        """设置缓存值"""
        # 先更新本地缓存
        with self._local_lock:
            super().__setitem__(key, value)
        self._emit("set", key, value, expire)

        # 异步更新Redis
        if self.has_redis:
            try:
                with self._redis_lock:
                    redis_key = self._redis_key(key)
                    serialized_value = self._serialize_value(value)
                    if expire is None:
                        self._redis.set(redis_key, serialized_value, ex=self.ttl)
                    else:
                        self._redis.set(redis_key, serialized_value, ex=expire)
            except Exception as e:
                logger.error(f"Failed to set cache to Redis for key {key}: {e}")
        return True

    def delete(self, key: str) -> bool:
        """删除缓存值"""
        try:
            with self._local_lock:
                super().__delitem__(key)
            self._emit("delete", key)

            # 异步删除Redis中的值
            if self.has_redis:
                try:
                    with self._redis_lock:
                        redis_key = self._redis_key(key)
                        self._redis.delete(redis_key)
                except Exception as e:
                    logger.error(f"Failed to delete cache from Redis for key {key}: {e}")
            return True
        except KeyError:
            return False

    def clear(self) -> bool:
        """清空所有缓存"""
        # 先清空本地缓存
        with self._local_lock:
            super().clear()
        self._emit("clear")

        # 异步清空Redis缓存
        if self.has_redis:
            try:
                with self._redis_lock:
                    pattern = f"{self.name}:*"
                    self._redis.clear(pattern)
            except Exception as e:
                logger.error(f"Failed to clear cache in Redis: {e}")
        return True

    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        return key in self

    def incr(self, key: str, delta: int = 1) -> int | None:
        """递增缓存值"""
        with self._local_lock:
            try:
                current = super().__getitem__(key)
                if not isinstance(current, (int, float)):
                    return None
                new_value = current + delta
                super().__setitem__(key, new_value)
                self._emit("set", key, new_value)
            except KeyError:
                new_value = delta
                super().__setitem__(key, new_value)
                self._emit("set", key, new_value)

        # 异步更新Redis
        if self.has_redis:
            try:
                with self._redis_lock:
                    redis_key = self._redis_key(key)
                    serialized_value = self._serialize_value(new_value)
                    self._redis.set(redis_key, serialized_value, ex=self.ttl)
            except Exception as e:
                logger.error(f"Failed to incr cache in Redis for key {key}: {e}")

        return new_value

    def decr(self, key: str, delta: int = 1) -> int | None:
        """递减缓存值"""
        return self.incr(key, -delta)

    def get_size(self) -> int:
        """获取缓存大小"""
        with self._local_lock:
            return len(self)

    def mget(self, keys: list[str]) -> dict[str, Any]:
        """批量获取缓存值"""
        result = {}
        keys_to_load = []

        # 先从本地缓存获取
        with self._local_lock:
            for key in keys:
                try:
                    result[key] = super().__getitem__(key)
                except KeyError:
                    keys_to_load.append(key)

        # 延迟加载缺失的键
        if keys_to_load and self.has_redis:
            try:
                with self._redis_lock:
                    pipe = self._redis.pipeline()
                    for key in keys_to_load:
                        redis_key = self._redis_key(key)
                        pipe.get(redis_key)
                    values = pipe.execute()

                # 更新本地缓存
                with self._local_lock:
                    # 使用 strict=True 确保 keys_to_load 和 values 长度匹配
                    for key, value in zip(keys_to_load, values, strict=True):
                        if value is not None:
                            deserialized_value = self._deserialize_value(value)
                            super().__setitem__(key, deserialized_value)
                            result[key] = deserialized_value
            except Exception as e:
                logger.error(f"Failed to mget from Redis: {e}")

        # 触发事件
        for key in keys:
            self._emit("get", key, result.get(key))

        return result

    def mset(self, items: dict[str, Any], expire: int | None = None) -> bool:
        """批量设置缓存值"""
        # 先更新本地缓存
        with self._local_lock:
            for key, value in items.items():
                super().__setitem__(key, value)

        # 触发事件
        for key, value in items.items():
            self._emit("set", key, value, expire)

        # 异步批量更新Redis
        if self.has_redis:
            try:
                with self._redis_lock:
                    pipe = self._redis.pipeline()
                    for key, value in items.items():
                        redis_key = self._redis_key(key)
                        serialized_value = self._serialize_value(value)
                        if expire is None:
                            pipe.set(redis_key, serialized_value, ex=self.ttl)
                        else:
                            pipe.setex(redis_key, expire, serialized_value)
                    pipe.execute()
            except Exception as e:
                logger.error(f"Failed to mset to Redis: {e}")
                return False

        return True

    def _emit(self, event: str, *args, **kwargs) -> None:
        """触发事件"""
        AbcYiCache._emit(self, event, *args, **kwargs)
