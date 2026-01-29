"""日志装饰器"""

import functools
import time
from collections.abc import Callable
from typing import Any

from yitool.log.context import log_context_decorator
from yitool.log.core import debug, exception, info


def log_function[T](func: Callable[..., T]) -> Callable[..., T]:
    """函数执行日志装饰器

    记录函数的执行开始和结束，包括执行时间

    Args:
        func: 要装饰的函数

    Returns:
        装饰后的函数
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # 记录函数开始执行
        start_time = time.time()
        info(f"开始执行函数: {func.__name__}")

        try:
            # 执行原始函数
            result = func(*args, **kwargs)

            # 记录函数执行成功
            end_time = time.time()
            execution_time = end_time - start_time
            info(f"函数 {func.__name__} 执行成功，耗时: {execution_time:.3f}秒")

            return result
        except Exception:
            # 记录函数执行异常
            end_time = time.time()
            execution_time = end_time - start_time
            exception(f"函数 {func.__name__} 执行失败，耗时: {execution_time:.3f}秒", exc_info=True)
            raise

    return wrapper


def log_execution_time[T](func: Callable[..., T]) -> Callable[..., T]:
    """函数执行时间记录装饰器

    仅记录函数的执行时间，不记录开始和结束信息

    Args:
        func: 要装饰的函数

    Returns:
        装饰后的函数
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        info(f"函数 {func.__name__} 执行耗时: {execution_time:.3f}秒")
        return result

    return wrapper


def log_with_context[U](**context_kwargs: Any) -> Callable[[Callable[..., U]], Callable[..., U]]:
    """带上下文的日志装饰器

    为函数添加指定的日志上下文，并记录函数执行信息

    Args:
        **context_kwargs: 要添加的上下文信息

    Returns:
        装饰器函数
    """
    def decorator(func: Callable[..., U]) -> Callable[..., U]:
        @functools.wraps(func)
        @log_context_decorator(**context_kwargs)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)
        return wrapper
    return decorator


def log_exception[T](func: Callable[..., T] | None = None, *, reraise: bool = True) -> Callable[..., T] | Callable[[Callable[..., T]], Callable[..., T]]:
    """异常捕获日志装饰器

    捕获函数执行过程中的异常，并记录日志，可选择是否重新抛出

    Args:
        func: 要装饰的函数
        reraise: 是否重新抛出异常，默认为True

    Returns:
        装饰后的函数或装饰器
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception:
                exception(f"函数 {func.__name__} 执行异常", exc_info=True)
                if reraise:
                    raise
                return None
        return wrapper

    if func is None:
        return decorator
    return decorator(func)


def log_debug[T](func: Callable[..., T]) -> Callable[..., T]:
    """调试日志装饰器

    仅在DEBUG级别下记录函数执行信息

    Args:
        func: 要装饰的函数

    Returns:
        装饰后的函数
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        from yitool.log.core import global_logger

        if global_logger.logger.isEnabledFor(10):  # DEBUG级别
            start_time = time.time()
            debug(f"开始执行调试函数: {func.__name__}")

            try:
                result = func(*args, **kwargs)
                end_time = time.time()
                debug(f"调试函数 {func.__name__} 执行成功，耗时: {end_time - start_time:.3f}秒")
                return result
            except Exception:
                end_time = time.time()
                debug(f"调试函数 {func.__name__} 执行失败，耗时: {end_time - start_time:.3f}秒", exc_info=True)
                raise

        return func(*args, **kwargs)

    return wrapper
