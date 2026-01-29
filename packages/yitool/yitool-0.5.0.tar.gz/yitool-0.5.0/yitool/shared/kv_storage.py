from __future__ import annotations

import os
import pickle
import threading
import time
from threading import Thread
from typing import Any, TypeVar

from cachetools import Cache

from yitool.exceptions import YiException
from yitool.log import logger
from yitool.utils.env_utils import EnvUtils
from yitool.utils.path_utils import PathUtils

KT = TypeVar("KT")
VT = TypeVar("VT")


class KVStorage[KT, VT](Cache):
    """基于pickle的持久化键值存储类，支持定时自动持久化"""

    def __init__(self,
                 maxsize: int = 1000000,
                 name: str = "kv_storage",
                 auto_save: bool = True,
                 save_interval: int = 10) -> None:
        """初始化键值存储

        Args:
            maxsize: 存储的最大容量，默认为100000
            name: 存储名称，用于标识持久化文件，默认为"kv_storage"
            auto_save: 是否启用自动保存，默认为True
            save_interval: 自动保存的时间间隔（秒），默认为10秒
        """
        super().__init__(maxsize)
        self._name = name
        self._auto_save = auto_save
        self._save_interval = save_interval

        # 只使用保存锁保护保存操作
        self._save_lock = threading.Lock()   # 用于保护保存操作

        self._dirty = False  # 标记数据是否被修改需要保存
        self._stopped = False  # 标记后台线程是否停止

        # 获取存储目录和路径
        self._storage_dir = self._get_storage_dir()
        self._storage_path = self._get_storage_path()

        # 尝试从文件加载已保存的数据
        self.load()

        # 启动后台保存线程
        if self._auto_save:
            self._start_background_saver()

    def _get_storage_dir(self) -> str:
        """获取存储目录"""
        app_storage_dir = "YI_APP_STORAGE_DIR"
        # 首先尝试从环境变量获取
        env_values = EnvUtils.dotenv_values()
        storage_dir = env_values.get(app_storage_dir)
        if storage_dir is None:
            raise YiException(f"{app_storage_dir} not set in environment variables")
        if not PathUtils.exists(storage_dir):
            try:
                os.makedirs(storage_dir, exist_ok=True)
            except Exception as e:
                logger.error(f"Failed to create storage directory: {e}")
                raise YiException(f"Failed to create storage directory: {e}") from e
        return storage_dir

    def _get_storage_path(self) -> str:
        """获取持久化文件路径"""
        return PathUtils.join(self._storage_dir, f"{self._name}.pickle")

    def _start_background_saver(self) -> None:
        """启动后台保存线程"""
        def saver_thread():
            while not self._stopped:
                time.sleep(self._save_interval)
                if self._dirty:
                    self._save_data()

        self._saver_thread = Thread(target=saver_thread, daemon=True, name=f"kv_storage_{self._name}_saver")
        self._saver_thread.start()
        logger.debug(f"Background saver thread started for '{self._name}' with interval {self._save_interval}s")

    def _save_data(self) -> bool:
        """内部保存方法，由后台线程调用

        Returns:
            操作是否成功
        """
        # 使用单独的锁保护保存操作
        if not self._save_lock.acquire(blocking=False):
            logger.debug(f"Save operation already in progress for '{self._name}'")
            return False

        try:
            # 创建临时文件路径
            temp_path = f"{self._storage_path}.tmp"

            # 直接获取数据快照
            data_snapshot = dict(self)
            self._dirty = False  # 标记为已保存

            # 写入数据到临时文件
            with open(temp_path, "wb") as f:
                pickle.dump(data_snapshot, f)

            # 原子性替换文件
            os.replace(temp_path, self._storage_path)

            logger.debug(f"KVStorage '{self._name}' saved to {self._storage_path}, {len(data_snapshot)} items")
            return True
        except Exception as e:
            logger.error(f"Failed to save KVStorage '{self._name}': {e}")
            # 保存失败，重新标记为脏数据
            self._dirty = True
            return False
        finally:
            self._save_lock.release()

    def save(self) -> bool:
        """立即保存数据到文件

        Returns:
            操作是否成功
        """
        return self._save_data()

    def load(self) -> bool:
        """从文件加载内容到当前存储

        Returns:
            操作是否成功
        """
        if not PathUtils.exists(self._storage_path):
            logger.debug(f"Storage file not found: {self._storage_path}")
            return False

        try:
            # 先读取文件内容
            with open(self._storage_path, "rb") as f:
                data = pickle.load(f)

            # 直接更新内存数据
            super().clear()
            for key, value in data.items():
                super().__setitem__(key, value)
            self._dirty = False  # 加载的数据是干净的

            logger.debug(f"KVStorage '{self._name}' loaded from {self._storage_path}, {len(data)} items")
            return True
        except Exception as e:
            logger.error(f"Failed to load KVStorage '{self._name}': {e}")
            return False

    def __setitem__(self, key: KT, value: VT) -> None:
        """设置键值对"""
        super().__setitem__(key, value)
        if self._auto_save:
            self._dirty = True  # 标记为需要保存，但不立即保存

    def __delitem__(self, key: KT) -> None:
        """删除键值对"""
        super().__delitem__(key)
        if self._auto_save:
            self._dirty = True  # 标记为需要保存，但不立即保存

    def __getitem__(self, key: KT) -> VT:
        """获取键对应的值"""
        return super().__getitem__(key)

    def __contains__(self, key: KT) -> bool:
        """检查键是否存在"""
        return super().__contains__(key)

    @property
    def name(self) -> str:
        """获取存储名称"""
        return self._name

    @property
    def size(self) -> int:
        """获取当前存储的键值对数量"""
        return len(self)

    def clear(self) -> None:
        """清空存储"""
        super().clear()
        if self._auto_save:
            self._dirty = True  # 标记为需要保存，但不立即保存

    def set(self, key: KT, value: VT) -> None:
        """设置键值对的便捷方法"""
        self[key] = value

    def get(self, key: KT, default: Any | None = None) -> Any:
        """获取键对应的值，如果键不存在则返回默认值"""
        try:
            return self[key]
        except KeyError:
            return default

    def delete(self, key: KT) -> bool:
        """删除键值对，如果键存在则返回True"""
        if key in self:
            del self[key]
            return True
        return False

    def contains(self, key: KT) -> bool:
        """检查键是否存在"""
        return key in self

    def to_dict(self) -> dict[KT, VT]:
        """将当前存储转换为字典"""
        return dict(self)

    def disable_auto_save(self) -> None:
        """禁用自动保存"""
        self._auto_save = False

    def enable_auto_save(self) -> None:
        """启用自动保存"""
        if not self._auto_save:
            self._auto_save = True
            # 如果之前没有启动后台线程，则启动它
            if not hasattr(self, "_saver_thread") or not self._saver_thread.is_alive():
                self._start_background_saver()

    def set_save_interval(self, interval: int) -> None:
        """设置自动保存的时间间隔

        Args:
            interval: 时间间隔（秒）
        """
        if interval > 0:
            self._save_interval = interval
            logger.debug(f"Save interval for '{self._name}' set to {interval}s")

    def __del__(self):
        """析构函数，确保数据被保存"""
        # 标记后台线程停止
        self._stopped = True

        # 如果有未保存的数据，尝试在析构时保存
        if self._auto_save and self._dirty:
            try:
                self.save()
            except Exception as e:
                logger.error(f"Failed to save data during cleanup for '{self._name}': {e}")

    def shutdown(self):
        """关闭存储，确保数据被保存"""
        self._stopped = True
        if self._auto_save and self._dirty:
            self.save()
        logger.debug(f"KVStorage '{self._name}' shutdown")
