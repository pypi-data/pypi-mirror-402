
import yaml
from fastapi import APIRouter, FastAPI
from fastapi.middleware import Middleware

from .middleware_manager import YiMiddlewareManager, yi_middleware_manager
from .middlewares import (
    YiCircuitBreakerMiddleware,
    YiCORSMiddleware,
    YiRateLimitMiddleware,
    YiRequestIdMiddleware,
    YiRequestLoggingMiddleware,
    YiResponseTimeMiddleware,
)
from ..yi_config.app import AppConfig


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
        self._middleware_manager = yi_middleware_manager

    def add_middlewares(self, middlewares: list[Middleware] | None = None, include_defaults: bool = True):
        """添加中间件

        Args:
            middlewares: 自定义中间件列表
            include_defaults: 是否包含默认中间件，默认为 True
        """
        if include_defaults:
            # 添加默认中间件
            default_middlewares = [
                YiRequestIdMiddleware,        # 用于生成请求ID
                YiRequestLoggingMiddleware,   # 用于记录请求日志
                YiResponseTimeMiddleware,     # 用于记录响应时间
                YiRateLimitMiddleware,        # 用于限流
                YiCircuitBreakerMiddleware,   # 用于断路器
                YiCORSMiddleware              # 用于CORS
            ]
            for middleware in default_middlewares:
                self.add_middleware(middleware)

        # 添加自定义中间件
        for middleware in middlewares or []:
            if isinstance(middleware, Middleware):
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
        for router in routers or []:
            self.include_router(router)

    def bootstrap(self, middlewares: list | None = None, routers: list[APIRouter] | None = None):
        """应用初始化"""
        # 添加中间件
        self.add_middlewares(middlewares=middlewares, include_defaults=not middlewares)
        # 添加路由
        self.include_routers(routers)

    @classmethod
    def from_config(cls, config_source, *args, **kwargs):
        """从配置源创建 FastAPI 应用实例

        Args:
            config_source: 配置源，可以是文件路径、字典或配置对象
            *args: FastAPI 初始化参数
            **kwargs: FastAPI 初始化参数

        Returns:
            YiFast: 配置好的 FastAPI 应用实例
        """
        # 从指定源加载配置
        if isinstance(config_source, str):
            # 从文件加载配置
            try:
                with open(config_source) as f:
                    config_dict = yaml.safe_load(f)
                app_config = AppConfig(**config_dict.get("app", {}))
            except FileNotFoundError:
                # 文件不存在，使用默认配置
                app_config = None
        elif isinstance(config_source, dict):
            # 从字典加载配置
            app_config = AppConfig(**config_source.get("app", {}))
        else:
            # 直接使用配置对象
            app_config = getattr(config_source, "app", None)

        # 合并配置到 kwargs
        if app_config:
            kwargs.setdefault("title", getattr(app_config, "name", kwargs.get("title")))
            kwargs.setdefault("version", getattr(app_config, "version", kwargs.get("version")))
            kwargs.setdefault("description", getattr(app_config, "description", kwargs.get("description")))

        return cls(*args, **kwargs)
