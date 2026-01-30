from __future__ import annotations

from enum import Enum

from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine

from yitool.yi_db._abc import AbcYiDB


class YiDBType(Enum):
    """数据库类型枚举，标识不同的数据库实现"""

    SQLALCHEMY = "sqlalchemy"  # SQLAlchemy 实现
    # 可扩展其他数据库库实现


class YiDBFactory:
    """
    数据库工厂类，统一创建不同类型的数据库实例

    核心功能：
    1. 基于枚举或字符串创建对应数据库实例
    2. 统一管理默认配置和自定义配置
    3. 支持注册新的数据库实现
    """

    # 注册表：映射数据库类型到具体实现类
    _registry: dict[YiDBType, type[AbcYiDB]] = {
        # 延迟注册，避免循环导入
    }

    # 默认配置：不同数据库类型的默认参数
    _default_configs: dict[YiDBType, dict] = {
        YiDBType.SQLALCHEMY: {},
    }

    @classmethod
    def create(cls, db_type: YiDBType | str, config: dict | None = None, engine: Engine | AsyncEngine | None = None) -> AbcYiDB:
        """
        创建数据库实例

        Args:
            db_type: 数据库类型，可以是枚举或字符串
            config: 自定义配置，会覆盖默认配置
            engine: 已存在的数据库引擎，可选

        Returns:
            AbcYiDB: 数据库实例
        """
        # 1. 处理输入类型
        if db_type is None:
            raise ValueError(f"数据库类型不能为空，支持的类型: {[t.value for t in YiDBType]}")

        if isinstance(db_type, str):
            try:
                db_type = YiDBType(db_type.lower())
            except ValueError:
                supported_types = [t.value for t in YiDBType]
                raise ValueError(f"不支持的数据库类型: {db_type}，支持的类型: {supported_types}") from None

        # 2. 检查类型是否已注册
        if db_type not in cls._registry:
            # 延迟注册，避免循环导入
            if db_type == YiDBType.SQLALCHEMY:
                from yitool.yi_db.yi_db_sqlalchemy import YiDB
                cls.register(YiDBType.SQLALCHEMY, YiDB)

        # 3. 合并配置
        final_config = cls._default_configs.get(db_type, {}).copy()
        if config:
            final_config.update(config)

        # 4. 创建实例
        db_class = cls._registry[db_type]
        if engine:
            return db_class(engine)

        # 5. 如果没有提供engine，尝试使用YiDB.create_engine创建默认引擎
        # 对于SQLAlchemy类型，创建内存数据库引擎
        if db_type == YiDBType.SQLALCHEMY:
            from sqlalchemy.ext.asyncio import create_async_engine
            engine = create_async_engine("sqlite+aiosqlite:///:memory:")
            return db_class(engine)

        # 其他类型需要提供engine
        raise ValueError(f"创建{db_type.value}类型的数据库实例需要提供engine参数")

    @classmethod
    def register(cls, db_type: YiDBType, db_class: type[AbcYiDB], default_config: dict | None = None) -> None:
        """
        注册新的数据库实现

        Args:
            db_type: 数据库类型枚举
            db_class: 数据库实现类，必须继承自 AbcYiDB
            default_config: 默认配置，可选
        """
        if not issubclass(db_class, AbcYiDB):
            raise TypeError(f"{db_class.__name__} 必须继承自 AbcYiDB 抽象基类")

        cls._registry[db_type] = db_class
        if default_config:
            cls._default_configs[db_type] = default_config

    @classmethod
    def get_supported_types(cls) -> list[str]:
        """
        获取所有支持的数据库类型

        Returns:
            list[str]: 支持的数据库类型列表
        """
        return [t.value for t in cls._registry.keys()]


# 延迟注册 YiDB 到工厂类，避免循环导入
try:
    from yitool.yi_db.yi_db_sqlalchemy import YiDB
    YiDBFactory.register(YiDBType.SQLALCHEMY, YiDB)
except ImportError:
    pass
