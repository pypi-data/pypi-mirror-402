from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AbcYiDB(ABC):
    """数据库抽象基类，定义统一的数据库操作接口"""

    @property
    @abstractmethod
    def engine(self) -> Any:
        """获取数据库引擎"""
        pass

    @property
    @abstractmethod
    def closed(self) -> bool:
        """检查连接是否关闭"""
        pass

    @abstractmethod
    def connect(self):
        """连接数据库"""
        pass

    @abstractmethod
    def close(self):
        """关闭数据库连接"""
        pass

    @abstractmethod
    def execute(self, query: str, params: dict[str, Any] | None = None, retry_times: int = 3) -> Any:
        """执行 SQL 查询"""
        pass

    @abstractmethod
    def read(self, query: str, schema_overrides: dict | None = None, retry_times: int = 3) -> list[dict[str, Any]]:
        """从数据库读取数据"""
        pass

    @abstractmethod
    def write(self, data: list[dict[str, Any]] | Any, table_name: str, if_table_exists: str = "append", retry_times: int = 3) -> int:
        """写入数据库表"""
        pass

    @abstractmethod
    def get_session(self) -> Any:
        """获取数据库会话"""
        pass

    @abstractmethod
    def exists(self, table_name: str) -> bool:
        """检查表是否存在"""
        pass

    @abstractmethod
    def columns(self, table_name: str) -> list | None:
        """获取表的所有列"""
        pass

    def __enter__(self):
        """上下文管理器进入，连接数据库"""
        # 调用 connect 方法
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出，关闭数据库连接"""
        # 调用 close 方法
        self.close()
