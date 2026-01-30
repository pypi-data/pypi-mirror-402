"""YiSingleton - 统一的单例基类"""

import threading
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T", bound="YiSingleton")


class YiSingleton:
    """单例基类，提供统一的单例管理能力
    
    使用方式:
        class MyClass(YiSingleton):
            def _on_initialize(self, name: str):
                self.name = name
        
        # 获取单例实例
        instance = MyClass.instance(name="test")
        
        # 重置单例（用于测试）
        MyClass.reset_instance()
    """

    _instances: dict[type, "YiSingleton"] = {}
    _initialized: dict[type, bool] = {}
    _locks: dict[type, threading.Lock] = {}

    def __init__(self, *args: Any, **kwargs: Any):
        """初始化单例实例
        
        注意：子类应该重写 _on_initialize() 方法而不是 __init__()
        """
        if not self._is_initialized():
            self._on_initialize(*args, **kwargs)
            self._mark_initialized()

    def _on_initialize(self, *args: Any, **kwargs: Any):
        """子类重写此方法实现初始化逻辑
        
        Args:
            *args: 初始化参数
            **kwargs: 初始化关键字参数
        """
        pass

    @classmethod
    def _get_lock(cls: type[T]) -> threading.Lock:
        """获取类级别的锁"""
        if cls not in cls._locks:
            cls._locks[cls] = threading.Lock()
        return cls._locks[cls]

    @classmethod
    def _is_initialized(cls: type[T]) -> bool:
        """检查类是否已初始化"""
        return cls._initialized.get(cls, False)

    @classmethod
    def _mark_initialized(cls: type[T]) -> None:
        """标记类为已初始化"""
        cls._initialized[cls] = True

    @classmethod
    def _mark_uninitialized(cls: type[T]) -> None:
        """标记类为未初始化"""
        cls._initialized[cls] = False

    @classmethod
    def instance(cls: type[T], *args: Any, **kwargs: Any) -> T:
        """获取单例实例
        
        Args:
            *args: 初始化参数（仅在首次初始化时生效）
            **kwargs: 初始化关键字参数（仅在首次初始化时生效）
        
        Returns:
            T: 单例实例
        
        Example:
            >>> instance = MyClass.instance(name="test")
        """
        if cls not in cls._instances:
            with cls._get_lock():
                if cls not in cls._instances:
                    instance = object.__new__(cls)
                    cls._instances[cls] = instance
                    instance.__init__(*args, **kwargs)
                    # 通知实例创建监听器
                    cls._notify_instance_created(instance)
        return cls._instances[cls]

    @classmethod
    def initialize(cls: type[T], *args: Any, **kwargs: Any) -> T:
        """初始化单例实例（显式初始化）
        
        Args:
            *args: 初始化参数
            **kwargs: 初始化关键字参数
        
        Returns:
            T: 单例实例
        
        Raises:
            RuntimeError: 如果实例已经初始化
        
        Example:
            >>> instance = MyClass.initialize(name="test")
        """
        if cls in cls._instances and cls._is_initialized():
            raise RuntimeError(
                f"{cls.__name__} has already been initialized. "
                f"Use {cls.__name__}.instance() to get the existing instance."
            )
        return cls.instance(*args, **kwargs)

    @classmethod
    def reset_instance(cls: type[T]) -> None:
        """重置单例实例（用于测试）
        
        注意：此方法会删除现有实例，下次调用 instance() 时会创建新实例
        
        Example:
            >>> MyClass.reset_instance()
        """
        with cls._get_lock():
            if cls in cls._instances:
                instance = cls._instances[cls]
                if hasattr(instance, "_on_cleanup"):
                    instance._on_cleanup()
                del cls._instances[cls]
            cls._mark_uninitialized()

    @classmethod
    def is_initialized(cls: type[T]) -> bool:
        """检查单例是否已初始化
        
        Returns:
            bool: 是否已初始化
        
        Example:
            >>> if MyClass.is_initialized():
            ...     instance = MyClass.instance()
        """
        return cls in cls._instances and cls._is_initialized()

    @classmethod
    def get_instance(cls: type[T]) -> T | None:
        """获取单例实例（如果已初始化）
        
        Returns:
            T | None: 单例实例，如果未初始化则返回 None
        
        Example:
            >>> instance = MyClass.get_instance()
            >>> if instance is not None:
            ...     print(instance)
        """
        if cls.is_initialized():
            return cls._instances[cls]
        return None

    def _on_cleanup(self) -> None:
        """子类重写此方法实现清理逻辑
        
        当调用 reset_instance() 时会被调用
        """
        pass

    def __new__(cls: type[T], *args: Any, **kwargs: Any) -> T:
        """创建实例（禁止直接实例化）
        
        Raises:
            RuntimeError: 如果直接调用构造函数
        
        Example:
            >>> # 错误用法
            >>> instance = MyClass()  # Raises RuntimeError
            >>> # 正确用法
            >>> instance = MyClass.instance()
        """
        if cls not in cls._instances:
            raise RuntimeError(
                f"Direct instantiation of {cls.__name__} is not allowed. "
                f"Please use {cls.__name__}.instance() to get the singleton instance."
            )
        return cls._instances[cls]

    @classmethod
    def add_instance_listener(cls: type[T], listener: Callable[[T], None]) -> None:
        """添加实例创建监听器
        
        Args:
            listener: 监听器函数，接收实例作为参数
        
        Example:
            >>> def on_instance_created(instance: MyClass):
            ...     print(f"Instance created: {instance}")
            >>> MyClass.add_instance_listener(on_instance_created)
        """
        if not hasattr(cls, "_instance_listeners"):
            cls._instance_listeners = []
        cls._instance_listeners.append(listener)

    @classmethod
    def remove_instance_listener(cls: type[T], listener: Callable[[T], None]) -> None:
        """移除实例创建监听器
        
        Args:
            listener: 要移除的监听器函数
        """
        if hasattr(cls, "_instance_listeners") and listener in cls._instance_listeners:
            cls._instance_listeners.remove(listener)

    @classmethod
    def _notify_instance_created(cls: type[T], instance: T) -> None:
        """通知实例创建事件"""
        if hasattr(cls, "_instance_listeners"):
            for listener in cls._instance_listeners:
                try:
                    listener(instance)
                except Exception as e:
                    import warnings
                    warnings.warn(f"Error in instance listener: {e}", stacklevel=2)
