"""yitool日志系统，基于rich的增强日志框架"""

from __future__ import annotations

from yitool.log.config import LogConfig
from yitool.log.context import (
    clear_log_context,
    log_context,
    set_log_context,
)
from yitool.log.core import (
    CRITICAL,
    DEBUG,
    ERROR,
    INFO,
    WARNING,
    critical,
    debug,
    error,
    exception,
    global_logger,
    info,
    set_log_level,
    setup_logging,
    structured_log,
    warning,
)
from yitool.log.decorators import (
    log_exception,
    log_execution_time,
    log_function,
)

__all__ = [
    # 核心日志函数和常量
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
    "debug",
    "info",
    "warning",
    "error",
    "critical",
    "exception",
    "structured_log",
    "setup_logging",
    "set_log_level",
    "global_logger",
    "logger",

    # 主要配置类
    "LogConfig",

    # 日志上下文管理
    "log_context",
    "set_log_context",
    "clear_log_context",

    # 常用日志装饰器
    "log_function",
    "log_execution_time",
    "log_exception",
]

# 保持向后兼容性
default_logger = global_logger.logger
logger = default_logger


