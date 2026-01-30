from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AbcYiSerializer(ABC):
    """序列化器抽象基类，定义统一接口"""

    @abstractmethod
    def serialize(self, obj: Any) -> bytes:
        """序列化对象为字节流

        Args:
            obj: 要序列化的对象

        Returns:
            序列化后的字节流
        """
        pass

    @abstractmethod
    def deserialize(self, data: bytes) -> Any:
        """从字节流反序列化对象

        Args:
            data: 要反序列化的字节流

        Returns:
            反序列化后的对象
        """
        pass

    def dumps(self, obj: Any) -> bytes:
        """序列化别名方法，等同于serialize"""
        return self.serialize(obj)

    def loads(self, data: bytes) -> Any:
        """反序列化别名方法，等同于deserialize"""
        return self.deserialize(data)
