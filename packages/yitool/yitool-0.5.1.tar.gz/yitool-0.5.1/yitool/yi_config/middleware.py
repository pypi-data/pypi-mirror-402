from pydantic_settings import BaseSettings, SettingsConfigDict


class RateLimitConfig(BaseSettings):
    """限流配置"""

    enabled: bool = False
    limit: int = 100  # 每个时间窗口的请求数
    window_seconds: int = 60  # 时间窗口大小（秒）
    key_func: str = "ip"  # 限流键生成函数：ip, user, api_key

    model_config = SettingsConfigDict(
        extra="allow"
    )


class CircuitBreakerConfig(BaseSettings):
    """熔断配置"""

    enabled: bool = False
    failure_threshold: int = 5  # 熔断阈值
    recovery_timeout: int = 30  # 恢复超时时间（秒）
    expected_exceptions: list[str] = ["HTTPException"]  # 预期的异常类型

    model_config = SettingsConfigDict(
        extra="allow"
    )


class RequestLogConfig(BaseSettings):
    """请求日志配置"""

    enabled: bool = True
    log_level: str = "info"  # 日志级别：debug, info, warning, error
    include_headers: bool = False  # 是否包含请求头
    include_body: bool = False  # 是否包含请求体
    include_response: bool = False  # 是否包含响应体

    model_config = SettingsConfigDict(
        extra="allow"
    )


class ResponseTimeConfig(BaseSettings):
    """响应时间配置"""

    enabled: bool = True
    buckets: list[float] = [0.1, 0.5, 1.0, 2.0, 5.0]  # 响应时间桶（秒）
    slow_request_threshold: float = 1.0  # 慢请求阈值（秒）

    model_config = SettingsConfigDict(
        extra="allow"
    )


class MiddlewareConfig(BaseSettings):
    """中间件配置"""

    rate_limit: RateLimitConfig = RateLimitConfig()
    circuit_breaker: CircuitBreakerConfig = CircuitBreakerConfig()
    request_log: RequestLogConfig = RequestLogConfig()
    response_time: ResponseTimeConfig = ResponseTimeConfig()

    model_config = SettingsConfigDict(
        extra="allow"
    )
