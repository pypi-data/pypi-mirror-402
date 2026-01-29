import base64
import hashlib
import json
import secrets
import time
from typing import Any

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from yitool.yi_cache import YiCacheFactory, YiCacheType

from .config import YiSessionConfig, yi_default_session_config
from .storage import YiMemorySessionStorage, yi_session_storage


class YiSessionManager:
    """会话管理器"""

    def __init__(
        self,
        config: YiSessionConfig = yi_default_session_config,
        storage: YiMemorySessionStorage = yi_session_storage
    ):
        """
        初始化会话管理器
        
        Args:
            config: 会话配置
            storage: 会话存储
        """
        self.config = config
        self.storage = storage
        # 确保密钥长度为 32 字节（256 位）
        self.encryption_key = self._ensure_key_length(config.secret_key)
        # 初始化会话监控统计
        self._stats = {
            "total_sessions": 0,
            "active_sessions": 0,
            "expired_sessions": 0,
            "created_sessions": 0,
            "deleted_sessions": 0,
            "session_accesses": 0,
            "encryption_failures": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "last_reset": time.time()
        }
        # 初始化会话缓存
        self._session_cache = YiCacheFactory.create(YiCacheType.MEMORY, config={"ttl": 300})

    def generate_session_id(self) -> str:
        """
        生成会话ID
        
        Returns:
            str: 会话ID
        """
        return secrets.token_urlsafe(self.config.session_id_length)

    def _ensure_key_length(self, key: str) -> bytes:
        """
        确保密钥长度为 32 字节（256 位）
        
        Args:
            key: 原始密钥
        
        Returns:
            bytes: 处理后的密钥
        """
        # 使用 SHA-256 哈希确保密钥长度为 32 字节
        return hashlib.sha256(key.encode()).digest()

    def _encrypt(self, data: dict[str, Any]) -> str:
        """
        加密会话数据
        
        Args:
            data: 会话数据
        
        Returns:
            str: 加密后的数据
        """
        # 序列化数据
        plaintext = json.dumps(data).encode()

        # 生成随机 IV
        iv = secrets.token_bytes(16)

        # 创建加密器
        cipher = Cipher(
            algorithms.AES(self.encryption_key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()

        # 填充数据
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(plaintext) + padder.finalize()

        # 加密数据
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()

        # 组合 IV 和密文
        encrypted = iv + ciphertext

        # Base64 编码
        return base64.b64encode(encrypted).decode()

    def _decrypt(self, encrypted_data: str) -> dict[str, Any]:
        """
        解密会话数据
        
        Args:
            encrypted_data: 加密后的数据
        
        Returns:
            Dict[str, Any]: 解密后的会话数据
        """
        # Base64 解码
        encrypted = base64.b64decode(encrypted_data.encode())

        # 提取 IV 和密文
        iv = encrypted[:16]
        ciphertext = encrypted[16:]

        # 创建解密器
        cipher = Cipher(
            algorithms.AES(self.encryption_key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()

        # 解密数据
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

        # 移除填充
        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()

        # 反序列化数据
        return json.loads(plaintext.decode())

    def get_stats(self) -> dict[str, Any]:
        """
        获取会话监控统计数据
        
        Returns:
            Dict[str, Any]: 会话统计数据
        """
        return self._stats

    def reset_stats(self) -> None:
        """重置会话监控统计数据"""
        self._stats = {
            "total_sessions": 0,
            "active_sessions": 0,
            "expired_sessions": 0,
            "created_sessions": 0,
            "deleted_sessions": 0,
            "session_accesses": 0,
            "encryption_failures": 0,
            "last_reset": time.time()
        }

    def generate_csrf_token(self) -> str:
        """
        生成 CSRF 令牌
        
        Returns:
            str: CSRF 令牌
        """
        return secrets.token_urlsafe(32)

    async def create_session(self, initial_data: dict[str, Any] | None = None) -> str:
        """
        创建新会话
        
        Args:
            initial_data: 初始会话数据
        
        Returns:
            str: 会话ID
        """
        session_id = self.generate_session_id()
        session_data = initial_data or {}
        # 生成 CSRF 令牌
        session_data["csrf_token"] = self.generate_csrf_token()
        # 添加时间戳
        current_time = time.time()
        session_data["created_at"] = current_time
        session_data["last_accessed"] = current_time
        # 加密会话数据
        encrypted_data = self._encrypt(session_data)
        await self.storage.set_session(session_id, {"encrypted_data": encrypted_data})

        # 更新统计数据
        self._stats["total_sessions"] += 1
        self._stats["active_sessions"] += 1
        self._stats["created_sessions"] += 1

        return session_id

    async def get_csrf_token(self, session_id: str) -> str | None:
        """
        获取会话的 CSRF 令牌
        
        Args:
            session_id: 会话ID
        
        Returns:
            Optional[str]: CSRF 令牌，如果会话不存在则返回 None
        """
        session_data = await self.get_session_data(session_id)
        if session_data:
            return session_data.get("csrf_token")
        return None

    async def regenerate_csrf_token(self, session_id: str) -> str | None:
        """
        重新生成 CSRF 令牌
        
        Args:
            session_id: 会话ID
        
        Returns:
            Optional[str]: 新的 CSRF 令牌，如果会话不存在则返回 None
        """
        session_data = await self.get_session_data(session_id)
        if session_data:
            # 生成新的 CSRF 令牌
            new_csrf_token = self.generate_csrf_token()
            session_data["csrf_token"] = new_csrf_token
            # 加密并存储
            encrypted_data = self._encrypt(session_data)
            await self.storage.set_session(session_id, {"encrypted_data": encrypted_data})
            # 更新缓存
            self._session_cache.set(session_id, session_data)
            return new_csrf_token
        return None

    async def validate_csrf_token(self, session_id: str, token: str) -> bool:
        """
        验证 CSRF 令牌
        
        Args:
            session_id: 会话ID
            token: 要验证的 CSRF 令牌
        
        Returns:
            bool: 验证成功返回 True，否则返回 False
        """
        session_data = await self.get_session_data(session_id)
        if session_data:
            return session_data.get("csrf_token") == token
        return False

    async def get_session_data(self, session_id: str) -> dict[str, Any] | None:
        """
        获取会话数据
        
        Args:
            session_id: 会话ID
        
        Returns:
            Optional[Dict[str, Any]]: 会话数据，如果会话不存在或已过期则返回None
        """
        current_time = time.time()

        # 尝试从缓存获取
        cached_data = self._session_cache.get(session_id)
        if cached_data:
            # 检查缓存中的会话是否过期
            if not self._is_session_expired(cached_data, current_time):
                # 缓存命中，更新最后访问时间
                cached_data["last_accessed"] = current_time
                self._session_cache.set(session_id, cached_data)
                # 加密并存储更新后的数据
                encrypted_data = self._encrypt(cached_data)
                await self.storage.set_session(session_id, {"encrypted_data": encrypted_data})
                # 更新统计数据
                self._stats["cache_hits"] += 1
                self._stats["session_accesses"] += 1
                return cached_data

        # 缓存未命中或已过期，从存储获取
        self._stats["cache_misses"] += 1
        self._stats["session_accesses"] += 1

        session_data = await self.storage.get_session(session_id)

        if session_data and "encrypted_data" in session_data:
            # 解密会话数据
            try:
                decrypted_data = self._decrypt(session_data["encrypted_data"])

                # 检查会话是否过期
                if self._is_session_expired(decrypted_data, current_time):
                    # 会话已过期，删除并返回None
                    await self.delete_session(session_id)
                    self._stats["expired_sessions"] += 1
                    if self._stats["active_sessions"] > 0:
                        self._stats["active_sessions"] -= 1
                    return None

                # 更新最后访问时间
                decrypted_data["last_accessed"] = current_time

                # 加密并存储更新后的数据
                encrypted_data = self._encrypt(decrypted_data)
                await self.storage.set_session(session_id, {"encrypted_data": encrypted_data})

                # 存入缓存
                self._session_cache.set(session_id, decrypted_data)

                return decrypted_data
            except Exception:
                # 解密失败，返回空会话
                self._stats["encryption_failures"] += 1
                return {}
        return session_data

    def _is_session_expired(self, session_data: dict[str, Any], current_time: float) -> bool:
        """
        检查会话是否过期
        
        Args:
            session_data: 会话数据
            current_time: 当前时间戳
        
        Returns:
            bool: 会话已过期返回True，否则返回False
        """
        # 检查绝对过期时间
        if self.config.session_absolute_expire_time and "created_at" in session_data:
            if current_time - session_data["created_at"] > self.config.session_absolute_expire_time:
                return True

        # 检查空闲超时
        if self.config.session_idle_timeout and "last_accessed" in session_data:
            if current_time - session_data["last_accessed"] > self.config.session_idle_timeout:
                return True

        # 检查默认过期时间
        if "created_at" in session_data:
            if current_time - session_data["created_at"] > self.config.session_expire_time:
                return True

        return False

    async def update_session(self, session_id: str, data: dict[str, Any]) -> None:
        """
        更新会话数据
        
        Args:
            session_id: 会话ID
            data: 要更新的会话数据
        """
        # 获取当前会话数据
        current_data = await self.get_session_data(session_id)
        if current_data:
            # 更新数据
            current_data.update(data)
            # 加密并存储
            encrypted_data = self._encrypt(current_data)
            await self.storage.set_session(session_id, {"encrypted_data": encrypted_data})
            # 更新缓存
            self._session_cache.set(session_id, current_data)

    async def delete_session(self, session_id: str) -> None:
        """
        删除会话
        
        Args:
            session_id: 会话ID
        """
        await self.storage.delete_session(session_id)
        # 清除缓存
        self._session_cache.delete(session_id)

        # 更新统计数据
        if self._stats["active_sessions"] > 0:
            self._stats["active_sessions"] -= 1
        self._stats["deleted_sessions"] += 1

    async def invalidate_session(self, session_id: str) -> None:
        """
        使会话失效
        
        Args:
            session_id: 会话ID
        """
        await self.storage.delete_session(session_id)
        # 清除缓存
        self._session_cache.delete(session_id)

        # 更新统计数据
        if self._stats["active_sessions"] > 0:
            self._stats["active_sessions"] -= 1
        self._stats["deleted_sessions"] += 1

    async def regenerate_session_id(self, session_id: str) -> str:
        """
        重新生成会话ID，保持会话数据不变
        
        Args:
            session_id: 旧会话ID
        
        Returns:
            str: 新会话ID
        """
        # 获取旧会话数据
        session_data = await self.get_session_data(session_id)
        if not session_data:
            # 如果旧会话不存在，创建新会话
            return await self.create_session()

        # 创建新会话并复制数据
        new_session_id = await self.create_session(session_data)

        # 删除旧会话和缓存
        await self.storage.delete_session(session_id)
        self._session_cache.delete(session_id)

        return new_session_id

    async def rotate_session_id(self, session_id: str) -> str:
        """
        轮换会话ID，用于定期轮换以防止会话固定攻击
        
        Args:
            session_id: 当前会话ID
        
        Returns:
            str: 新会话ID
        """
        return await self.regenerate_session_id(session_id)

    async def regenerate_session_on_auth(self, session_id: str, user_id: str) -> str:
        """
        在用户认证成功后重新生成会话ID，防止会话固定攻击
        
        Args:
            session_id: 当前会话ID
            user_id: 认证的用户ID
        
        Returns:
            str: 新会话ID
        """
        # 获取当前会话数据
        session_data = await self.get_session_data(session_id)
        if not session_data:
            # 如果会话不存在，创建新会话
            new_session_data = {"user_id": user_id, "authenticated": True}
            return await self.create_session(new_session_data)

        # 更新会话数据，标记为已认证
        session_data["user_id"] = user_id
        session_data["authenticated"] = True
        session_data["auth_time"] = time.time()

        # 创建新会话并复制数据
        new_session_id = await self.create_session(session_data)

        # 删除旧会话和缓存
        await self.storage.delete_session(session_id)
        self._session_cache.delete(session_id)

        return new_session_id


# 创建全局会话管理器实例
yi_session_manager = YiSessionManager()
