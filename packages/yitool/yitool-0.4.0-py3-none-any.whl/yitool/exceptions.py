from __future__ import annotations

from typing import Any


class YiException(Exception):
    """异常基类"""

    def __init__(self, message: str = "未知错误", code: str = "ERROR", data: Any = None):
        self.message = message
        self.code = code
        self.data = data
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


class YiConfigError(YiException):
    """配置错误异常"""

    def __init__(self, message: str = "配置错误异常", code: str = "CONFIG_ERROR", data: Any = None):
        super().__init__(message, code, data)


class YiFileError(YiException):
    """文件操作异常"""

    def __init__(self, message: str = "文件操作异常", code: str = "FILE_ERROR", data: Any = None):
        super().__init__(message, code, data)


class YiDatabaseError(YiException):
    """数据库操作异常"""

    def __init__(self, message: str = "数据库操作异常", code: str = "DATABASE_ERROR", data: Any = None):
        super().__init__(message, code, data)


class YiRedisError(YiException):
    """Redis操作异常"""

    def __init__(self, message: str = "Redis操作异常", code: str = "REDIS_ERROR", data: Any = None):
        super().__init__(message, code, data)
