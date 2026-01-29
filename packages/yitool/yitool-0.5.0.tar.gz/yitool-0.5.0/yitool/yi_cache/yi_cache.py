from __future__ import annotations

from enum import Enum

from yitool.yi_cache._abc import AbcYiCache


class YiCacheType(Enum):
    """缓存类型枚举，标识不同的缓存实现"""

    MEMORY = "memory"  # 内存缓存
    REDIS = "redis"    # Redis缓存
    TTL = "ttl"        # TTL缓存


class YiCacheFactory:
    """
    缓存工厂类，统一创建不同类型的缓存实例

    核心功能：
    1. 基于枚举或字符串创建对应缓存实例
    2. 统一管理默认配置和自定义配置
    3. 支持注册新的缓存实现
    """

    # 注册表：映射缓存类型到具体实现类
    _registry: dict[YiCacheType, type[AbcYiCache]] = {
        # 延迟注册，避免循环导入
    }

    # 默认配置：不同缓存类型的默认参数
    _default_configs: dict[YiCacheType, dict] = {
        YiCacheType.MEMORY: {},
        YiCacheType.REDIS: {
            "host": "localhost",
            "port": 6379,
            "db": 0,
        },
        YiCacheType.TTL: {
            "maxsize": 100,
            "ttl": 3600,
            "name": "default_ttl_cache",
        },
    }

    @classmethod
    def create(cls, cache_type: YiCacheType | str, config: dict | None = None) -> AbcYiCache:
        """
        创建缓存实例

        Args:
            cache_type: 缓存类型，可以是枚举或字符串
            config: 自定义配置，会覆盖默认配置

        Returns:
            Cache: 缓存实例
        """
        # 1. 处理输入类型
        if isinstance(cache_type, str):
            try:
                cache_type = YiCacheType(cache_type.lower())
            except ValueError:
                supported_types = [t.value for t in YiCacheType]
                raise ValueError(f"不支持的缓存类型: {cache_type}，支持的类型: {supported_types}") from None

        # 2. 检查类型是否已注册
        if cache_type not in cls._registry:
            # 延迟注册，避免循环导入
            if cache_type == YiCacheType.MEMORY:
                from yitool.yi_cache.yi_cache_memory import YiCacheMemory
                cls.register(YiCacheType.MEMORY, YiCacheMemory)
            elif cache_type == YiCacheType.REDIS:
                from yitool.yi_cache.yi_cache_redis import YiCacheRedis
                cls.register(YiCacheType.REDIS, YiCacheRedis)
            elif cache_type == YiCacheType.TTL:
                from yitool.yi_cache.yi_cache_ttl import YiCacheTTL
                cls.register(YiCacheType.TTL, YiCacheTTL)
            else:
                raise NotImplementedError(f"未注册的缓存类型: {cache_type}")

        # 3. 合并配置
        final_config = cls._default_configs.get(cache_type, {}).copy()
        if config:
            final_config.update(config)

        # 4. 创建实例
        cache_class = cls._registry[cache_type]
        return cache_class(**final_config)

    @classmethod
    def register(cls, cache_type: YiCacheType, cache_class: type[AbcYiCache], default_config: dict | None = None) -> None:
        """
        注册新的缓存实现

        Args:
            cache_type: 缓存类型枚举
            cache_class: 缓存实现类，必须继承自 Cache
            default_config: 默认配置，可选
        """
        if not issubclass(cache_class, AbcYiCache):
            raise TypeError(f"{cache_class.__name__} 必须继承自 Cache 抽象基类")

        cls._registry[cache_type] = cache_class
        if default_config:
            cls._default_configs[cache_type] = default_config

    @classmethod
    def get_supported_types(cls) -> list[str]:
        """
        获取所有支持的缓存类型

        Returns:
            list[str]: 支持的缓存类型列表
        """
        return [t.value for t in cls._registry.keys()]


# 延迟注册各缓存实现，避免循环导入
try:
    from yitool.yi_cache.yi_cache_memory import YiCacheMemory
    YiCacheFactory.register(YiCacheType.MEMORY, YiCacheMemory)
except ImportError:
    pass

try:
    from yitool.yi_cache.yi_cache_redis import YiCacheRedis
    YiCacheFactory.register(YiCacheType.REDIS, YiCacheRedis)
except ImportError:
    pass

try:
    from yitool.yi_cache.yi_cache_ttl import YiCacheTTL
    YiCacheFactory.register(YiCacheType.TTL, YiCacheTTL)
except ImportError:
    pass
