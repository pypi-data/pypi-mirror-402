
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class APIKeyConfig(BaseSettings):
    enabled: bool = False
    keys: list[str] = []
    header_name: str = "X-API-Key"
    query_param_name: str = "api_key"

    model_config = SettingsConfigDict(
        extra="allow"
    )

    @field_validator("enabled")
    @classmethod
    def validate_enabled(cls, v):
        """Validate enabled flag."""
        return bool(v)

    @field_validator("keys")
    @classmethod
    def validate_keys(cls, v):
        """Validate API keys list."""
        if not isinstance(v, list):
            raise ValueError("Keys must be a list")
        for key in v:
            if not key or len(key.strip()) == 0:
                raise ValueError(f"API key cannot be empty, got: {key}")
        return v

    @field_validator("header_name")
    @classmethod
    def validate_header_name(cls, v):
        """Validate header name."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Header name cannot be empty")
        return v.strip()

    @field_validator("query_param_name")
    @classmethod
    def validate_query_param_name(cls, v):
        """Validate query param name."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Query param name cannot be empty")
        return v.strip()
