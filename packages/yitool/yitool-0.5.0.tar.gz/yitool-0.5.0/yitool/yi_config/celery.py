
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class CeleryConfig(BaseSettings):
    broker_url: str | None = None
    result_backend: str | None = None
    task_serializer: str = "json"
    result_serializer: str = "json"
    accept_content: list[str] = ["json"]
    timezone: str = "UTC"
    enable_utc: bool = True
    worker: dict = {}
    beat: dict = {}
    beat_schedule: dict | None = None

    model_config = SettingsConfigDict(
        extra="allow"
    )

    @field_validator("broker_url")
    @classmethod
    def validate_broker_url(cls, v):
        """Validate broker URL format."""
        if v is None:
            return v
        if len(v.strip()) == 0:
            raise ValueError("Broker URL cannot be empty")
        return v.strip()

    @field_validator("result_backend")
    @classmethod
    def validate_result_backend(cls, v):
        """Validate result backend format."""
        if v is None:
            return v
        if len(v.strip()) == 0:
            raise ValueError("Result backend cannot be empty")
        return v.strip()

    @field_validator("task_serializer")
    @classmethod
    def validate_task_serializer(cls, v):
        """Validate task serializer format."""
        allowed_serializers = ["json", "pickle", "yaml", "msgpack"]
        if v not in allowed_serializers:
            raise ValueError(f"Task serializer must be one of {allowed_serializers}, got: {v}")
        return v

    @field_validator("result_serializer")
    @classmethod
    def validate_result_serializer(cls, v):
        """Validate result serializer format."""
        allowed_serializers = ["json", "pickle", "yaml", "msgpack"]
        if v not in allowed_serializers:
            raise ValueError(f"Result serializer must be one of {allowed_serializers}, got: {v}")
        return v

    @field_validator("accept_content")
    @classmethod
    def validate_accept_content(cls, v):
        """Validate accept content formats."""
        if not isinstance(v, list):
            raise ValueError("Accept content must be a list")
        if not v:
            raise ValueError("Accept content cannot be empty")
        allowed_content = ["json", "pickle", "yaml", "msgpack"]
        for content in v:
            if content not in allowed_content:
                raise ValueError(f"Content type {content} is not allowed. Allowed types: {allowed_content}")
        return v

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v):
        """Validate timezone format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Timezone cannot be empty")
        return v.strip()

    @field_validator("worker")
    @classmethod
    def validate_worker(cls, v):
        """Validate worker configuration."""
        if not isinstance(v, dict):
            raise ValueError("Worker configuration must be a dictionary")
        return v

    @field_validator("beat")
    @classmethod
    def validate_beat(cls, v):
        """Validate beat configuration."""
        if not isinstance(v, dict):
            raise ValueError("Beat configuration must be a dictionary")
        return v
