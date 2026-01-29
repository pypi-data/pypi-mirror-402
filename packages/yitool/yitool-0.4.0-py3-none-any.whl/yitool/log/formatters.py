"""日志格式化器"""

import json
import logging
from typing import Any

from yitool.log.context import get_log_context


class SimpleFormatter(logging.Formatter):
    """简单日志格式化器

    提供简单的日志格式化，支持日志上下文
    """

    def __init__(self, fmt: str | None = None, datefmt: str | None = None, style: str = "%"):
        """初始化简单日志格式化器

        Args:
            fmt: 日志格式字符串，默认包含时间、级别、名称、消息和上下文
            datefmt: 日期格式字符串，默认使用ISO格式
            style: 格式样式，支持 %, {, $
        """
        if fmt is None:
            fmt = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
        if datefmt is None:
            datefmt = "%Y-%m-%d %H:%M:%S"

        super().__init__(fmt, datefmt, style)

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录

        Args:
            record: 日志记录对象

        Returns:
            格式化后的日志字符串
        """
        # 获取日志上下文
        context = get_log_context()

        # 添加上下文信息到日志记录
        if context:
            record.__dict__.update(context)

        # 添加额外的日志属性
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            record.__dict__.update(record.extra)

        return super().format(record)


class JSONFormatter(logging.Formatter):
    """JSON日志格式化器

    将日志记录格式化为JSON字符串，支持日志上下文
    """

    def __init__(self, datefmt: str | None = None):
        """初始化JSON日志格式化器

        Args:
            datefmt: 日期格式字符串，默认使用ISO格式
        """
        if datefmt is None:
            datefmt = "%Y-%m-%d %H:%M:%S"

        super().__init__(fmt=None, datefmt=datefmt)

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为JSON字符串

        Args:
            record: 日志记录对象

        Returns:
            格式化后的JSON字符串
        """
        # 获取日志上下文
        context = get_log_context()

        # 保存原始消息
        original_message = record.msg if hasattr(record, "msg") else str(record.getMessage())

        # 基本日志数据
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": original_message,
            "pathname": record.pathname,
            "filename": record.filename,
            "lineno": record.lineno,
            "funcName": record.funcName,
            "process": record.process,
            "thread": record.thread,
        }

        # 添加上下文数据
        log_data.update(context)

        # 添加额外的日志属性
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_data.update(record.extra)

        # 添加异常信息
        if record.exc_info:
            log_data["exc_info"] = self.formatException(record.exc_info)

        # 返回JSON字符串
        return json.dumps(log_data, ensure_ascii=False, default=str)


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器

    支持将日志格式化为结构化格式，支持日志上下文
    """

    def __init__(self, fmt: str | None = None, datefmt: str | None = None, style: str = "%", use_json: bool = False):
        """初始化结构化日志格式化器

        Args:
            fmt: 日志格式字符串
            datefmt: 日期格式字符串
            style: 格式样式
            use_json: 是否使用JSON格式输出
        """
        if fmt is None:
            fmt = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
        if datefmt is None:
            datefmt = "%Y-%m-%d %H:%M:%S"

        super().__init__(fmt, datefmt, style)
        self.use_json = use_json

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录

        Args:
            record: 日志记录对象

        Returns:
            格式化后的日志字符串
        """
        # 获取日志上下文
        context = get_log_context()

        # 保存原始消息
        original_message = record.msg if hasattr(record, "msg") else str(record.getMessage())

        # 基本日志数据
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": original_message,
            "pathname": record.pathname,
            "filename": record.filename,
            "lineno": record.lineno,
            "funcName": record.funcName,
        }

        # 添加上下文数据
        log_data.update(context)

        # 添加额外的日志属性
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_data.update(record.extra)

        # 如果是JSON格式，返回JSON字符串
        if self.use_json:
            import json
            return json.dumps(log_data, ensure_ascii=False, default=str)

        # 否则返回格式化的字符串
        return super().format(record)

    def get_structured_data(self, record: logging.LogRecord) -> dict[str, Any]:
        """获取结构化日志数据

        Args:
            record: 日志记录对象

        Returns:
            结构化日志数据
        """
        # 获取日志上下文
        context = get_log_context()

        # 保存原始消息
        original_message = record.msg if hasattr(record, "msg") else str(record.getMessage())

        # 基本日志数据
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": original_message,
            "pathname": record.pathname,
            "filename": record.filename,
            "lineno": record.lineno,
            "funcName": record.funcName,
        }

        # 添加上下文数据
        log_data.update(context)

        # 添加额外的日志属性
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_data.update(record.extra)

        return log_data
