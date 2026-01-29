
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    url: str | None = None
    username: str | None = None
    password: str | None = None
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False

    model_config = SettingsConfigDict(
        extra="allow"
    )

    @field_validator("url")
    @classmethod
    def validate_database_url(cls, v):
        """Validate database URL format."""
        if v is None:
            return v
        if len(v.strip()) == 0:
            raise ValueError("Database URL cannot be empty")
        v = v.strip()
        if not any(prefix in v for prefix in ["mysql", "postgresql", "sqlite"]):
            raise ValueError(f"Database URL must start with 'mysql', 'postgresql', or 'sqlite', got: {v}")
        return v

    @field_validator("pool_size")
    @classmethod
    def validate_pool_size(cls, v):
        """Validate pool size."""
        if v < 1:
            raise ValueError(f"Pool size must be at least 1, got: {v}")
        if v > 100:
            raise ValueError(f"Pool size must be at most 100, got: {v}")
        return v

    @field_validator("max_overflow")
    @classmethod
    def validate_max_overflow(cls, v):
        """Validate max overflow."""
        if v < 0:
            raise ValueError(f"Max overflow must be non-negative, got: {v}")
        if v > 200:
            raise ValueError(f"Max overflow must be at most 200, got: {v}")
        return v

    @field_validator("pool_timeout")
    @classmethod
    def validate_pool_timeout(cls, v):
        """Validate pool timeout."""
        if v < 1:
            raise ValueError(f"Pool timeout must be at least 1 second, got: {v}")
        if v > 300:
            raise ValueError(f"Pool timeout must be at most 300 seconds, got: {v}")
        return v

    @field_validator("pool_recycle")
    @classmethod
    def validate_pool_recycle(cls, v):
        """Validate pool recycle."""
        if v < 300:
            raise ValueError(f"Pool recycle must be at least 300 seconds, got: {v}")
        if v > 86400:
            raise ValueError(f"Pool recycle must be at most 86400 seconds (1 day), got: {v}")
        return v

    @property
    def db_type(self) -> str:
        """获取数据库类型"""
        url = self.url
        if "://" in url:
            scheme_part = url.split("://")[0]
            if "+" in scheme_part:
                return scheme_part.split("+")[0]
            return scheme_part
        return url.split("+")[0] if "+" in url else url
