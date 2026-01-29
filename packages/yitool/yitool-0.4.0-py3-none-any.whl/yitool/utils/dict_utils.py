from __future__ import annotations

from typing import Any


class DictUtils:
    """字典工具类"""

    @staticmethod
    def is_empty(d: dict | None) -> bool:
        """检查字典是否为空或None。"""
        return d is None or len(d) == 0

    @staticmethod
    def safe(d: dict | None) -> dict:
        """确保输入是字典，如果是None则返回空字典。"""
        return d if d is not None else {}

    @staticmethod
    def get_value_case_insensitive(d: dict, key: str, default: Any = None) -> Any:
        """以不区分大小写的方式从字典中获取值。"""
        if DictUtils.is_empty(d):
            return default
        for k, v in d.items():
            if isinstance(k, str) and k.lower() == key.lower():
                return v
        return default

    @staticmethod
    def get_value_or_raise(d: dict, key: str) -> Any:
        """如果键存在则从字典中获取值，否则引发KeyError。"""
        if key in d:
            return d[key]
        raise KeyError(f"Key not found: {key}")

    @staticmethod
    def get(d: dict | None, key: str, default: Any = None, insensitive: bool = False) -> Any:
        """如果键存在则从字典中获取值，否则返回默认值。"""
        if d is None:
            return default
        if insensitive:
            return DictUtils.get_value_case_insensitive(d, key, default)
        return d.get(key, default)

    @staticmethod
    def set(d: dict | None, key: str, value: Any) -> None:
        """在字典中设置值。"""
        if d is None:
            raise ValueError("Cannot set value on a None dictionary.")
        d[key] = value

    @staticmethod
    def delete(d: dict | None, key: str) -> None:
        """如果键存在则从字典中删除键。"""
        if d is None:
            return
        if key in d:
            del d[key]

    @staticmethod
    def shallow_merge(base: dict | None, override: dict | None) -> dict:
        """浅合并两个字典，'override'的值优先。"""
        base = DictUtils.safe(base)
        override = DictUtils.safe(override)
        merged = base.copy()
        merged.update(override)
        return merged

    @staticmethod
    def deep_merge(base: dict | None, override: dict | None) -> dict:
        """深合并两个字典，'override'的值优先。"""
        base = DictUtils.safe(base)
        override = DictUtils.safe(override)

        def _merge(a: Any, b: Any) -> Any:
            """递归合并两个值"""
            # 如果b不是字典，直接返回b（覆盖）
            if not isinstance(b, dict):
                return b

            # 如果a不是字典，返回b（覆盖）
            if not isinstance(a, dict):
                return b

            # 都为字典，递归合并
            result = a.copy()
            for key, value in b.items():
                if key in result:
                    result[key] = _merge(result[key], value)
                else:
                    result[key] = value
            return result

        return _merge(base, override)
