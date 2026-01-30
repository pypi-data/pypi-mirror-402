from __future__ import annotations

from typing import Any

from yitool.yi_serializer._abc import AbcYiSerializer

# 尝试导入 msgpack，失败时提供友好提示
MSGPACK_AVAILABLE = False
try:
    import msgpack
    MSGPACK_AVAILABLE = True
except ImportError:
    pass


class YiSerializerMsgPack(AbcYiSerializer):
    """MsgPack 序列化器实现

    支持高效的二进制序列化和反序列化，提供灵活的配置选项
    """

    def __init__(self, use_bin_type: bool = True, raw: bool = False):
        """初始化MsgPack序列化器

        Args:
            use_bin_type: 是否使用二进制类型标记，默认True
            raw: 是否返回原始字节流或自动解码为字符串，默认False（自动解码）

        Raises:
            ImportError: 如果msgpack库未安装
        """
        if not MSGPACK_AVAILABLE:
            raise ImportError("msgpack 库未安装，请使用 pip install msgpack 安装")

        self.use_bin_type = use_bin_type
        self.raw = raw

    def serialize(self, obj: Any) -> bytes:
        """MsgPack 序列化，将对象转换为MsgPack二进制字节流

        Args:
            obj: 要序列化的对象

        Returns:
            序列化后的MsgPack二进制字节流

        Raises:
            msgpack.PackValueError: 如果对象不可MsgPack序列化
        """
        return msgpack.packb(obj, use_bin_type=self.use_bin_type)

    def deserialize(self, data: bytes) -> Any:
        """MsgPack 反序列化，将MsgPack二进制字节流转换为对象

        Args:
            data: 要反序列化的MsgPack二进制字节流

        Returns:
            反序列化后的对象

        Raises:
            msgpack.UnpackValueError: 如果数据格式无效
        """
        return msgpack.unpackb(data, raw=self.raw, use_list=True)
