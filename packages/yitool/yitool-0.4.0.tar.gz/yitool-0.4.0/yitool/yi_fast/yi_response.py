from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T")

class YiResponse[T](BaseModel):
    """响应模型"""

    code: int = 0
    message: str = "success"
    data: T | None = None


class R:
    @staticmethod
    def ok(data: Any | None = None, message: str = "success", code: int = 0) -> dict[str, Any]:
        """成功响应"""
        return {"code": code, "message": message, "data": data}

    @staticmethod
    def fail(message: str = "error", code: int = -1, data: Any | None = None) -> dict[str, Any]:
        """错误响应"""
        return {"code": code, "message": message, "data": data}
