from __future__ import annotations

import configparser
import json
import os
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from yitool.log import logger

# 尝试导入外部库
TOMLI_AVAILABLE = False
try:
    import tomli
    TOMLI_AVAILABLE = True
except ImportError:
    pass

PYYAML_AVAILABLE = False
try:
    import yaml
    PYYAML_AVAILABLE = True
except ImportError:
    pass


class ConfigLoader(ABC):
    """配置加载器抽象基类"""

    @abstractmethod
    def load(self, file_path: str) -> dict[str, Any]:
        """加载配置文件

        Args:
            file_path: 配置文件路径

        Returns:
            配置字典
        """
        pass

    @abstractmethod
    def dump(self, config: dict[str, Any], file_path: str) -> bool:
        """保存配置到文件

        Args:
            config: 配置字典
            file_path: 配置文件路径

        Returns:
            是否保存成功
        """
        pass


class JsonConfigLoader(ConfigLoader):
    """JSON配置加载器"""

    def load(self, file_path: str) -> dict[str, Any]:
        """加载JSON配置文件"""
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)

    def dump(self, config: dict[str, Any], file_path: str) -> bool:
        """保存配置到JSON文件"""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save JSON config: {e}")
            return False


class YamlConfigLoader(ConfigLoader):
    """YAML配置加载器"""

    def __init__(self):
        if not PYYAML_AVAILABLE:
            raise ImportError("pyyaml is not installed. Please install it with: pip install pyyaml")

    def load(self, file_path: str) -> dict[str, Any]:
        """加载YAML配置文件"""
        with open(file_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def dump(self, config: dict[str, Any], file_path: str) -> bool:
        """保存配置到YAML文件"""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(config, f, ensure_ascii=False, default_flow_style=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save YAML config: {e}")
            return False


class IniConfigLoader(ConfigLoader):
    """INI配置加载器"""

    def load(self, file_path: str) -> dict[str, Any]:
        """加载INI配置文件"""
        config = configparser.ConfigParser()
        config.read(file_path, encoding="utf-8")

        # 转换为字典
        result = {}
        for section in config.sections():
            result[section] = dict(config[section])
        return result

    def dump(self, config: dict[str, Any], file_path: str) -> bool:
        """保存配置到INI文件"""
        try:
            ini_config = configparser.ConfigParser()
            for section, values in config.items():
                if isinstance(values, dict):
                    ini_config[section] = values

            with open(file_path, "w", encoding="utf-8") as f:
                ini_config.write(f)
            return True
        except Exception as e:
            logger.error(f"Failed to save INI config: {e}")
            return False


class TomlConfigLoader(ConfigLoader):
    """TOML配置加载器"""

    def __init__(self):
        if not TOMLI_AVAILABLE:
            raise ImportError("tomli is not installed. Please install it with: pip install tomli")

    def load(self, file_path: str) -> dict[str, Any]:
        """加载TOML配置文件"""
        with open(file_path, "rb") as f:
            return tomli.load(f)

    def dump(self, config: dict[str, Any], file_path: str) -> bool:
        """保存配置到TOML文件"""
        try:
            import tomli_w
            with open(file_path, "wb") as f:
                tomli_w.dump(config, f)
            return True
        except Exception as e:
            logger.error(f"Failed to save TOML config: {e}")
            return False


class ConfigUtils:
    """配置工具类，提供统一的配置管理接口"""

    # 支持的配置格式
    SUPPORTED_FORMATS = ["json", "yaml", "yml", "ini", "toml"]

    # 配置加载器映射
    LOADERS = {
        "json": JsonConfigLoader,
        "yaml": YamlConfigLoader,
        "yml": YamlConfigLoader,
        "ini": IniConfigLoader,
        "toml": TomlConfigLoader
    }

    def __init__(self):
        """初始化配置工具"""
        self.config = {}
        self.sources = []
        self._last_modified = {}  # 记录文件最后修改时间
        self._hot_reload_interval = 0  # 热更新间隔（秒）
        self._hot_reload_running = False  # 热更新是否运行中
        self._hot_reload_callbacks = []  # 热更新回调函数列表

    @staticmethod
    def _get_file_format(file_path: str) -> str:
        """获取文件格式

        Args:
            file_path: 文件路径

        Returns:
            文件格式
        """
        ext = os.path.splitext(file_path)[1].lower().lstrip(".")
        if ext not in ConfigUtils.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported file format: {ext}. Supported formats: {', '.join(ConfigUtils.SUPPORTED_FORMATS)}")
        return ext

    def _get_loader(self, file_path: str) -> ConfigLoader:
        """获取配置加载器

        Args:
            file_path: 配置文件路径

        Returns:
            配置加载器实例
        """
        format = self._get_file_format(file_path)
        loader_class = ConfigUtils.LOADERS[format]
        return loader_class()

    def _replace_env_vars(self, config: dict[str, Any]) -> dict[str, Any]:
        """替换配置中的环境变量

        Args:
            config: 配置字典

        Returns:
            替换后的配置字典
        """
        result = {}
        for key, value in config.items():
            if isinstance(value, dict):
                result[key] = self._replace_env_vars(value)
            elif isinstance(value, str):
                result[key] = os.path.expandvars(value)
            else:
                result[key] = value
        return result

    def _merge_dict(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """合并字典

        Args:
            base: 基础字典
            override: 覆盖字典

        Returns:
            合并后的字典
        """
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_dict(result[key], value)
            else:
                result[key] = value
        return result

    def load(self, file_path: str) -> dict[str, Any]:
        """加载单个配置文件

        Args:
            file_path: 配置文件路径

        Returns:
            配置字典
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Config file not found: {file_path}")

        logger.info(f"Loading config from: {file_path}")
        loader = self._get_loader(file_path)
        config = loader.load(file_path)
        config = self._replace_env_vars(config)

        # 记录文件最后修改时间
        self._last_modified[file_path] = os.path.getmtime(file_path)
        self.sources.append(file_path)

        return config

    def load_multiple(self, file_paths: list[str]) -> dict[str, Any]:
        """加载多个配置文件并合并

        Args:
            file_paths: 配置文件路径列表

        Returns:
            合并后的配置字典
        """
        merged_config = {}
        for file_path in file_paths:
            config = self.load(file_path)
            merged_config = self._merge_dict(merged_config, config)
        self.config = merged_config
        return merged_config

    def load_dir(self, dir_path: str) -> dict[str, Any]:
        """加载目录下的所有配置文件并合并

        Args:
            dir_path: 目录路径

        Returns:
            合并后的配置字典
        """
        if not os.path.exists(dir_path):
            raise FileNotFoundError(f"Config directory not found: {dir_path}")

        file_paths = []
        for root, _, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    format = self._get_file_format(file_path)
                    if format in ConfigUtils.SUPPORTED_FORMATS:
                        file_paths.append(file_path)
                except ValueError:
                    continue

        return self.load_multiple(file_paths)

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔路径

        Args:
            key: 配置键，支持点号分隔路径，如 "database.host"
            default: 默认值

        Returns:
            配置值或默认值
        """
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """设置配置值，支持点号分隔路径

        Args:
            key: 配置键，支持点号分隔路径，如 "database.host"
            value: 配置值
        """
        keys = key.split(".")
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save(self, file_path: str) -> bool:
        """保存配置到文件

        Args:
            file_path: 配置文件路径

        Returns:
            是否保存成功
        """
        try:
            loader = self._get_loader(file_path)
            return loader.dump(self.config, file_path)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False

    def _check_modifications(self):
        """检查配置文件是否修改"""
        modified = False
        for file_path in self.sources:
            if not os.path.exists(file_path):
                continue

            current_mtime = os.path.getmtime(file_path)
            if file_path not in self._last_modified or current_mtime > self._last_modified[file_path]:
                self._last_modified[file_path] = current_mtime
                modified = True

        if modified:
            # 重新加载配置
            self.load_multiple(self.sources)
            # 调用回调函数
            for callback in self._hot_reload_callbacks:
                try:
                    callback(self.config)
                except Exception as e:
                    logger.error(f"Error in hot reload callback: {e}")

    def _hot_reload_loop(self):
        """热更新循环"""
        while self._hot_reload_running:
            self._check_modifications()
            time.sleep(self._hot_reload_interval)

    def enable_hot_reload(self, interval: int = 5, callback: Callable[[dict[str, Any]], None] = None) -> None:
        """启用配置热更新

        Args:
            interval: 检查间隔（秒）
            callback: 配置变更回调函数
        """
        if callback:
            self._hot_reload_callbacks.append(callback)

        if self._hot_reload_running:
            logger.warning("Hot reload is already running")
            return

        self._hot_reload_interval = interval
        self._hot_reload_running = True
        logger.info(f"Hot reload enabled with interval: {interval} seconds")

        # 启动热更新线程
        import threading
        thread = threading.Thread(target=self._hot_reload_loop, daemon=True)
        thread.start()

    def disable_hot_reload(self) -> None:
        """禁用配置热更新"""
        self._hot_reload_running = False
        self._hot_reload_callbacks.clear()
        logger.info("Hot reload disabled")

    def get_config(self) -> dict[str, Any]:
        """获取完整配置

        Returns:
            完整配置字典
        """
        return self.config.copy()

    def clear(self) -> None:
        """清空配置"""
        self.config = {}
        self.sources = []
        self._last_modified.clear()
        self.disable_hot_reload()


# 创建全局配置工具实例
config = ConfigUtils()
