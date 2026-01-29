"""导出公共接口"""

from __future__ import annotations

import importlib
import typing

from yitool.const import __VERSION__

__version__ = __VERSION__

__all__ = [
    # 核心模块
    "shared",
    "utils",
    "misc",
    "cli",
    "const",
    "enums",
    "exceptions",
    "log",
    "yi_serializer",
    "yi_db",
    "yi_cache",
    "yi_config",
    "yi_fast",
    "yi_celery",
    "yi_event_bus",
    "yi_mail",
    "yi_monitor",
    "yi_storage",
    # 常用组件（简化导入）
    "YiDB",
    "YiRedis",
    # SQLModel 支持导出（延迟导入以避免循环依赖）
    "YiSQLModelSerializable",
    "SqlModelUtils",
    "yi_cache_manager",
    "yi_event_bus",
    "YiEventBusException",
    "on_event",
    "once_event",
    "emit_event",
    "on_event_before",
    "on_event_after",
    "AbcYiEventBus",
    "YiRateLimit",
    "YiRateLimitMiddleware",
    "create_rate_limit",
    "create_rate_limit_middleware",
    "default_rate_limit",
    "default_rate_limit_middleware",
    "YiBaseMailer",
    "YiConsoleMailer",
    "YiSMTPMailer",
    "YiSESMailer",
    "YiSendGridMailer",
    "YiMailerFactory",
    "YiMailQueue",
    "create_mailer",
    "create_mail_queue",
    "yi_mailer",
    "yi_mail_queue",
    "YiMonitor",
    "YiMonitorMiddleware",
    "create_monitor",
    "create_monitor_middleware",
    "add_metrics_endpoint",
    "default_monitor",
    "default_monitor_middleware",
    "AbcYiStorage",
    "YiLocalStorage",
    "YiS3Storage",
    "YiStorageFactory",
    "YiStorageType",
    "yi_create_storage",
    "yi_storage",
    "YiSecurity",
    "YiJWTManager",
    "YiPasswordManager",
    "yi_security",
    "create_jwt_manager",
    "yi_password_manager",
]

# 常用组件的简化导入
try:
    from yitool.yi_db.yi_db import YiDB
except ImportError:
    pass

try:
    from yitool.yi_cache.yi_redis import YiRedis
except ImportError:
    pass

try:
    from yitool.yi_cache.yi_cache_manager import yi_cache_manager
except ImportError:
    pass

try:
    from yitool.yi_event_bus.yi_event_bus import YiEventBusException, yi_event_bus
except ImportError:
    pass

try:
    from yitool.yi_event_bus._abc import AbcYiEventBus
except ImportError:
    pass

try:
    from yitool.yi_event_bus.decorators import emit_event, on_event, on_event_after, on_event_before, once_event
except ImportError:
    pass

try:
    from yitool.yi_fast import (
        YiJWTManager,
        YiPasswordManager,
        YiRateLimit,
        YiRateLimitMiddleware,
        YiSecurity,
        create_jwt_manager,
        create_rate_limit,
        create_rate_limit_middleware,
        default_rate_limit,
        default_rate_limit_middleware,
        yi_password_manager,
        yi_security,
    )
except ImportError:
    pass

try:
    from yitool.yi_mail import (
        YiBaseMailer,
        YiConsoleMailer,
        YiMailerFactory,
        YiMailQueue,
        YiSendGridMailer,
        YiSESMailer,
        YiSMTPMailer,
        create_mail_queue,
        create_mailer,
        yi_mail_queue,
        yi_mailer,
    )
except ImportError:
    pass

try:
    from yitool.yi_monitor import (
        YiMonitor,
        YiMonitorMiddleware,
        add_metrics_endpoint,
        create_monitor,
        create_monitor_middleware,
        default_monitor,
        default_monitor_middleware,
    )
except ImportError:
    pass


try:
    from yitool.yi_storage import (
        AbcYiStorage,
        YiLocalStorage,
        YiS3Storage,
        YiStorageFactory,
        YiStorageType,
        yi_create_storage,
        yi_storage,
    )
except ImportError:
    pass


# Copied from https://peps.python.org/pep-0562/
def __getattr__(name: str) -> typing.Any:
    if name in __all__:
        return importlib.import_module("." + name, __name__)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
