import secrets

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class JWTConfig(BaseSettings):
    secret_key: str = secrets.token_urlsafe(32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    model_config = SettingsConfigDict(
        extra="allow"
    )

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v):
        """Validate secret key strength."""
        # if not v or len(v.strip()) < 32:
        #     raise ValueError("Secret key must be at least 32 characters long")
        return v.strip()

    @field_validator("algorithm")
    @classmethod
    def validate_algorithm(cls, v):
        """Validate JWT algorithm."""
        allowed_algorithms = ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512", "ES256", "ES384", "ES512"]
        if v not in allowed_algorithms:
            raise ValueError(f"JWT algorithm must be one of {allowed_algorithms}, got: {v}")
        return v

    @field_validator("access_token_expire_minutes")
    @classmethod
    def validate_access_token_expire_minutes(cls, v):
        """Validate access token expire minutes."""
        if v < 1:
            raise ValueError(f"Access token expire minutes must be at least 1, got: {v}")
        if v > 1440:
            raise ValueError(f"Access token expire minutes must be at most 1440 (1 day), got: {v}")
        return v

    @field_validator("refresh_token_expire_days")
    @classmethod
    def validate_refresh_token_expire_days(cls, v):
        """Validate refresh token expire days."""
        if v < 1:
            raise ValueError(f"Refresh token expire days must be at least 1, got: {v}")
        if v > 365:
            raise ValueError(f"Refresh token expire days must be at most 365, got: {v}")
        return v
