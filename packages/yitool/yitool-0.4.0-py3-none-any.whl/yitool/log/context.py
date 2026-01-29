"""日志上下文管理"""

import contextvars
from contextlib import contextmanager
from typing import Any

# 使用contextvars支持异步环境
_log_context = contextvars.ContextVar("log_context", default=None)


def get_log_context() -> dict[str, Any]:
    """获取当前日志上下文

    Returns:
        当前日志上下文字典
    """
    context = _log_context.get()
    if context is None:
        context = {}
        _log_context.set(context)
    return context.copy()


def set_log_context(**kwargs) -> None:
    """设置日志上下文

    Args:
        **kwargs: 要设置的上下文键值对
    """
    current_context = _log_context.get()
    new_context = {**current_context, **kwargs}
    _log_context.set(new_context)


def clear_log_context() -> None:
    """清除日志上下文"""
    _log_context.set({})


@contextmanager
def log_context(**kwargs):
    """日志上下文管理器

    用于在特定上下文中添加日志上下文信息，支持异步环境

    Args:
        **kwargs: 上下文键值对

    Example:
        >>> with log_context(user_id=123, request_id='abc123'):
        ...     logger.info('Processing request')
        ...     # 日志会包含user_id和request_id
    """
    # 获取当前上下文
    current_context = _log_context.get()

    # 创建新的上下文
    new_context = {**current_context, **kwargs}

    # 设置新的上下文
    token = _log_context.set(new_context)

    try:
        yield
    finally:
        # 恢复原来的上下文
        _log_context.reset(token)


def log_context_decorator(**context_kwargs):
    """日志上下文装饰器

    用于为函数添加日志上下文信息

    Args:
        **context_kwargs: 上下文键值对

    Example:
        >>> @log_context_decorator(user_id=lambda: get_current_user_id())
        ... def process_request():
        ...     logger.info('Processing request')
        ...     # 日志会包含user_id
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 计算上下文值
            resolved_context = {}
            for key, value in context_kwargs.items():
                if callable(value):
                    resolved_context[key] = value()
                else:
                    resolved_context[key] = value

            # 使用上下文管理器
            with log_context(**resolved_context):
                return func(*args, **kwargs)
        return wrapper
    return decorator
