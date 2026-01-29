from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


class AbcYiCache(ABC):
    """缓存抽象基类，定义统一的缓存接口"""

    def __init__(self, enable_events: bool = False):
        """初始化缓存

        Args:
            enable_events: 是否启用事件监听机制，默认不启用
        """
        self._enable_events = enable_events
        if self._enable_events:
            self._listeners = {
                "set": [],      # 设置缓存时触发
                "get": [],      # 获取缓存时触发
                "delete": [],   # 删除缓存时触发
                "clear": [],    # 清空缓存时触发
                "expire": [],   # 缓存过期时触发
            }

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """获取缓存值

        Args:
            key: 缓存键
            default: 默认值，如果键不存在则返回

        Returns:
            缓存值或默认值
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any, expire: int | None = None) -> bool:
        """设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间（秒），None表示永不过期

        Returns:
            是否设置成功
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除缓存值

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        pass

    @abstractmethod
    def clear(self) -> bool:
        """清空缓存

        Returns:
            是否清空成功
        """
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """检查缓存是否存在

        Args:
            key: 缓存键

        Returns:
            缓存是否存在
        """
        pass

    @abstractmethod
    def incr(self, key: str, delta: int = 1) -> int | None:
        """递增缓存值

        Args:
            key: 缓存键
            delta: 递增步长

        Returns:
            递增后的值，或None如果键不存在或不是数值类型
        """
        pass

    @abstractmethod
    def decr(self, key: str, delta: int = 1) -> int | None:
        """递减缓存值

        Args:
            key: 缓存键
            delta: 递减步长

        Returns:
            递减后的值，或None如果键不存在或不是数值类型
        """
        pass

    @abstractmethod
    def get_size(self) -> int:
        """获取缓存大小

        Returns:
            缓存中的键值对数量
        """
        pass

    def on(self, event: str, listener: Callable) -> None:
        """注册事件监听器

        Args:
            event: 事件类型，支持 set、get、delete、clear、expire
            listener: 监听器函数，参数根据事件类型不同而不同
        """
        if self._enable_events and hasattr(self, "_listeners") and event in self._listeners:
            self._listeners[event].append(listener)

    def off(self, event: str, listener: Callable) -> None:
        """移除事件监听器

        Args:
            event: 事件类型
            listener: 要移除的监听器函数
        """
        if self._enable_events and hasattr(self, "_listeners") and event in self._listeners and listener in self._listeners[event]:
            self._listeners[event].remove(listener)

    def _emit(self, event: str, *args, **kwargs) -> None:
        """触发事件

        Args:
            event: 事件类型
            *args: 位置参数
            **kwargs: 关键字参数
        """
        if self._enable_events and hasattr(self, "_listeners") and event in self._listeners:
            for listener in self._listeners[event]:
                try:
                    listener(event, *args, **kwargs)
                except Exception:
                    pass
