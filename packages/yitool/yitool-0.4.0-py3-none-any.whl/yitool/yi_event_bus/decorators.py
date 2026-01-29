from collections.abc import Callable
from functools import wraps
from typing import Any

from .yi_event_bus import YiEventBus, yi_event_bus


def on_event(event_name: str, priority: int = 0, bus: YiEventBus | None = None):
    """
    装饰器：将函数注册为事件监听器

    :param event_name: 事件名称
    :param priority: 事件优先级，值越小执行顺序越靠前，默认值：0
    :param bus: 事件总线实例，默认使用全局event_bus
    :return: 装饰后的函数
    """
    _bus = bus or yi_event_bus

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        # 注册事件监听器
        _bus.on(event_name, func, priority=priority)

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        return wrapper

    return decorator


def once_event(event_name: str, priority: int = 0, bus: YiEventBus | None = None):
    """
    装饰器：将函数注册为一次性事件监听器

    :param event_name: 事件名称
    :param priority: 事件优先级，值越小执行顺序越靠前，默认值：0
    :param bus: 事件总线实例，默认使用全局event_bus
    :return: 装饰后的函数
    """
    _bus = bus or yi_event_bus

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        # 注册一次性事件监听器
        _bus.once(event_name, func, priority=priority)

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        return wrapper

    return decorator


def emit_event(
    event_name: str,
    before: bool = True,
    after: bool = True,
    bus: YiEventBus | None = None
):
    """
    装饰器：在函数执行前后触发事件

    :param event_name: 事件名称
    :param before: 是否在函数执行前触发事件，默认值：True
    :param after: 是否在函数执行后触发事件，默认值：True
    :param bus: 事件总线实例，默认使用全局event_bus
    :return: 装饰后的函数
    """
    _bus = bus or yi_event_bus

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # 函数执行前触发事件
            if before:
                _bus.emit(f"{event_name}.before", *args, **kwargs)

            # 执行原始函数
            result = func(*args, **kwargs)

            # 函数执行后触发事件
            if after:
                _bus.emit(f"{event_name}.after", result, *args, **kwargs)

            return result

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # 函数执行前触发事件
            if before:
                _bus.emit(f"{event_name}.before", *args, **kwargs)

            # 执行原始异步函数
            result = await func(*args, **kwargs)

            # 函数执行后触发事件
            if after:
                _bus.emit(f"{event_name}.after", result, *args, **kwargs)

            return result

        # 根据原始函数类型返回相应的包装函数
        if hasattr(func, "__code__") and "async def" in func.__code__.co_flags.__repr__():
            return async_wrapper

        # 对于使用@asyncio.coroutine装饰的函数
        if hasattr(func, "__code__") and hasattr(func, "__name__"):
            import inspect
            if inspect.iscoroutinefunction(func):
                return async_wrapper

        return sync_wrapper

    return decorator


def on_event_before(event_name: str, priority: int = 0, bus: YiEventBus | None = None):
    """
    装饰器：将函数注册为事件监听器，事件名称自动添加.before后缀

    :param event_name: 事件名称
    :param priority: 事件优先级，值越小执行顺序越靠前，默认值：0
    :param bus: 事件总线实例，默认使用全局event_bus
    :return: 装饰后的函数
    """
    return on_event(f"{event_name}.before", priority=priority, bus=bus)


def on_event_after(event_name: str, priority: int = 0, bus: YiEventBus | None = None):
    """
    装饰器：将函数注册为事件监听器，事件名称自动添加.after后缀

    :param event_name: 事件名称
    :param priority: 事件优先级，值越小执行顺序越靠前，默认值：0
    :param bus: 事件总线实例，默认使用全局event_bus
    :return: 装饰后的函数
    """
    return on_event(f"{event_name}.after", priority=priority, bus=bus)
