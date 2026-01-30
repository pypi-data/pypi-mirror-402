from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    name: str | None = None
    version: str | None = None
    environment: str = "development"
    debug: bool = True

    model_config = SettingsConfigDict(
        extra="allow"
    )

    @field_validator("name")
    @classmethod
    def validate_app_name(cls, v):
        """Validate app name format."""
        if v is not None and len(v.strip()) == 0:
            raise ValueError("App name cannot be empty")
        return v.strip() if v is not None else v

    @field_validator("version")
    @classmethod
    def validate_app_version(cls, v):
        """Validate app version format."""
        if v is not None and len(v.strip()) == 0:
            raise ValueError("App version cannot be empty")
        return v.strip() if v is not None else v

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment format."""
        allowed_environments = ["development", "staging", "production", "testing"]
        if v not in allowed_environments:
            raise ValueError(f"Environment must be one of {allowed_environments}, got: {v}")
        return v
