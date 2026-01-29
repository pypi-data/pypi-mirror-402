from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


class AbcYiEventBus(ABC):
    """YiEventBus抽象基类，定义事件总线的核心接口"""

    @abstractmethod
    def on(self, event_name: str, callback: Callable[..., Any], priority: int = 0) -> None:
        """
        注册事件监听器（永久监听，对应 Node.js on 方法）

        :param event_name: 事件名称
        :param callback: 事件回调函数，接收用户传递的任意参数
        :param priority: 事件优先级，值越小执行顺序越靠前，默认值：0
        :return: None
        """
        pass

    @abstractmethod
    def emit(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        """
        触发事件（对应 Node.js emit 方法）

        :param event_name: 事件名称
        :param args: 位置参数，传递给回调函数
        :param kwargs: 关键字参数，传递给回调函数
        :return: None
        """
        pass

    @abstractmethod
    def off(self, event_name: str, callback: Callable[..., Any]) -> None:
        """
        移除事件监听器（对应 Node.js off 方法）

        :param event_name: 事件名称
        :param callback: 要移除的回调函数
        :return: None
        """
        pass

    @abstractmethod
    def once(self, event_name: str, callback: Callable[..., Any], priority: int = 0) -> None:
        """
        注册一次性事件监听器（仅执行一次，执行后自动移除）

        :param event_name: 事件名称
        :param callback: 事件回调函数
        :param priority: 事件优先级，值越小执行顺序越靠前，默认值：0
        :return: None
        """
        pass

    @abstractmethod
    def clear(self, event_name: str | None = None) -> None:
        """
        清空事件监听器

        :param event_name: 事件名称，为空则清空所有事件的监听器
        :return: None
        """
        pass

    @abstractmethod
    def listeners(self, event_name: str) -> int:
        """
        获取事件监听器数量

        :param event_name: 事件名称
        :return: 监听器数量
        """
        pass
