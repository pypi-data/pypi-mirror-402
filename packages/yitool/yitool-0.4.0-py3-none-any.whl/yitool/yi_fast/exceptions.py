from fastapi import HTTPException, status


class YiHTTPException(HTTPException):
    """基础HTTP异常类"""

    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class YiNotFoundException(YiHTTPException):
    """资源未找到异常"""

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class YiBadRequestException(YiHTTPException):
    """请求参数错误异常"""

    def __init__(self, detail: str = "Bad request"):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


class YiUnauthorizedException(YiHTTPException):
    """未授权异常"""

    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)


class YiForbiddenException(YiHTTPException):
    """禁止访问异常"""

    def __init__(self, detail: str = "Forbidden"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)


class YiConflictException(YiHTTPException):
    """资源冲突异常"""

    def __init__(self, detail: str = "Conflict"):
        super().__init__(detail=detail, status_code=status.HTTP_409_CONFLICT)


class YiInternalServerErrorException(YiHTTPException):
    """内部服务器错误异常"""

    def __init__(self, detail: str = "Internal server error"):
        super().__init__(detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
