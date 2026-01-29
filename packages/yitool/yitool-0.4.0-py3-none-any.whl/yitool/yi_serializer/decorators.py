from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

from yitool.yi_serializer.yi_serializer import YiSerializerFactory, YiSerializerType


def deserialize_args(
    serializer_type: YiSerializerType | str = YiSerializerType.JSON,
    param_indices: list[int] | None = None,
    param_names: list[str] | None = None,
    **config: Any
) -> Callable:
    """
    装饰器：自动反序列化函数的输入参数

    Args:
        serializer_type: 序列化器类型，支持枚举或字符串
        param_indices: 需要反序列化的位置参数索引列表
        param_names: 需要反序列化的关键字参数名称列表
        **config: 序列化器配置参数

    Returns:
        装饰后的函数，输入参数已反序列化
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 创建序列化器实例
            serializer = YiSerializerFactory.create(serializer_type, config)

            # 处理位置参数
            new_args = list(args)
            if param_indices:
                for idx in param_indices:
                    if idx < len(new_args):
                        new_args[idx] = serializer.deserialize(new_args[idx])

            # 处理关键字参数
            new_kwargs = kwargs.copy()
            if param_names:
                for name in param_names:
                    if name in new_kwargs:
                        new_kwargs[name] = serializer.deserialize(new_kwargs[name])

            # 调用原函数
            return func(*new_args, **new_kwargs)
        return wrapper
    return decorator


def serialize_args(
    serializer_type: YiSerializerType | str = YiSerializerType.JSON,
    param_indices: list[int] | None = None,
    param_names: list[str] | None = None,
    **config: Any
) -> Callable:
    """
    装饰器：自动序列化函数的输入参数

    Args:
        serializer_type: 序列化器类型，支持枚举或字符串
        param_indices: 需要序列化的位置参数索引列表
        param_names: 需要序列化的关键字参数名称列表
        **config: 序列化器配置参数

    Returns:
        装饰后的函数，输入参数已序列化
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 创建序列化器实例
            serializer = YiSerializerFactory.create(serializer_type, config)

            # 处理位置参数
            new_args = list(args)
            if param_indices:
                for idx in param_indices:
                    if idx < len(new_args):
                        new_args[idx] = serializer.serialize(new_args[idx])

            # 处理关键字参数
            new_kwargs = kwargs.copy()
            if param_names:
                for name in param_names:
                    if name in new_kwargs:
                        new_kwargs[name] = serializer.serialize(new_kwargs[name])

            # 调用原函数
            return func(*new_args, **new_kwargs)
        return wrapper
    return decorator


def serialize(
    serializer_type: YiSerializerType | str = YiSerializerType.JSON,
    **config: Any
) -> Callable:
    """
    装饰器：自动序列化函数的返回值

    Args:
        serializer_type: 序列化器类型，支持枚举或字符串
        **config: 序列化器配置参数

    Returns:
        装饰后的函数，返回值为序列化后的字节流
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> bytes:
            # 调用原函数获取返回值
            result = func(*args, **kwargs)
            # 创建序列化器实例
            serializer = YiSerializerFactory.create(serializer_type, config)
            # 序列化返回值
            return serializer.serialize(result)
        return wrapper
    return decorator


def deserialize(
    serializer_type: YiSerializerType | str = YiSerializerType.JSON,
    **config: Any
) -> Callable:
    """
    装饰器：自动反序列化函数的返回值

    Args:
        serializer_type: 序列化器类型，支持枚举或字符串
        **config: 序列化器配置参数

    Returns:
        装饰后的函数，返回值为反序列化后的Python对象
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 调用原函数获取返回值
            result = func(*args, **kwargs)
            # 创建序列化器实例
            serializer = YiSerializerFactory.create(serializer_type, config)
            # 反序列化返回值
            return serializer.deserialize(result)
        return wrapper
    return decorator


def serialize_args_return(
    input_type: YiSerializerType | str = YiSerializerType.JSON,
    output_type: YiSerializerType | str = YiSerializerType.JSON,
    input_config: dict[str, Any] | None = None,
    output_config: dict[str, Any] | None = None,
    param_indices: list[int] | None = None,
    param_names: list[str] | None = None
) -> Callable:
    """
    装饰器：组合反序列化输入参数和序列化返回值

    Args:
        input_type: 输入参数序列化器类型
        output_type: 返回值序列化器类型
        input_config: 输入序列化器配置
        output_config: 输出序列化器配置
        param_indices: 需要反序列化的位置参数索引列表
        param_names: 需要反序列化的关键字参数名称列表

    Returns:
        装饰后的函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> bytes:
            # 1. 创建输入序列化器并反序列化输入参数
            input_serializer = YiSerializerFactory.create(input_type, input_config or {})

            # 处理位置参数
            new_args = list(args)
            if param_indices:
                for idx in param_indices:
                    if idx < len(new_args):
                        new_args[idx] = input_serializer.deserialize(new_args[idx])

            # 处理关键字参数
            new_kwargs = kwargs.copy()
            if param_names:
                for name in param_names:
                    if name in new_kwargs:
                        new_kwargs[name] = input_serializer.deserialize(new_kwargs[name])

            # 2. 执行原函数
            result = func(*new_args, **new_kwargs)

            # 3. 创建输出序列化器并序列化返回值
            output_serializer = YiSerializerFactory.create(output_type, output_config or {})
            return output_serializer.serialize(result)
        return wrapper
    return decorator
