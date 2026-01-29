from __future__ import annotations

import pickle
from typing import Any

from yitool.yi_serializer._abc import AbcYiSerializer


class YiSerializerPickle(AbcYiSerializer):
    """Pickle 序列化器实现

    支持Python对象的二进制序列化和反序列化，提供灵活的协议版本选项
    """

    def __init__(self, protocol: int = pickle.HIGHEST_PROTOCOL):
        """初始化Pickle序列化器

        Args:
            protocol: Pickle协议版本，默认使用最高版本
            协议版本说明：
            - 0: 原始ASCII协议，向后兼容
            - 1: 老式二进制协议
            - 2: Python 2.3版本引入的新二进制协议
            - 3: Python 3.0版本引入，不兼容Python 2
            - 4: Python 3.4版本引入，优化了大型对象的序列化
            - 5: Python 3.8版本引入，支持缓存pickle数据
        """
        self.protocol = protocol

    def serialize(self, obj: Any) -> bytes:
        """Pickle 序列化，将Python对象转换为二进制字节流

        Args:
            obj: 要序列化的Python对象

        Returns:
            序列化后的二进制字节流

        Raises:
            pickle.PickleError: 如果对象不可Pickle序列化
        """
        return pickle.dumps(obj, protocol=self.protocol)

    def deserialize(self, data: bytes) -> Any:
        """Pickle 反序列化，将二进制字节流转换为Python对象

        Args:
            data: 要反序列化的二进制字节流

        Returns:
            反序列化后的Python对象

        Raises:
            pickle.UnpicklingError: 如果数据格式无效或被篡改
        """
        return pickle.loads(data)
