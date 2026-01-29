"""配置模块，包含所有应用配置类"""

from .api_key import APIKeyConfig
from .app import AppConfig
from .celery import CeleryConfig
from .cors import CORSConfig
from .database import DatabaseConfig
from .datasource import DataSourceConfig
from .jwt import JWTConfig
from .middleware import CircuitBreakerConfig, MiddlewareConfig, RateLimitConfig, RequestLogConfig, ResponseTimeConfig
from .server import ServerConfig

# 延迟导入，避免循环导入
from .yi_config import YiConfig, YiSettings

# 导出全局配置实例（默认使用降级模式）
yi_config = YiConfig.instance(allow_fallback=True)
config = yi_config  # 提供简洁的别名

__all__ = [
    "AppConfig",
    "ServerConfig",
    "DatabaseConfig",
    "DataSourceConfig",
    "JWTConfig",
    "CORSConfig",
    "CeleryConfig",
    "APIKeyConfig",
    "RateLimitConfig",
    "CircuitBreakerConfig",
    "RequestLogConfig",
    "ResponseTimeConfig",
    "MiddlewareConfig",
    "YiSettings",
    "YiConfig",
    "yi_config",
    "config",  # 添加简洁别名到导出列表
]
