
from fastapi import APIRouter, FastAPI
from fastapi.middleware import Middleware

from .middlewares import (
    YiCircuitBreakerMiddleware,
    YiCORSMiddleware,
    YiRateLimitMiddleware,
    YiRequestIdMiddleware,
    YiRequestLoggingMiddleware,
    YiResponseTimeMiddleware,
)
from .middleware_manager import YiMiddlewareManager, yi_middleware_manager


class YiFast(FastAPI):
    """自定义 FastAPI 应用类"""

    def __init__(self, *args, config=None, **kwargs):
        """初始化 FastAPI 应用

        Args:
            *args: FastAPI 初始化参数
            config: 配置对象或配置字典
            **kwargs: FastAPI 初始化参数
        """
        super().__init__(*args, **kwargs)
        self._config = config
        self._middleware_manager = yi_middleware_manager
        self._initialize()

    def _initialize(self):
        """初始化应用"""
        # 可以在这里添加统一的初始化逻辑
        pass

    @classmethod
    def create(cls, *args, config=None, **kwargs):
        """创建并配置 FastAPI 应用实例

        Args:
            *args: FastAPI 初始化参数
            config: 配置对象或配置字典
            **kwargs: FastAPI 初始化参数

        Returns:
            YiFastApp: 配置好的 FastAPI 应用实例
        """
        return cls(*args, config=config, **kwargs)

    @classmethod
    def create_by(cls, source, *args, **kwargs):
        """从指定源创建 FastAPI 应用实例

        Args:
            source: 配置源，可以是文件路径或字典
            *args: FastAPI 初始化参数
            **kwargs: FastAPI 初始化参数

        Returns:
            YiFastApp: 配置好的 FastAPI 应用实例
        """
        from yitool.yi_config.app import AppConfig
        from yitool.yi_config.server import ServerConfig

        # 从指定源加载配置
        if isinstance(source, str):
            # 从文件加载配置
            import yaml
            try:
                with open(source) as f:
                    config_dict = yaml.safe_load(f)
                app_config = AppConfig(**config_dict.get("app", {}))
                server_config = ServerConfig(**config_dict.get("server")) if config_dict.get("server") else None
            except FileNotFoundError:
                # 文件不存在，使用默认配置
                app_config = None
                server_config = None
        elif isinstance(source, dict):
            # 从字典加载配置
            app_config = AppConfig(**source.get("app", {}))
            server_config = ServerConfig(**source.get("server")) if source.get("server") else None
        else:
            # 直接使用配置对象
            app_config = getattr(source, "app", None)
            server_config = getattr(source, "server", None)

        # 合并配置到 kwargs
        if app_config:
            kwargs.setdefault("title", getattr(app_config, "name", kwargs.get("title")))
            kwargs.setdefault("version", getattr(app_config, "version", kwargs.get("version")))
            kwargs.setdefault("description", getattr(app_config, "description", kwargs.get("description")))

        if server_config:
            # 服务器配置通常在启动时使用，这里不直接设置
            pass

        return cls.create(*args, config=source, **kwargs)

    def add_middlewares(self, middlewares: list[Middleware] | None = None, include_defaults: bool = True):
        """添加中间件

        Args:
            middlewares: 自定义中间件列表
            include_defaults: 是否包含默认中间件，默认为 True
        """
        if include_defaults:
            # 添加默认中间件
            self.add_middleware(YiRequestIdMiddleware) # 用于生成请求ID
            self.add_middleware(YiRequestLoggingMiddleware) # 用于记录请求日志
            self.add_middleware(YiResponseTimeMiddleware) # 用于记录响应时间
            self.add_middleware(YiRateLimitMiddleware) # 用于限流
            self.add_middleware(YiCircuitBreakerMiddleware) # 用于断路器
            self.add_middleware(YiCORSMiddleware) # 用于CORS
            # self.add_middleware(YiSessionMiddleware) # 用于会话管理

        # 添加自定义中间件
        for middleware in middlewares or []:
            if isinstance(middleware, Middleware):
                # Middleware objects have cls, args, and kwargs attributes
                self.add_middleware(middleware.cls, *middleware.args, **middleware.kwargs)
            else:
                self.add_middleware(middleware)

    def add_default_middleware(self, middleware_type: str, include: bool = True):
        """添加或移除特定的默认中间件

        Args:
            middleware_type: 中间件类型，支持 'request_id', 'logging', 'response_time', 'rate_limit', 'circuit_breaker', 'cors'
            include: 是否添加该中间件，True 表示添加，False 表示跳过
        """
        middleware_map = {
            "request_id": YiRequestIdMiddleware,
            "logging": YiRequestLoggingMiddleware,
            "response_time": YiResponseTimeMiddleware,
            "rate_limit": YiRateLimitMiddleware,
            "circuit_breaker": YiCircuitBreakerMiddleware,
            "cors": YiCORSMiddleware
        }

        if include and middleware_type in middleware_map:
            self.add_middleware(middleware_map[middleware_type])

    def use_middleware_manager(self, middleware_manager: YiMiddlewareManager | None = None):
        """使用中间件管理器

        Args:
            middleware_manager: 中间件管理器实例，默认为全局实例
        """
        if middleware_manager:
            self._middleware_manager = middleware_manager
        # 注册中间件到应用
        self._middleware_manager.register_to_app(self)

    def include_routers(self, routers: list[APIRouter] | None = None):
        """添加路由"""
        # self.include_router(core_router) # 注册核心路由
        # self.include_router(auth_router) # 注册认证路由
        # self.include_router(users_router) # 注册用户管理路由
        # self.include_router(tasks_router) # 注册任务管理路由
        for router in routers or []:
            self.include_router(router)

    def bootstrap(self, middlewares: list | None = None, routers: list[APIRouter] | None = None):
        """应用初始化"""
        # 添加中间件
        if middlewares:
            self.add_middlewares(middlewares, include_defaults=False)
        else:
            self.add_middlewares(include_defaults=True)
        # 添加路由
        self.include_routers(routers)
