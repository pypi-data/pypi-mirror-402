
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class CORSConfig(BaseSettings):
    origins: list[str] = ["*"]
    methods: list[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    headers: list[str] = ["*"]
    expose_headers: list[str] = []
    allow_credentials: bool = True
    max_age: int = 600

    model_config = SettingsConfigDict(
        extra="allow"
    )

    @field_validator("origins")
    @classmethod
    def validate_origins(cls, v):
        """Validate CORS origins."""
        if not isinstance(v, list):
            raise ValueError("Origins must be a list")
        if not v:
            raise ValueError("Origins cannot be empty")
        return v

    @field_validator("methods")
    @classmethod
    def validate_methods(cls, v):
        """Validate CORS methods."""
        if not isinstance(v, list):
            raise ValueError("Methods must be a list")
        if not v:
            raise ValueError("Methods cannot be empty")
        allowed_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"]
        for method in v:
            if method not in allowed_methods:
                raise ValueError(f"Method {method} is not allowed. Allowed methods: {allowed_methods}")
        return v

    @field_validator("headers")
    @classmethod
    def validate_headers(cls, v):
        """Validate CORS headers."""
        if not isinstance(v, list):
            raise ValueError("Headers must be a list")
        if not v:
            raise ValueError("Headers cannot be empty")
        return v
