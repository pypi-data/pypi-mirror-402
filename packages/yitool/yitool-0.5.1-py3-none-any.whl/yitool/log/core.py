"""核心日志类"""

import logging
from typing import Any

from yitool.const import __YITECH__
from yitool.log.config import LogConfig
from yitool.log.handlers import FileHandler, TerminalHandler


class Logger:
    """核心日志类

    整合所有日志组件，提供统一的日志管理接口
    """

    def __init__(self, name: str = __YITECH__):
        """初始化日志类

        Args:
            name: 日志器名称
        """
        self.name = name
        self._logger = logging.getLogger(name)
        self._config = LogConfig()
        self._handlers = {}
        self._initialized = False

    @property
    def logger(self) -> logging.Logger:
        """获取底层logging.Logger实例

        Returns:
            logging.Logger实例
        """
        return self._logger

    @property
    def config(self) -> LogConfig:
        """获取当前日志配置

        Returns:
            当前日志配置
        """
        return self._config

    def setup(self, config: LogConfig | None = None) -> None:
        """设置日志系统

        Args:
            config: 日志配置，如为None则使用默认配置
        """
        if config:
            self._config = config

        # 清除已有的处理器
        for handler in self._logger.handlers[:]:
            self._logger.removeHandler(handler)
        self._handlers.clear()

        # 设置终端处理器
        if self._config.terminal.enabled:
            terminal_handler = TerminalHandler(self._config.terminal)
            self._logger.addHandler(terminal_handler)
            self._handlers["terminal"] = terminal_handler

        # 设置文件处理器
        if self._config.file.enabled and self._config.file.path:
            try:
                file_handler = FileHandler(
                    self._config.file,
                    self._config.structured
                )
                self._logger.addHandler(file_handler)
                self._handlers["file"] = file_handler
            except Exception as e:
                self._logger.error(f"Failed to set up file logging: {e}")

        # 设置日志级别和传播
        self._logger.setLevel(self._config.level)
        self._logger.propagate = self._config.propagate

        # 添加过滤器
        for filter in self._config.filters:
            self._logger.addFilter(filter)
            for handler in self._handlers.values():
                handler.addFilter(filter)

        self._initialized = True
        self.debug(f"Logging system initialized with level: {logging.getLevelName(self._config.level)}")

    def update_config(self, config_dict: dict[str, Any]) -> None:
        """更新日志配置

        Args:
            config_dict: 配置字典，将与现有配置合并
        """
        # 从字典创建新配置
        new_config = LogConfig.from_dict(config_dict)
        # 合并配置
        self._config = self._merge_configs(self._config, new_config)
        # 重新设置日志系统
        self.setup(self._config)

    def set_level(self, level: int | str) -> None:
        """动态设置日志级别

        Args:
            level: 日志级别，可以是数字或字符串，如logging.DEBUG, 'DEBUG', 10
        """
        if isinstance(level, str):
            level = logging.getLevelName(level.upper())
        self._config.level = level
        self._logger.setLevel(level)
        self.info(f"Log level changed to: {logging.getLevelName(level)}")

    def structured_log(self, level: int, message: str, **kwargs) -> None:
        """记录结构化日志

        Args:
            level: 日志级别
            message: 日志消息
            **kwargs: 额外的结构化数据
        """
        if self._logger.isEnabledFor(level):
            extra = kwargs.copy()
            self._logger.log(level, message, extra=extra)

    def debug(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """记录调试信息

        Args:
            msg: 日志消息
            *args: 消息格式化参数
            **kwargs: 额外参数
        """
        if self._logger.isEnabledFor(logging.DEBUG):
            self._logger.debug(msg, *args, **kwargs)

    def info(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """记录一般信息

        Args:
            msg: 日志消息
            *args: 消息格式化参数
            **kwargs: 额外参数
        """
        if self._logger.isEnabledFor(logging.INFO):
            self._logger.info(msg, *args, **kwargs)

    def warning(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """记录警告信息

        Args:
            msg: 日志消息
            *args: 消息格式化参数
            **kwargs: 额外参数
        """
        if self._logger.isEnabledFor(logging.WARNING):
            self._logger.warning(msg, *args, **kwargs)

    def error(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """记录错误信息

        Args:
            msg: 日志消息
            *args: 消息格式化参数
            **kwargs: 额外参数
        """
        if self._logger.isEnabledFor(logging.ERROR):
            self._logger.error(msg, *args, **kwargs)

    def critical(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """记录严重错误信息

        Args:
            msg: 日志消息
            *args: 消息格式化参数
            **kwargs: 额外参数
        """
        if self._logger.isEnabledFor(logging.CRITICAL):
            self._logger.critical(msg, *args, **kwargs)

    def exception(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """记录异常信息，自动包含堆栈跟踪

        Args:
            msg: 日志消息
            *args: 消息格式化参数
            **kwargs: 额外参数
        """
        if self._logger.isEnabledFor(logging.ERROR):
            self._logger.exception(msg, *args, **kwargs)

    def get_handler(self, name: str) -> logging.Handler | None:
        """获取指定名称的日志处理器

        Args:
            name: 处理器名称，如'terminal'或'file'

        Returns:
            日志处理器实例，如不存在则返回None
        """
        return self._handlers.get(name)

    def reset(self) -> None:
        """重置日志系统

        恢复默认配置并重新初始化
        """
        self._config = LogConfig()
        self.setup()

    @staticmethod
    def _merge_configs(old_config: LogConfig, new_config: LogConfig) -> LogConfig:
        """合并日志配置

        Args:
            old_config: 旧配置
            new_config: 新配置

        Returns:
            合并后的配置
        """
        # 使用Pydantic的model_copy和model_dump特性进行配置合并
        # 将新配置转换为字典，仅包含非默认值
        new_config_dict = new_config.model_dump(exclude_unset=True)

        # 合并配置
        merged_config = old_config.model_copy(update=new_config_dict)

        return merged_config


# 创建全局日志实例
global_logger = Logger()
"""yitool的全局日志实例，基于Logger类的增强日志系统"""

# 导出常用方法和常量
def setup_logging(config: LogConfig | None = None) -> None:
    """设置日志系统

    Args:
        config: 日志配置，如为None则使用默认配置
    """
    global_logger.setup(config)


def set_log_level(level: int | str) -> None:
    """动态设置日志级别

    Args:
        level: 日志级别，可以是数字或字符串
    """
    global_logger.set_level(level)


def structured_log(level: int, message: str, **kwargs) -> None:
    """记录结构化日志

    Args:
        level: 日志级别
        message: 日志消息
        **kwargs: 额外的结构化数据
    """
    global_logger.structured_log(level, message, **kwargs)


def debug(msg: Any, *args: Any, **kwargs: Any) -> None:
    """记录调试信息

    Args:
        msg: 日志消息
        *args: 消息格式化参数
        **kwargs: 额外参数
    """
    global_logger.debug(msg, *args, **kwargs)


def info(msg: Any, *args: Any, **kwargs: Any) -> None:
    """记录一般信息

    Args:
        msg: 日志消息
        *args: 消息格式化参数
        **kwargs: 额外参数
    """
    global_logger.info(msg, *args, **kwargs)


def warning(msg: Any, *args: Any, **kwargs: Any) -> None:
    """记录警告信息

    Args:
        msg: 日志消息
        *args: 消息格式化参数
        **kwargs: 额外参数
    """
    global_logger.warning(msg, *args, **kwargs)


def error(msg: Any, *args: Any, **kwargs: Any) -> None:
    """记录错误信息

    Args:
        msg: 日志消息
        *args: 消息格式化参数
        **kwargs: 额外参数
    """
    global_logger.error(msg, *args, **kwargs)


def critical(msg: Any, *args: Any, **kwargs: Any) -> None:
    """记录严重错误信息

    Args:
        msg: 日志消息
        *args: 消息格式化参数
        **kwargs: 额外参数
    """
    global_logger.critical(msg, *args, **kwargs)


def exception(msg: Any, *args: Any, **kwargs: Any) -> None:
    """记录异常信息，自动包含堆栈跟踪

    Args:
        msg: 日志消息
        *args: 消息格式化参数
        **kwargs: 额外参数
    """
    global_logger.exception(msg, *args, **kwargs)


# 导出日志级别常量
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL
