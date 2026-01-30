"""DB集合

yitool.yi_db 模块提供数据库操作功能，包括 SQLAlchemy ORM 支持（YiDB）和新增的 SQLModel 支持。

SQLModel 支持（新增）：
- YiSQLModelSerializable: SQLModel 基础序列化类，遵循 yitool 标准
- SqlModelUtils: SQLModel 工具类，遵循 yitool utils 静态方法风格
- create_sqlmodel_engine: SQLModel 引擎创建函数

主要组件：
- AbcYiDB: 数据库抽象接口
- YiDB: SQLAlchemy ORM 实现
- YiDBFactory: 数据库工厂，用于创建不同类型的数据库实例
- YiDBType: 数据库类型枚举（SQLAlchemy）
- engine: 引擎创建和会话管理
- session: 会话管理
- base: 基础模块
- mixin: 混入类

SQLModel 支持说明：
SQLModel 是 SQLAlchemy 和 Pydantic 的深度整合方案。yitool 提供 SQLModel 基础类和工具函数，帮助使用者更便捷地定义和使用 SQLModel 模型。

使用方式：
    1. 基础类：继承 YiSQLModelSerializable
    2. 工具函数：使用 SqlModelUtils 静态方法
    3. 引擎创建：使用 create_sqlmodel_engine()

参考示例：
    examples/sqlmodel_example.py

注意事项：
    - sqlmodel 包尚未安装时，LSP 会报错，这是正常的
    - 安装：uv pip install sqlmodel
    - yitool 不提供具体业务模型，使用者根据业务需求自行定义

主要功能：
- ORM 操作（SQLAlchemy）：完整的 ORM 支持
- SQLModel 支持（新增）：SQLModel 基础类和工具函数
- 引擎管理：同步/异步引擎创建
- 会话管理：Session 上下文管理
- 重试机制：自动重试失败的数据库操作
- 批量操作：批量插入和更新优化
- 查询缓存：缓存查询结果

设计原则：
- 工具包定位：提供基础能力，不涉及业务逻辑
- 向后兼容：现有 SQLAlchemy API 保持不变
- 类型安全：支持 mypy strict 模式
"""

from yitool.yi_db._abc import AbcYiDB
from yitool.yi_db.yi_db import YiDBFactory, YiDBType

try:
    from yitool.yi_db.sqlmodel_base import YiSQLModelSerializable  # noqa: F401
    from yitool.yi_db.sqlmodel_utils import SqlModelUtils  # noqa: F401
    _sqlmodel_available = True
except ImportError:
    _sqlmodel_available = False

__all__ = [
    "AbcYiDB",
    "YiDBFactory",
    "YiDBType",
    "base",
    "engine",
    "session",
    "mixin",
]

if _sqlmodel_available:
    __all__.extend(["YiSQLModelSerializable", "SqlModelUtils"])
