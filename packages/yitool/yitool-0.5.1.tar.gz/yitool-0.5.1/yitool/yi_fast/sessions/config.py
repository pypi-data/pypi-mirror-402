
from pydantic import BaseModel, Field


class YiSessionConfig(BaseModel):
    """会话配置"""

    secret_key: str = Field(
        default="your-secret-key-here",
        description="会话加密密钥，生产环境中应使用随机生成的密钥"
    )

    cookie_name: str = Field(
        default="session_id",
        description="会话Cookie名称"
    )

    cookie_max_age: int = Field(
        default=86400,  # 24小时
        description="会话Cookie最大过期时间（秒）"
    )

    cookie_path: str = Field(
        default="/",
        description="会话Cookie路径"
    )

    cookie_domain: str | None = Field(
        default=None,
        description="会话Cookie域名"
    )

    cookie_secure: bool = Field(
        default=False,
        description="是否仅通过HTTPS传输会话Cookie"
    )

    cookie_httponly: bool = Field(
        default=True,
        description="是否仅通过HTTP传输会话Cookie，防止XSS攻击"
    )

    cookie_samesite: str = Field(
        default="lax",
        description="会话Cookie SameSite策略"
    )

    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis连接URL"
    )

    redis_pool_size: int = Field(
        default=10,
        description="Redis连接池大小"
    )

    redis_max_connections: int = Field(
        default=50,
        description="Redis最大连接数"
    )

    session_expire_time: int = Field(
        default=86400,  # 24小时
        description="会话默认过期时间（秒）"
    )

    session_absolute_expire_time: int | None = Field(
        default=604800,  # 7天
        description="会话绝对过期时间（秒），无论活动与否"
    )

    session_idle_timeout: int | None = Field(
        default=1800,  # 30分钟
        description="会话空闲超时时间（秒），用户无活动后过期"
    )

    session_id_length: int = Field(
        default=32,
        description="会话ID长度"
    )


# 创建默认会话配置
yi_default_session_config = YiSessionConfig()
