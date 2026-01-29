from __future__ import annotations

from enum import Enum
from typing import Any

from yitool.yi_serializer._abc import AbcYiSerializer


class YiSerializerType(Enum):
    """序列化器类型枚举，标识不同的序列化实现"""

    JSON = "json"       # JSON序列化器
    MSGPACK = "msgpack" # MsgPack序列化器
    PICKLE = "pickle"   # Pickle序列化器


class YiSerializerFactory:
    """
    序列化器工厂类，统一创建不同类型的序列化器实例

    核心功能：
    1. 基于枚举或字符串创建对应序列化器实例
    2. 统一管理默认配置和自定义配置
    3. 支持注册新的序列化实现
    4. 提供便捷的创建方法
    """

    # 注册表：映射序列化器类型到具体实现类
    _registry: dict[YiSerializerType, type[AbcYiSerializer]] = {
        # 延迟注册，避免循环导入
    }

    # 默认配置：不同序列化器类型的默认参数
    _default_configs: dict[YiSerializerType, dict[str, Any]] = {
        YiSerializerType.JSON: {
            "encoding": "utf-8",
            "ensure_ascii": False,
            "indent": None
        },
        YiSerializerType.MSGPACK: {
            "use_bin_type": True,
            "raw": False
        },
        YiSerializerType.PICKLE: {
            "protocol": -1  # 表示使用最高协议版本
        },
    }

    @classmethod
    def create(cls, serializer_type: YiSerializerType | str, config: dict[str, Any] | None = None) -> AbcYiSerializer:
        """
        创建序列化器实例

        Args:
            serializer_type: 序列化器类型，可以是枚举或字符串
            config: 自定义配置，会覆盖默认配置

        Returns:
            AbcYiSerializer: 序列化器实例
        """
        # 1. 处理输入类型
        if isinstance(serializer_type, str):
            try:
                serializer_type = YiSerializerType(serializer_type.lower())
            except ValueError:
                supported_types = [t.value for t in YiSerializerType]
                raise ValueError(f"不支持的序列化器类型: {serializer_type}，支持的类型: {supported_types}") from None

        # 2. 检查类型是否已注册
        if serializer_type not in cls._registry:
            raise NotImplementedError(f"未注册的序列化器类型: {serializer_type}")

        # 3. 合并配置
        final_config = cls._default_configs.get(serializer_type, {}).copy()
        if config:
            final_config.update(config)

        # 4. 创建实例
        serializer_class = cls._registry[serializer_type]
        return serializer_class(**final_config)

    @classmethod
    def register(cls, serializer_type: YiSerializerType, serializer_class: type[AbcYiSerializer], default_config: dict[str, Any] | None = None) -> None:
        """
        注册新的序列化器实现

        Args:
            serializer_type: 序列化器类型枚举
            serializer_class: 序列化器实现类，必须继承自 AbcYiSerializer
            default_config: 默认配置，可选
        """
        if not issubclass(serializer_class, AbcYiSerializer):
            raise TypeError(f"{serializer_class.__name__} 必须继承自 AbcYiSerializer 抽象基类")

        cls._registry[serializer_type] = serializer_class
        if default_config:
            cls._default_configs[serializer_type] = default_config

    @classmethod
    def get_supported_types(cls) -> list[str]:
        """
        获取所有支持的序列化器类型

        Returns:
            list[str]: 支持的序列化器类型列表
        """
        return [t.value for t in cls._registry.keys()]

    @classmethod
    def create_json_serializer(cls, encoding: str = "utf-8", ensure_ascii: bool = False, indent: int | None = None) -> Any:
        """
        直接创建JSON序列化器实例（更简洁的API）

        Args:
            encoding: 编码格式，默认utf-8
            ensure_ascii: 是否确保ASCII字符，默认False
            indent: 缩进空格数，默认None

        Returns:
            YiSerializerJson: JSON序列化器实例
        """
        from yitool.yi_serializer.yi_serializer_json import YiSerializerJson
        return YiSerializerJson(encoding=encoding, ensure_ascii=ensure_ascii, indent=indent)

    @classmethod
    def create_msgpack_serializer(cls, use_bin_type: bool = True, raw: bool = False) -> Any:
        """
        直接创建MsgPack序列化器实例（更简洁的API）

        Args:
            use_bin_type: 是否使用二进制类型标记，默认True
            raw: 是否返回原始字节流，默认False

        Returns:
            YiSerializerMsgPack: MsgPack序列化器实例
        """
        from yitool.yi_serializer.yi_serializer_msgpack import YiSerializerMsgPack
        return YiSerializerMsgPack(use_bin_type=use_bin_type, raw=raw)

    @classmethod
    def create_pickle_serializer(cls, protocol: int = -1) -> Any:
        """
        直接创建Pickle序列化器实例（更简洁的API）

        Args:
            protocol: Pickle协议版本，默认使用最高版本

        Returns:
            YiSerializerPickle: Pickle序列化器实例
        """
        from yitool.yi_serializer.yi_serializer_pickle import YiSerializerPickle
        return YiSerializerPickle(protocol=protocol)
