import gzip
import pickle
import secrets
import time
from typing import Any

# 导入 yitool 的 yi_cache
from yitool.yi_cache import YiCacheFactory, YiCacheType

from .config import YiSessionConfig, yi_default_session_config


class YiMemorySessionStorage:
    """内存会话存储"""

    def __init__(self, config: YiSessionConfig = yi_default_session_config):
        """
        初始化内存会话存储
        
        Args:
            config: 会话配置
        """
        self.config = config
        self._sessions: dict[str, bytes] = {}  # 使用压缩存储
        self._expires: dict[str, float] = {}
        self._memory_limit = 100 * 1024 * 1024  # 默认内存限制：100MB
        self._memory_usage = 0  # 当前内存使用量（字节）
        self._cleanup_probability = 0.1  # 10%的概率进行清理
        self._last_cleanup = time.time()  # 上次清理时间
        self._cleanup_interval = 60  # 清理间隔（秒）

    async def connect(self) -> None:
        """连接到存储（内存存储不需要实际连接）"""
        pass

    async def close(self) -> None:
        """关闭连接（内存存储不需要实际关闭）"""
        pass

    async def get_session(self, session_id: str) -> dict[str, Any] | None:
        """
        获取会话数据
        
        Args:
            session_id: 会话ID
        
        Returns:
            Optional[Dict[str, Any]]: 会话数据，如果会话不存在或已过期则返回None
        """
        # 检查是否需要清理
        if self._should_cleanup():
            self._clean_expired_sessions()

        if session_id in self._sessions and session_id in self._expires:
            # 更新会话过期时间
            self._expires[session_id] = time.time() + self.config.session_expire_time
            # 解压会话数据
            try:
                compressed_data = self._sessions[session_id]
                decompressed_data = gzip.decompress(compressed_data)
                return pickle.loads(decompressed_data)
            except Exception:
                # 解压失败，返回空会话
                return {}
        return None

    def _should_cleanup(self) -> bool:
        """
        检查是否需要进行会话清理
        
        Returns:
            bool: 是否需要清理
        """
        # 检查时间间隔
        if time.time() - self._last_cleanup > self._cleanup_interval:
            self._last_cleanup = time.time()
            return True

        # 检查概率清理
        return secrets.randbelow(100) < self._cleanup_probability * 100

    async def set_session(self, session_id: str, session_data: dict[str, Any]) -> None:
        """
        设置会话数据
        
        Args:
            session_id: 会话ID
            session_data: 会话数据
        """
        # 压缩会话数据
        try:
            serialized_data = pickle.dumps(session_data)
            compressed_data = gzip.compress(serialized_data)

            # 计算内存使用变化
            old_size = len(self._sessions[session_id]) if session_id in self._sessions else 0
            new_size = len(compressed_data)

            # 检查内存限制
            if self._memory_usage - old_size + new_size > self._memory_limit:
                # 内存不足，清理最旧的会话
                self._clean_oldest_sessions()

            # 更新存储和内存使用统计
            if session_id in self._sessions:
                self._memory_usage = self._memory_usage - old_size + new_size
            else:
                self._memory_usage += new_size

            self._sessions[session_id] = compressed_data
            self._expires[session_id] = time.time() + self.config.session_expire_time
        except Exception:
            # 压缩失败，使用未压缩存储
            self._sessions[session_id] = pickle.dumps(session_data)
            self._expires[session_id] = time.time() + self.config.session_expire_time

    async def delete_session(self, session_id: str) -> None:
        """
        删除会话数据
        
        Args:
            session_id: 会话ID
        """
        if session_id in self._sessions:
            # 更新内存使用统计
            self._memory_usage -= len(self._sessions[session_id])
            del self._sessions[session_id]
        if session_id in self._expires:
            del self._expires[session_id]

    async def update_session(self, session_id: str, session_data: dict[str, Any]) -> None:
        """
        更新会话数据
        
        Args:
            session_id: 会话ID
            session_data: 会话数据
        """
        current_data = await self.get_session(session_id)
        if current_data:
            current_data.update(session_data)
            await self.set_session(session_id, current_data)

    async def exists(self, session_id: str) -> bool:
        """
        检查会话是否存在
        
        Args:
            session_id: 会话ID
        
        Returns:
            bool: 会话存在返回True，否则返回False
        """
        # 清理过期会话
        self._clean_expired_sessions()
        return session_id in self._sessions

    def _clean_expired_sessions(self) -> None:
        """清理过期会话"""
        now = time.time()
        expired_session_ids = [session_id for session_id, expire_time in self._expires.items() if expire_time < now]

        for session_id in expired_session_ids:
            if session_id in self._sessions:
                # 更新内存使用统计
                self._memory_usage -= len(self._sessions[session_id])
                del self._sessions[session_id]
            if session_id in self._expires:
                del self._expires[session_id]

    def _clean_oldest_sessions(self) -> None:
        """清理最旧的会话以释放内存"""
        # 按过期时间排序，清理最早过期的会话
        sorted_sessions = sorted(self._expires.items(), key=lambda x: x[1])

        # 清理直到内存使用低于限制的 80%
        target_usage = self._memory_limit * 0.8

        for session_id, _ in sorted_sessions:
            if self._memory_usage <= target_usage:
                break

            if session_id in self._sessions:
                # 更新内存使用统计
                self._memory_usage -= len(self._sessions[session_id])
                del self._sessions[session_id]
            if session_id in self._expires:
                del self._expires[session_id]


class YiCacheSessionStorage:
    """基于 yitool yi_cache 的会话存储"""

    def __init__(self, config: YiSessionConfig = yi_default_session_config, cache_type: YiCacheType = YiCacheType.REDIS):
        """
        初始化基于 yi_cache 的会话存储
        
        Args:
            config: 会话配置
            cache_type: 缓存类型，默认为 REDIS
        """
        self.config = config
        self.cache_type = cache_type
        self.cache = YiCacheFactory.create(cache_type)

    async def connect(self) -> None:
        """连接到存储"""
        # yi_cache 会自动处理连接
        pass

    async def close(self) -> None:
        """关闭连接"""
        # yi_cache 会自动处理连接关闭
        pass

    async def get_session(self, session_id: str) -> dict[str, Any] | None:
        """
        获取会话数据
        
        Args:
            session_id: 会话ID
        
        Returns:
            Optional[Dict[str, Any]]: 会话数据，如果会话不存在或已过期则返回None
        """
        key = f"session:{session_id}"
        session_data = self.cache.get(key)

        if session_data:
            # 更新过期时间
            self.cache.set(key, session_data, expire=self.config.session_expire_time)
            return session_data
        return None

    async def set_session(self, session_id: str, session_data: dict[str, Any]) -> None:
        """
        设置会话数据
        
        Args:
            session_id: 会话ID
            session_data: 会话数据
        """
        key = f"session:{session_id}"
        self.cache.set(key, session_data, expire=self.config.session_expire_time)

    async def delete_session(self, session_id: str) -> None:
        """
        删除会话数据
        
        Args:
            session_id: 会话ID
        """
        key = f"session:{session_id}"
        self.cache.delete(key)

    async def update_session(self, session_id: str, session_data: dict[str, Any]) -> None:
        """
        更新会话数据
        
        Args:
            session_id: 会话ID
            session_data: 会话数据
        """
        current_data = await self.get_session(session_id)
        if current_data:
            current_data.update(session_data)
            await self.set_session(session_id, current_data)

    async def exists(self, session_id: str) -> bool:
        """
        检查会话是否存在
        
        Args:
            session_id: 会话ID
        
        Returns:
            bool: 会话存在返回True，否则返回False
        """
        key = f"session:{session_id}"
        return self.cache.exists(key)


# 创建全局会话存储实例
yi_session_storage = YiMemorySessionStorage()
