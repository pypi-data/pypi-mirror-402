from __future__ import annotations

# 导出公共API
from yitool.yi_serializer._abc import AbcYiSerializer
from yitool.yi_serializer.decorators import (
    deserialize,
    deserialize_args,
    serialize,
    serialize_args,
    serialize_args_return,
)
from yitool.yi_serializer.yi_serializer import YiSerializerFactory, YiSerializerType
from yitool.yi_serializer.yi_serializer_json import YiSerializerJson
from yitool.yi_serializer.yi_serializer_msgpack import YiSerializerMsgPack
from yitool.yi_serializer.yi_serializer_pickle import YiSerializerPickle

# 导出所有公共类和函数
__all__ = [
    "AbcYiSerializer",
    "YiSerializerFactory",
    "YiSerializerType",
    "YiSerializerJson",
    "YiSerializerMsgPack",
    "YiSerializerPickle",
    "deserialize",
    "deserialize_args",
    "serialize",
    "serialize_args",
    "serialize_args_return",
]

# 初始化注册各序列化器实现，避免循环导入
# JSON序列化器
YiSerializerFactory.register(YiSerializerType.JSON, YiSerializerJson)

# Pickle序列化器
YiSerializerFactory.register(YiSerializerType.PICKLE, YiSerializerPickle)

# MsgPack序列化器
try:
    # 只有在msgpack库可用时才注册，避免ImportError
    from yitool.yi_serializer.yi_serializer_msgpack import MSGPACK_AVAILABLE
    if MSGPACK_AVAILABLE:
        YiSerializerFactory.register(YiSerializerType.MSGPACK, YiSerializerMsgPack)
except ImportError:
    # msgpack库未安装，跳过注册
    pass
