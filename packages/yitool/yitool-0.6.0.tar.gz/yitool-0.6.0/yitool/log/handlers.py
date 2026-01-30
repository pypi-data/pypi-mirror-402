"""日志处理器"""

import logging
import logging.handlers
import os

from rich.console import Console
from rich.logging import RichHandler

from yitool.log.config import FileConfig, StructuredConfig, TerminalConfig
from yitool.log.formatters import JSONFormatter, SimpleFormatter, StructuredFormatter


class TerminalHandler(RichHandler):
    """终端日志处理器

    基于RichHandler的增强终端日志处理器，支持配置化管理
    """

    def __init__(self, config: TerminalConfig | None = None):
        """初始化终端日志处理器

        Args:
            config: 终端日志配置，如为None则使用默认配置
        """
        if config is None:
            config = TerminalConfig()

        # 创建Rich控制台
        console = config.console or Console(
            width=config.width,
        )

        # 初始化RichHandler
        super().__init__(
            show_time=config.show_time,
            rich_tracebacks=config.rich_tracebacks,
            tracebacks_show_locals=config.tracebacks_show_locals,
            markup=config.markup,
            show_path=config.show_path,
            console=console,
        )

        # 设置格式化器
        self.setFormatter(SimpleFormatter())

        self.config = config

    def set_log_config(self, config: TerminalConfig) -> None:
        """更新终端日志配置

        Args:
            config: 新的终端日志配置
        """
        self.config = config
        self.console.width = config.width
        self.show_time = config.show_time
        self.rich_tracebacks = config.rich_tracebacks
        self.tracebacks_show_locals = config.tracebacks_show_locals
        self.markup = config.markup
        self.show_path = config.show_path


class FileHandler(logging.handlers.RotatingFileHandler):
    """文件日志处理器

    支持日志轮转和保留策略，支持多种日志格式
    """

    def __init__(self, config: FileConfig | None = None, structured_config: StructuredConfig | None = None):
        """初始化文件日志处理器

        Args:
            config: 文件日志配置，如为None则使用默认配置
            structured_config: 结构化日志配置，用于决定日志格式
        """
        if config is None:
            config = FileConfig()
        if structured_config is None:
            structured_config = StructuredConfig()

        # 确保日志目录存在
        if config.path:
            log_dir = os.path.dirname(config.path)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
        else:
            raise ValueError("File path must be provided for FileHandler")

        # 解析轮转大小
        max_bytes = 10 * 1024 * 1024  # 默认10MB
        if config.rotation:
            rotation = config.rotation.lower()
            if "mb" in rotation:
                max_bytes = int(rotation.replace("mb", "").strip()) * 1024 * 1024
            elif "gb" in rotation:
                max_bytes = int(rotation.replace("gb", "").strip()) * 1024 * 1024 * 1024

        # 解析备份数量
        backup_count = config.backup_count
        if config.retention:
            retention = config.retention.lower()
            if "days" in retention:
                backup_count = int(retention.replace("days", "").strip())

        # 初始化RotatingFileHandler
        super().__init__(
            filename=config.path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding=config.encoding,
        )

        # 设置格式化器
        if structured_config.use_json:
            self.setFormatter(JSONFormatter())
        elif structured_config.enabled:
            self.setFormatter(StructuredFormatter(use_json=False))
        else:
            self.setFormatter(SimpleFormatter())

        self.config = config
        self.structured_config = structured_config

    def set_log_config(self, config: FileConfig, structured_config: StructuredConfig | None = None) -> None:
        """更新文件日志配置

        Args:
            config: 新的文件日志配置
            structured_config: 新的结构化日志配置
        """
        self.config = config
        if structured_config:
            self.structured_config = structured_config

        # 更新格式化器
        if self.structured_config.use_json:
            self.setFormatter(JSONFormatter())
        elif self.structured_config.enabled:
            self.setFormatter(StructuredFormatter(use_json=False))
        else:
            self.setFormatter(SimpleFormatter())

        # 更新轮转和保留策略
        max_bytes = 10 * 1024 * 1024  # 默认10MB
        if config.rotation:
            rotation = config.rotation.lower()
            if "mb" in rotation:
                max_bytes = int(rotation.replace("mb", "").strip()) * 1024 * 1024
            elif "gb" in rotation:
                max_bytes = int(rotation.replace("gb", "").strip()) * 1024 * 1024 * 1024

        backup_count = config.backup_count
        if config.retention:
            retention = config.retention.lower()
            if "days" in retention:
                backup_count = int(retention.replace("days", "").strip())

        self.maxBytes = max_bytes
        self.backupCount = backup_count
