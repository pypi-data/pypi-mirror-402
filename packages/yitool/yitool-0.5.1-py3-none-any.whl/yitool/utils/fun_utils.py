from __future__ import annotations

import asyncio
import functools
import inspect
import types
from collections.abc import Callable
from typing import Any


class FunUtils:
    """函数工具类"""

    @staticmethod
    def name(func: Callable) -> str:
        """获取给定函数的名称"""
        if isinstance(func, functools.partial):
            return FunUtils.name(func.func)
        if hasattr(func, "__name__"):
            return func.__name__
        if hasattr(func, "__class__") and hasattr(func.__class__, "__name__"):
            return func.__class__.__name__
        return str(func)

    @staticmethod
    async def is_async(func: Callable) -> bool:
        """检查给定函数是否为异步函数，包括

        协程函数、异步生成器和协程对象。
        """
        return (
            inspect.iscoroutinefunction(func)
            or inspect.isasyncgenfunction(func)
            or isinstance(func, types.CoroutineType)
            or isinstance(func, types.GeneratorType)
            and asyncio.iscoroutine(func)
            or isinstance(func, functools.partial)
            and await FunUtils.is_async(func.func)
        )

    @staticmethod
    async def async_execute(
        func: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        if await FunUtils.is_async(func):
            return await func(*args, **kwargs)
        return func(*args, **kwargs)

    @staticmethod
    def execute(
        func: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        if asyncio.iscoroutinefunction(func):
            loop = asyncio.get_event_loop()
            if loop.is_running():
                coro = func(*args, **kwargs)
                future = asyncio.run_coroutine_threadsafe(coro, loop)
                return future.result()
            else:
                return loop.run_until_complete(func(*args, **kwargs))
        return func(*args, **kwargs)

