"""安全工具函数模块"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import jwt
from passlib.context import CryptContext

# 密码上下文，用于密码哈希和验证
# 使用pbkdf2_sha256方案，它没有72字节的密码长度限制
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def generate_secret_key(length: int = 32) -> str:
    """生成随机密钥

    Args:
        length: 密钥长度，默认为32字节

    Returns:
        随机密钥字符串
    """
    return secrets.token_hex(length)


def hash_password(password: str) -> str:
    """哈希密码

    使用bcrypt算法对密码进行哈希处理

    Args:
        password: 原始密码字符串

    Returns:
        哈希后的密码字符串
    """
    # bcrypt只处理前72个字节的密码，超过的部分会被忽略
    # 为了避免bcrypt库抛出异常，我们主动截断密码
    return pwd_context.hash(password[:72])


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码

    验证原始密码与哈希密码是否匹配

    Args:
        plain_password: 原始密码字符串
        hashed_password: 哈希后的密码字符串

    Returns:
        密码是否匹配
    """
    # 与哈希时保持一致，只验证前72个字节
    return pwd_context.verify(plain_password[:72], hashed_password)


def generate_jwt(
    data: dict[str, Any],
    secret_key: str,
    algorithm: str = "HS256",
    expires_delta: timedelta | None = None
) -> str:
    """生成JWT令牌

    Args:
        data: 要编码到JWT中的数据
        secret_key: JWT密钥
        algorithm: 加密算法，默认为HS256
        expires_delta: 过期时间增量，默认为15分钟

    Returns:
        生成的JWT令牌字符串
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt


def decode_jwt(
    token: str,
    secret_key: str,
    algorithm: str = "HS256"
) -> dict[str, Any]:
    """解码JWT令牌

    Args:
        token: JWT令牌字符串
        secret_key: JWT密钥
        algorithm: 加密算法，默认为HS256

    Returns:
        解码后的JWT数据

    Raises:
        JWTError: JWT解码失败
    """
    return jwt.decode(token, secret_key, algorithms=[algorithm])


def create_hmac_signature(
    data: str,
    secret_key: str,
    algorithm: str = "sha256"
) -> str:
    """创建HMAC签名

    Args:
        data: 要签名的数据
        secret_key: 签名密钥
        algorithm: 签名算法，默认为sha256

    Returns:
        HMAC签名字符串
    """
    h = hmac.new(
        secret_key.encode("utf-8"),
        data.encode("utf-8"),
        hashlib.sha256
    )
    return h.hexdigest()


def verify_hmac_signature(
    data: str,
    signature: str,
    secret_key: str,
    algorithm: str = "sha256"
) -> bool:
    """验证HMAC签名

    Args:
        data: 原始数据
        signature: 要验证的签名
        secret_key: 签名密钥
        algorithm: 签名算法，默认为sha256

    Returns:
        签名是否有效
    """
    expected_signature = create_hmac_signature(data, secret_key, algorithm)
    return hmac.compare_digest(expected_signature, signature)


def sanitize_input(input_str: str) -> str:
    """清理输入字符串

    移除或转义潜在的危险字符

    Args:
        input_str: 原始输入字符串

    Returns:
        清理后的字符串
    """
    # 简单的HTML字符转义
    return (
        input_str
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
        .replace("/", "&#x2F;")
    )


def is_strong_password(password: str) -> tuple[bool, list[str]]:
    """检查密码强度

    验证密码是否符合强密码要求

    Args:
        password: 要检查的密码

    Returns:
        元组(是否强密码, 不符合要求的原因列表)
    """
    errors = []

    if len(password) < 8:
        errors.append("密码长度至少为8个字符")

    if not any(c.isupper() for c in password):
        errors.append("密码至少包含一个大写字母")

    if not any(c.islower() for c in password):
        errors.append("密码至少包含一个小写字母")

    if not any(c.isdigit() for c in password):
        errors.append("密码至少包含一个数字")

    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        errors.append("密码至少包含一个特殊字符")

    return len(errors) == 0, errors


def generate_otp(length: int = 6) -> str:
    """生成一次性密码(OTP)

    Args:
        length: OTP长度，默认为6位

    Returns:
        一次性密码字符串
    """
    return str(secrets.randbelow(10 ** length)).zfill(length)


def get_password_strength_score(password: str) -> int:
    """获取密码强度评分

    0-100分，分数越高表示密码越强

    Args:
        password: 要评分的密码

    Returns:
        密码强度评分
    """
    if not password:
        return 0

    score = 0
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    # 长度评分 (0-40分)
    password_len = len(password)
    if password_len >= 12:
        score += 40
    elif password_len >= 8:
        score += 20
    elif password_len >= 6:
        score += 10

    # 检查字符类型
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in special_chars for c in password)

    # 字符类型评分
    if has_upper:
        score += 10
    if has_lower:
        score += 10
    if has_digit:
        score += 10
    if has_special:
        score += 10

    # 多种字符类型奖励 (0-10分)
    char_types = sum([has_upper, has_lower, has_digit, has_special])
    if char_types > 1:
        score += min(char_types - 1, 1) * 10

    return max(score, 0)
