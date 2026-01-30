from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerConfig(BaseSettings):
    port: int = 8000
    host: str = "localhost"
    reload: bool = True
    workers: int = 1
    timeout: int = 30

    model_config = SettingsConfigDict(
        extra="allow"
    )

    @field_validator("port")
    @classmethod
    def validate_port(cls, v):
        """Validate port range."""
        if v < 1 or v > 65535:
            raise ValueError(f"Port must be between 1 and 65535, got: {v}")
        return v

    @field_validator("host")
    @classmethod
    def validate_host(cls, v):
        """Validate host format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Host cannot be empty")
        return v.strip()
