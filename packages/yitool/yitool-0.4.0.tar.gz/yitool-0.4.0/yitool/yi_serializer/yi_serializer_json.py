from __future__ import annotations

import json
from typing import Any

from yitool.yi_serializer._abc import AbcYiSerializer


class YiSerializerJson(AbcYiSerializer):
    """JSON 序列化器实现

    支持标准JSON序列化和反序列化，提供灵活的配置选项
    """

    def __init__(self, encoding: str = "utf-8", ensure_ascii: bool = False, indent: int | None = None):
        """初始化JSON序列化器

        Args:
            encoding: 编码格式，默认utf-8
            ensure_ascii: 是否确保ASCII字符，默认False（支持中文等非ASCII字符）
            indent: 缩进空格数，默认None（压缩格式）
        """
        self.encoding = encoding
        self.ensure_ascii = ensure_ascii
        self.indent = indent

    def serialize(self, obj: Any) -> bytes:
        """JSON 序列化，将对象转换为JSON字节流

        Args:
            obj: 要序列化的对象，必须是JSON可序列化类型

        Returns:
            序列化后的JSON字节流

        Raises:
            TypeError: 如果对象不可JSON序列化
        """
        json_str = json.dumps(obj, ensure_ascii=self.ensure_ascii, indent=self.indent)
        return json_str.encode(self.encoding)

    def deserialize(self, data: bytes) -> Any:
        """JSON 反序列化，将JSON字节流转换为对象

        Args:
            data: 要反序列化的JSON字节流

        Returns:
            反序列化后的对象

        Raises:
            json.JSONDecodeError: 如果JSON格式无效
        """
        json_str = data.decode(self.encoding)
        return json.loads(json_str)
