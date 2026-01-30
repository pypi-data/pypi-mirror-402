"""日志配置管理"""

import logging
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class TerminalConfig(BaseSettings):
    """终端日志配置"""

    enabled: bool = True
    width: int | None = None
    show_time: bool = True
    rich_tracebacks: bool = True
    tracebacks_show_locals: bool = True
    markup: bool = True
    show_path: bool = True
    console: Any = None

    model_config = SettingsConfigDict(
        extra="allow"
    )


class FileConfig(BaseSettings):
    """文件日志配置"""

    enabled: bool = False
    path: str | None = None
    rotation: str = "10 MB"
    retention: str = "7 days"
    encoding: str = "utf-8"
    backup_count: int = 7

    model_config = SettingsConfigDict(
        extra="allow"
    )


class StructuredConfig(BaseSettings):
    """结构化日志配置"""

    enabled: bool = False
    use_json: bool = False
    extra_fields: list[str] = []

    model_config = SettingsConfigDict(
        extra="allow"
    )


class LogConfig(BaseSettings):
    """日志配置类"""

    level: str = "INFO"
    terminal: TerminalConfig = TerminalConfig()
    file: FileConfig = FileConfig()
    structured: StructuredConfig = StructuredConfig()
    filters: list[logging.Filter] = []
    propagate: bool = False

    model_config = SettingsConfigDict(
        extra="allow"
    )

    @field_validator("level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level format."""
        if not v:
            return logging.INFO
        # Convert string level to logging constant
        return logging.getLevelName(v.upper())

    @classmethod
    def from_dict(cls, config_dict: dict) -> "LogConfig":
        """从字典创建日志配置（兼容旧接口）"""
        return cls.model_validate(config_dict)
