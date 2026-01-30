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
    "config",
]

# 单例出口（延迟初始化）
config = None

def get_config():
    """获取配置实例（延迟初始化）"""
    global config
    if config is None:
        config = YiConfig.instance()
    return config
