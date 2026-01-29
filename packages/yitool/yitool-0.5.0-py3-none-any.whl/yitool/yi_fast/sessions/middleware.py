from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .config import YiSessionConfig, yi_default_session_config
from .manager import YiSessionManager, yi_session_manager


class YiSessionMiddleware(BaseHTTPMiddleware):
    """会话中间件"""

    def __init__(
        self,
        app,
        config: YiSessionConfig = yi_default_session_config,
        manager: YiSessionManager = yi_session_manager
    ):
        """
        初始化会话中间件
        
        Args:
            app: FastAPI应用
            config: 会话配置
            manager: 会话管理器
        """
        super().__init__(app)
        self.config = config
        self.manager = manager

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response]
    ) -> Response:
        """
        处理请求，管理会话
        
        Args:
            request: 请求对象
            call_next: 下一个中间件或路由处理函数
        
        Returns:
            Response: 响应对象
        """
        # 获取会话ID
        session_id = request.cookies.get(self.config.cookie_name)

        # 如果没有会话ID，创建新会话
        if not session_id:
            session_id = await self.manager.create_session()
        else:
            # 检查会话是否存在
            session_data = await self.manager.get_session_data(session_id)
            if not session_data:
                # 如果会话不存在，创建新会话
                session_id = await self.manager.create_session()

        # 将会话ID存储到请求状态中
        request.state.session_id = session_id

        # 调用下一个中间件或路由处理函数
        response = await call_next(request)

        # 设置会话Cookie
        response.set_cookie(
            key=self.config.cookie_name,
            value=session_id,
            max_age=self.config.cookie_max_age,
            path=self.config.cookie_path,
            domain=self.config.cookie_domain,
            secure=self.config.cookie_secure,
            httponly=self.config.cookie_httponly,
            samesite=self.config.cookie_samesite,
        )

        return response
