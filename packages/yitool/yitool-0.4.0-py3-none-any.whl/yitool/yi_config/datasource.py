
from pydantic_settings import BaseSettings, SettingsConfigDict

from yitool.yi_config.database import DatabaseConfig


class DataSourceConfig(BaseSettings):
    master: DatabaseConfig
    slave: DatabaseConfig | None = None
    tasks: DatabaseConfig | None = None

    model_config = SettingsConfigDict(
        extra="allow"
    )
