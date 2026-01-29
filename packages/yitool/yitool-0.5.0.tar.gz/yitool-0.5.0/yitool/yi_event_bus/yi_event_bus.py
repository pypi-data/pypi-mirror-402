import asyncio
import inspect
from collections.abc import Callable
from typing import Any

from blinker import Namespace

from ._abc import AbcYiEventBus


class YiEventBusException(Exception):
    """YiEventBus自定义异常类，用于事件回调异常处理"""

    def __init__(self, event_name: str, message: str, original_exception: Exception = None):
        self.event_name = event_name
        self.original_exception = original_exception
        super().__init__(f"事件 [{event_name}] 错误: {message}")


class YiEventBus(AbcYiEventBus):
    """
    基于 blinker 封装的轻量级本地事件总线
    提供 on/emit/off/once 核心事件驱动能力，简洁易用
    """

    def __init__(self):
        # 1. 初始化 blinker 命名空间，用于管理所有事件（信号）
        self._namespace = Namespace()
        # 2. 缓存回调函数映射，用于 off 方法移除监听（用户回调 -> blinker 包装回调）
        self._callback_map: dict[str, dict[Callable[..., Any], Callable[..., Any]]] = {}
        # 3. 缓存一次性回调函数，用于 once 方法自动移除
        self._once_callback_map: dict[str, dict[Callable[..., Any], Callable[..., Any]]] = {}

    def _wrap_callback(self, event_name: str, callback: Callable[..., Any], is_once: bool = False) -> Callable[..., Any]:
        """
        包装用户回调函数，适配 blinker 的参数格式（sender, **kwargs）
        :param event_name: 事件名称
        :param callback: 用户传入的回调函数
        :param is_once: 是否为一次性回调
        :return: 包装后的回调函数
        """
        def wrapped_callback(*args: Any, **kwargs: Any) -> None:
            # blinker会传递sender作为位置参数，然后是我们的关键字参数
            # 提取用户自定义的args和kwargs
            user_args = kwargs.get("args", ())
            user_kwargs = kwargs.get("kwargs", {})

            # 执行用户回调函数
            try:
                if inspect.iscoroutinefunction(callback):
                    # 异步回调处理
                    coro = callback(*user_args, **user_kwargs)
                    # 检查当前是否已经在事件循环中
                    try:
                        loop = asyncio.get_running_loop()
                        # 已经在事件循环中，直接提交任务
                        loop.create_task(coro)
                    except RuntimeError:
                        # 不在事件循环中，使用 asyncio.run()
                        asyncio.run(coro)
                else:
                    # 同步回调，直接执行
                    callback(*user_args, **user_kwargs)
            except Exception as e:
                # 使用自定义异常类，并指定原始异常
                raise YiEventBusException(event_name, f"回调执行异常: {str(e)}", e) from e

            # 一次性回调：执行后自动移除监听
            if is_once:
                # 从一次性回调映射中移除
                if event_name in self._once_callback_map and callback in self._once_callback_map[event_name]:
                    wrapped = self._once_callback_map[event_name][callback][0]
                    self._once_callback_map[event_name].pop(callback)
                    if not self._once_callback_map[event_name]:
                        del self._once_callback_map[event_name]
                    # 从信号中断开连接
                    signal = self._namespace.signal(event_name)
                    signal.disconnect(wrapped)

        return wrapped_callback

    def on(self, event_name: str, callback: Callable[..., Any], priority: int = 0) -> None:
        """
        注册事件监听器（永久监听，对应 Node.js on 方法）
        :param event_name: 事件名称
        :param callback: 事件回调函数，接收用户传递的任意参数
        :param priority: 事件优先级，值越小执行顺序越靠前，默认值：0
        """
        if not callable(callback):
            raise TypeError("回调函数必须是可调用对象（Callable）")

        # 1. 获取/创建 blinker 信号（事件对应信号）
        signal = self._namespace.signal(event_name)

        # 2. 包装用户回调，适配 blinker 格式
        wrapped_callback = self._wrap_callback(event_name, callback, is_once=False)

        # 3. 强引用连接信号（避免回调被 Python 垃圾回收）
        signal.connect(wrapped_callback, weak=False)

        # 4. 缓存回调映射，用于后续 off 移除，存储 (wrapped_callback, priority)
        if event_name not in self._callback_map:
            self._callback_map[event_name] = {}
        self._callback_map[event_name][callback] = (wrapped_callback, priority)

    def emit(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        """
        触发事件（对应 Node.js emit 方法）
        :param event_name: 事件名称
        :param args: 位置参数，传递给回调函数
        :param kwargs: 关键字参数，传递给回调函数
        """
        # 获取所有回调函数和优先级
        all_callbacks = []

        # 添加普通监听器
        if event_name in self._callback_map:
            for callback, (wrapped, priority) in self._callback_map[event_name].items():
                all_callbacks.append((priority, wrapped, callback, False))

        # 添加一次性监听器
        if event_name in self._once_callback_map:
            for callback, (wrapped, priority) in self._once_callback_map[event_name].items():
                all_callbacks.append((priority, wrapped, callback, True))

        # 按优先级升序排序，优先级越小执行顺序越靠前
        all_callbacks.sort(key=lambda x: x[0])

        # 执行回调函数
        for _priority, wrapped_callback, original_callback, is_once in all_callbacks:
            # 执行回调
            wrapped_callback(event_name, args=args, kwargs=kwargs)

            # 如果是一次性回调，执行后移除
            if is_once:
                # 从一次性回调映射中移除
                if event_name in self._once_callback_map and original_callback in self._once_callback_map[event_name]:
                    self._once_callback_map[event_name].pop(original_callback)
                    if not self._once_callback_map[event_name]:
                        del self._once_callback_map[event_name]

    def off(self, event_name: str, callback: Callable[..., Any]) -> None:
        """
        移除事件监听器（对应 Node.js off 方法）
        :param event_name: 事件名称
        :param callback: 要移除的回调函数
        """
        removed = False

        # 1. 先检查并移除普通监听器
        if event_name in self._callback_map and callback in self._callback_map[event_name]:
            wrapped_callback, _ = self._callback_map[event_name].pop(callback)
            if not self._callback_map[event_name]:
                del self._callback_map[event_name]

            # 从 blinker 信号中断开连接
            signal = self._namespace.signal(event_name)
            signal.disconnect(wrapped_callback)
            removed = True

        # 2. 如果普通监听器中没有找到，再检查并移除一次性监听器
        if not removed and event_name in self._once_callback_map and callback in self._once_callback_map[event_name]:
            wrapped_callback, _ = self._once_callback_map[event_name].pop(callback)
            if not self._once_callback_map[event_name]:
                del self._once_callback_map[event_name]

            # 从 blinker 信号中断开连接
            signal = self._namespace.signal(event_name)
            signal.disconnect(wrapped_callback)

    def once(self, event_name: str, callback: Callable[..., Any], priority: int = 0) -> None:
        """
        注册一次性事件监听器（仅执行一次，执行后自动移除）
        :param event_name: 事件名称
        :param callback: 事件回调函数
        :param priority: 事件优先级，值越小执行顺序越靠前，默认值：0
        """
        if not callable(callback):
            raise TypeError("回调函数必须是可调用对象（Callable）")

        # 1. 获取/创建 blinker 信号
        signal = self._namespace.signal(event_name)

        # 2. 包装用户回调，标记为一次性
        wrapped_callback = self._wrap_callback(event_name, callback, is_once=True)

        # 3. 强引用连接信号
        signal.connect(wrapped_callback, weak=False)

        # 4. 缓存一次性回调映射，存储 (wrapped_callback, priority)
        if event_name not in self._once_callback_map:
            self._once_callback_map[event_name] = {}
        self._once_callback_map[event_name][callback] = (wrapped_callback, priority)

    def clear(self, event_name: str | None = None) -> None:
        """
        清空事件监听器
        :param event_name: 事件名称，为空则清空所有事件的监听器
        """
        if event_name:
            # 清空指定事件的监听器
            if event_name in self._callback_map:
                signal = self._namespace.signal(event_name)
                for _callback, (wrapped_callback, _) in self._callback_map[event_name].items():
                    signal.disconnect(wrapped_callback)
                del self._callback_map[event_name]

            if event_name in self._once_callback_map:
                signal = self._namespace.signal(event_name)
                for _callback, (wrapped_callback, _) in self._once_callback_map[event_name].items():
                    signal.disconnect(wrapped_callback)
                del self._once_callback_map[event_name]
        else:
            # 清空所有事件的监听器
            for event in list(self._callback_map.keys()):
                self.clear(event)

    def listeners(self, event_name: str) -> int:
        """
        获取事件监听器数量
        :param event_name: 事件名称
        :return: 监听器数量
        """
        regular_count = len(self._callback_map.get(event_name, {}))
        once_count = len(self._once_callback_map.get(event_name, {}))
        return regular_count + once_count


# 创建全局事件总线实例
yi_event_bus = YiEventBus()
