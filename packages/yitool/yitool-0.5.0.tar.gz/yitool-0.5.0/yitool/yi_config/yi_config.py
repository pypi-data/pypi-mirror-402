import os
import threading
import time
from collections.abc import Callable
from typing import Any

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

from yitool.log import LogConfig, info, setup_logging, warning
from yitool.utils.crypto_utils import CryptoUtils
from yitool.utils.dict_utils import DictUtils
from yitool.yi_config.api_key import APIKeyConfig
from yitool.yi_config.app import AppConfig
from yitool.yi_config.celery import CeleryConfig
from yitool.yi_config.cors import CORSConfig
from yitool.yi_config.database import DatabaseConfig
from yitool.yi_config.datasource import DataSourceConfig
from yitool.yi_config.jwt import JWTConfig
from yitool.yi_config.middleware import MiddlewareConfig
from yitool.yi_config.server import ServerConfig


class YiSettings(BaseSettings):
    app: AppConfig
    server: ServerConfig
    database: DatabaseConfig | None = None
    datasource: DataSourceConfig
    jwt: JWTConfig | None = None
    cors: CORSConfig = CORSConfig()
    celery: CeleryConfig | None = None
    api_key: APIKeyConfig | None = None
    middleware: MiddlewareConfig = MiddlewareConfig()
    log: LogConfig = LogConfig()

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="allow",
        validate_assignment=True
    )
    
    @classmethod
    def model_validate(cls, obj):
        """增强模型验证，提供更详细的错误信息"""
        try:
            return super().model_validate(obj)
        except Exception as e:
            # 提供更详细的错误信息
            error_msg = f"Configuration validation error: {e}"
            info(error_msg)
            raise ValueError(error_msg) from e
    
    def model_post_init(self, __context):
        """模型初始化后进行额外验证"""
        super().model_post_init(__context)
        # 执行额外的验证逻辑
        self._validate_config_integrity()
    
    def _validate_config_integrity(self):
        """验证配置的完整性和一致性"""
        # 示例：验证数据库配置和数据源配置的一致性
        if self.database and not self.datasource:
            warning("Database config provided but no datasource config found")
        
        # 示例：验证CORS配置的安全性
        if self.cors.origins == ["*"] and not self.jwt:
            warning("CORS allows all origins (*) but no JWT config provided, consider adding authentication")
        
        # 示例：验证日志配置
        if self.log.level < 20 and self.app.environment == "production":
            warning("Debug logging enabled in production environment")


class YiConfig:
    """全局配置管理类，实现单例模式"""

    _instance = None

    # 配置缓存，避免重复加载相同的配置文件
    _config_cache = {}
    _datasource_cache = {}
    
    # 文件监控相关
    _file_watcher_thread = None
    _file_watcher_running = False
    _file_modification_times = {}
    _reload_interval = 5  # 检查间隔（秒）
    
    # 配置变更事件监听器
    _config_change_listeners: list[Callable[[dict[str, Any]], None]] = []
    
    # 加密相关
    _encryption_key = None
    _encrypted_prefix = "encrypted:"
    
    @classmethod
    def set_encryption_key(cls, key: str):
        """设置加密密钥

        Args:
            key: 加密密钥字符串
        """
        cls._encryption_key = key
        info("Encryption key set for sensitive configurations")
    
    @classmethod
    def get_encryption_key(cls) -> str | None:
        """获取加密密钥

        Returns:
            加密密钥字符串或None
        """
        return cls._encryption_key

    @classmethod
    def reset_instance(cls):
        """重置单例实例，用于测试"""
        cls._instance = None
        cls._settings = None
        cls._config_cache.clear()
        cls._datasource_cache.clear()
        cls._file_watcher_running = False
        cls._file_modification_times.clear()
        cls._config_change_listeners.clear()

    def __new__(cls, config_source: str | dict | None = None):
        """实现单例模式，强制使用单例

        Args:
            config_source: 配置源，可以是文件路径字符串或配置字典
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize(config_source)
        return cls._instance

    @classmethod
    def instance(cls, allow_fallback: bool = False):
        """获取单例实例

        Args:
            allow_fallback: 是否允许降级到默认配置，False 时初始化失败会抛出异常

        Returns:
            YiConfig 单例实例

        Raises:
            RuntimeError: 当 allow_fallback=False 且初始化失败时抛出
        """
        if cls._instance is None:
            try:
                cls._instance = YiConfig.from_file("application.yaml")
            except Exception as e:
                if allow_fallback:
                    error_type = type(e).__name__
                    info(f"Configuration error ({error_type}), using default configuration: {e}")
                    cls._instance = cls(config_source={})
                else:
                    error_messages = {
                        FileNotFoundError: "Configuration file not found",
                        yaml.YAMLError: "Invalid YAML format in configuration file",
                        ValueError: "Configuration validation error",
                        PermissionError: "Permission denied"
                    }
                    error_msg = error_messages.get(type(e), "Unexpected error")
                    raise RuntimeError(
                        f"Failed to initialize YiConfig: {error_msg} - {e}. "
                        "Please check your configuration files."
                    ) from e
        return cls._instance

    def _initialize(self, config_source: str | dict | None = None):
        """初始化配置

        Args:
            config_source: 配置源，可以是文件路径字符串或配置字典
        """
        # 根据配置源类型加载配置
        if isinstance(config_source, str):
            # 从指定文件加载配置
            self._load_from_file(config_source)
        elif isinstance(config_source, dict):
            # 从字典加载配置
            self._load_from_dict(config_source)
        else:
            # 默认行为：从文件系统加载
            yaml_config = self.load_yaml_config()
            datasource_config = self.load_datasource_config()
            self._set_settings(yaml_config, datasource_config)

        # 初始化日志系统
        setup_logging(self._settings.log)
        
        # 启动文件监控
        self.start_file_watcher()

    def start_file_watcher(self):
        """启动文件监控线程"""
        if not self._file_watcher_running:
            self._file_watcher_running = True
            self._file_watcher_thread = threading.Thread(
                target=self._watch_config_files,
                daemon=True
            )
            self._file_watcher_thread.start()
            info("Configuration file watcher started")

    def stop_file_watcher(self):
        """停止文件监控线程"""
        self._file_watcher_running = False
        if self._file_watcher_thread:
            self._file_watcher_thread.join(timeout=2)
        info("Configuration file watcher stopped")

    def _watch_config_files(self):
        """监控配置文件变化"""
        while self._file_watcher_running:
            try:
                # 检查主要配置文件
                env = os.getenv("__YI_ENV__", "dev")
                config_files = [
                    "application.yml",
                    f"application.{env}.yml",
                    "datasource.yml"
                ]
                
                # 检查文件是否有变化
                files_changed = False
                for file_path in config_files:
                    if os.path.exists(file_path):
                        current_mtime = os.path.getmtime(file_path)
                        if file_path not in self._file_modification_times:
                            self._file_modification_times[file_path] = current_mtime
                        elif current_mtime != self._file_modification_times[file_path]:
                            self._file_modification_times[file_path] = current_mtime
                            files_changed = True
                            info(f"Configuration file changed: {file_path}")
                
                # 如果有文件变化，重新加载配置
                if files_changed:
                    self._reload_config()
                    
            except Exception as e:
                warning(f"Error in file watcher: {e}")
            
            # 等待一段时间后再次检查
            time.sleep(self._reload_interval)

    def _reload_config(self):
        """重新加载配置"""
        try:
            info("Reloading configuration...")
            
            # 清空缓存
            self._config_cache.clear()
            self._datasource_cache.clear()
            
            # 重新加载配置
            yaml_config = self.load_yaml_config()
            datasource_config = self.load_datasource_config()
            self._set_settings(yaml_config, datasource_config)
            
            # 重新初始化日志系统
            setup_logging(self._settings.log)
            
            # 触发配置变更事件
            self._notify_config_change()
            
            info("Configuration reloaded successfully")
        except Exception as e:
            warning(f"Error reloading configuration: {e}")

    def _notify_config_change(self):
        """通知配置变更事件"""
        config_dict = {
            "app": self._settings.app.model_dump(),
            "server": self._settings.server.model_dump(),
            "database": self._settings.database.model_dump() if self._settings.database else None,
            "datasource": self._settings.datasource.model_dump(),
            "jwt": self._settings.jwt.model_dump() if self._settings.jwt else None,
            "cors": self._settings.cors.model_dump(),
            "celery": self._settings.celery.model_dump() if self._settings.celery else None,
            "api_key": self._settings.api_key.model_dump() if self._settings.api_key else None,
            "middleware": self._settings.middleware.model_dump(),
            "log": self._settings.log.model_dump()
        }
        
        for listener in self._config_change_listeners:
            try:
                listener(config_dict)
            except Exception as e:
                warning(f"Error in config change listener: {e}")
    
    def encrypt_value(self, value: str) -> str:
        """加密敏感配置值

        Args:
            value: 原始值

        Returns:
            加密后的值，带有前缀标记
        """
        if not self._encryption_key:
            warning("Encryption key not set, returning value as-is")
            return value
        
        try:
            # 使用AES加密
            encrypted_data, iv = CryptoUtils.aes_encrypt(value, self._encryption_key)
            # 将加密数据和IV转换为base64字符串
            encrypted_str = CryptoUtils.base64_encode(encrypted_data)
            iv_str = CryptoUtils.base64_encode(iv)
            # 组合成一个字符串
            combined = f"{encrypted_str}:{iv_str}"
            return f"{self._encrypted_prefix}{combined}"
        except Exception as e:
            warning(f"Error encrypting value: {e}")
            return value
    
    def decrypt_value(self, value: str) -> str:
        """解密敏感配置值

        Args:
            value: 加密的值（带有前缀标记）

        Returns:
            解密后的值
        """
        if not value.startswith(self._encrypted_prefix):
            return value
        
        if not self._encryption_key:
            warning("Encryption key not set, returning encrypted value")
            return value
        
        try:
            # 移除前缀
            encrypted_part = value[len(self._encrypted_prefix):]
            # 分离加密数据和IV
            encrypted_str, iv_str = encrypted_part.split(":", 1)
            # 解码base64
            encrypted_data = CryptoUtils.base64_decode(encrypted_str)
            iv = CryptoUtils.base64_decode(iv_str)
            # 使用AES解密
            decrypted_data = CryptoUtils.aes_decrypt(encrypted_data, self._encryption_key, iv)
            return decrypted_data.decode("utf-8")
        except Exception as e:
            warning(f"Error decrypting value: {e}")
            return value
    
    def _decrypt_config_values(self, config: dict) -> dict:
        """递归解密配置字典中的所有加密值

        Args:
            config: 配置字典

        Returns:
            解密后的配置字典
        """
        if not isinstance(config, dict):
            return config
        
        decrypted_config = {}
        for key, value in config.items():
            if isinstance(value, str):
                decrypted_config[key] = self.decrypt_value(value)
            elif isinstance(value, dict):
                decrypted_config[key] = self._decrypt_config_values(value)
            else:
                decrypted_config[key] = value
        
        return decrypted_config
    
    def load_from_env(self, prefix: str = "YI_") -> dict:
        """从环境变量加载配置

        Args:
            prefix: 环境变量前缀，默认为 YI_

        Returns:
            配置字典
        """
        config = {}
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # 移除前缀并转换为小写
                config_key = key[len(prefix):].lower()
                # 处理嵌套配置，如 YI_APP_NAME -> app.name
                parts = config_key.split("_")
                current = config
                
                for i, part in enumerate(parts):
                    if i == len(parts) - 1:
                        # 处理不同类型的环境变量值
                        if "," in value:
                            # 尝试解析为列表
                            current[part] = [item.strip() for item in value.split(",")]
                        elif "=" in value and not value.startswith("[") and not value.startswith("{"):
                            # 尝试解析为字典
                            current[part] = dict(item.strip().split("=") for item in value.split(","))
                        else:
                            # 尝试解析为适当的类型
                            current[part] = value
                    else:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
        
        return config
    
    def merge_with_env(self, config: dict, prefix: str = "YI_") -> dict:
        """将环境变量配置合并到现有配置中

        Args:
            config: 现有配置字典
            prefix: 环境变量前缀，默认为 YI_

        Returns:
            合并后的配置字典
        """
        env_config = self.load_from_env(prefix)
        if env_config:
            info(f"Merging environment configuration with prefix: {prefix}")
            return DictUtils.deep_merge(config, env_config)
        return config

    def add_config_change_listener(self, listener: Callable[[dict[str, Any]], None]):
        """添加配置变更监听器

        Args:
            listener: 配置变更回调函数
        """
        self._config_change_listeners.append(listener)

    def remove_config_change_listener(self, listener: Callable[[dict[str, Any]], None]):
        """移除配置变更监听器

        Args:
            listener: 要移除的监听器函数
        """
        if listener in self._config_change_listeners:
            self._config_change_listeners.remove(listener)

    def _get_datasource_config(self, config_dict: dict) -> dict:
        """获取数据源配置，提供默认值

        Args:
            config_dict: 配置字典

        Returns:
            dict: 数据源配置
        """
        datasource_config = config_dict.get("datasource", {})
        if not datasource_config:
            try:
                # 尝试从默认datasource.yml加载
                return self.load_datasource_config()
            except Exception:
                # 返回默认配置
                return {
                    "master": {
                        "url": "sqlite+aiosqlite:///:memory:",
                        "pool_size": 5,
                        "max_overflow": 10
                    }
                }
        return datasource_config

    def _load_from_file(self, file_path: str):
        """从指定文件加载配置

        Args:
            file_path: 配置文件路径
        """
        with open(file_path) as f:
            config_dict = yaml.safe_load(f) or {}

        # 获取数据源配置
        datasource_config = self._get_datasource_config(config_dict)

        self._set_settings(config_dict, datasource_config)

    def _load_from_dict(self, config_dict: dict):
        """从字典加载配置

        Args:
            config_dict: 配置字典
        """
        config_dict = config_dict or {}

        # 获取数据源配置
        datasource_config = self._get_datasource_config(config_dict)

        self._set_settings(config_dict, datasource_config)

    def _process_config(self, config_dict: dict, datasource_config: dict) -> tuple[dict, dict]:
        """处理配置：解密和合并环境变量

        Args:
            config_dict: 配置字典
            datasource_config: 数据源配置字典

        Returns:
            tuple[dict, dict]: 处理后的配置字典和数据源配置字典
        """
        # 确保配置字典存在
        config_dict = config_dict or {}
        datasource_config = datasource_config or {}
        
        # 解密配置值
        config_dict = self._decrypt_config_values(config_dict)
        datasource_config = self._decrypt_config_values(datasource_config)
        
        # 合并环境变量配置
        config_dict = self.merge_with_env(config_dict)
        datasource_config = self.merge_with_env(datasource_config, prefix="YI_DATASOURCE_")
        
        return config_dict, datasource_config

    def _set_settings(self, yaml_config: dict, datasource_config: dict):
        # 处理配置
        yaml_config, datasource_config = self._process_config(yaml_config, datasource_config)
        
        # 使用默认值或空字典，确保不会因为缺少键而报错
        self._settings = YiSettings(
            app=AppConfig(**yaml_config.get("app", {})),
            server=ServerConfig(**yaml_config.get("server", {})),
            database=DatabaseConfig(**yaml_config.get("database", {})) if yaml_config.get("database") else None,
            datasource=DataSourceConfig(**datasource_config),
            jwt=JWTConfig(**yaml_config.get("jwt", {})) if yaml_config.get("jwt") else None,
            cors=CORSConfig(**(yaml_config.get("cors", {}) or {})),
            celery=CeleryConfig(**yaml_config.get("celery", {})) if yaml_config.get("celery") else None,
            api_key=APIKeyConfig(**yaml_config.get("api_key", {})) if yaml_config.get("api_key") else None,
            middleware=MiddlewareConfig(**yaml_config.get("middleware", {})),
            log=LogConfig(**yaml_config.get("log", {})),
        )

    def load_yaml_config(self) -> dict:
        """Load configuration from YAML file, supporting environment-specific configs.

        Priority: environment-specific config > default config
        Environment is determined by __YI_ENV__ environment variable, defaulting to "dev"
        """
        # Get environment from env var, default to "dev"
        env = os.getenv("__YI_ENV__", "dev")

        # 构建缓存键
        cache_key = f"{env}:yaml"

        # 检查缓存
        if cache_key in self._config_cache:
            return self._config_cache[cache_key]

        # Default config file path
        default_config_path = "application.yml"

        # Environment-specific config file path
        env_config_path = f"application.{env}.yml"

        # Load default config
        config: dict = {}
        try:
            with open(default_config_path) as f:
                config = yaml.safe_load(f) or {}
        except FileNotFoundError:
            pass

        # Load and merge environment-specific config if it exists
        try:
            with open(env_config_path) as f:
                env_config = yaml.safe_load(f)
                if env_config:
                    # Merge environment config into default config
                    config = DictUtils.deep_merge(config, env_config)
        except FileNotFoundError:
            pass

        # 缓存结果
        self._config_cache[cache_key] = config

        return config

    def load_datasource_config(self, file_path: str = "datasource.yml") -> dict:
        """Load datasource configuration from YAML file."""
        # 检查缓存
        if file_path in self._datasource_cache:
            return self._datasource_cache[file_path]

        try:
            with open(file_path) as f:
                config = yaml.safe_load(f)
                if isinstance(config, dict):
                    if "datasource" in config:
                        result = config["datasource"]
                    else:
                        # 直接使用配置文件内容作为数据源配置
                        result = config
                else:
                    # 配置文件格式不正确，返回默认配置
                    result = {
                        "master": {
                            "url": "sqlite+aiosqlite:///:memory:",
                            "pool_size": 5,
                            "max_overflow": 10
                        }
                    }
        except FileNotFoundError:
            # 文件不存在，返回默认配置
            result = {
                "master": {
                    "url": "sqlite+aiosqlite:///:memory:",
                    "pool_size": 5,
                    "max_overflow": 10
                }
            }
        except Exception:
            # 其他异常，返回默认配置
            result = {
                "master": {
                    "url": "sqlite+aiosqlite:///:memory:",
                    "pool_size": 5,
                    "max_overflow": 10
                }
            }

        # 缓存结果
        self._datasource_cache[file_path] = result

        return result

    @property
    def settings(self) -> YiSettings:
        """获取全局 settings 实例"""
        return self._settings

    def __getattr__(self, name: str):
        """允许直接访问配置属性，如 config.app 而不是 config.settings.app"""
        if hasattr(self._settings, name):
            return getattr(self._settings, name)
        raise AttributeError(f"YiConfig has no attribute '{name}'")

    def get(self, key: str, default: Any = None):
        """通过点路径访问配置值

        Args:
            key: 配置键，支持点路径，如 'app.name'
            default: 默认值，当配置不存在时返回

        Returns:
            Any: 配置值或默认值
        """
        parts = key.split(".")
        current = self._settings
        
        for part in parts:
            if hasattr(current, part):
                current = getattr(current, part)
            else:
                return default
        
        return current

    def set(self, key: str, value: Any):
        """通过点路径设置配置值

        Args:
            key: 配置键，支持点路径，如 'app.name'
            value: 配置值

        Returns:
            bool: True 表示设置成功，False 表示设置失败
        """
        parts = key.split(".")
        current = self._settings
        
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                if hasattr(current, part):
                    setattr(current, part, value)
                    return True
                else:
                    return False
            else:
                if hasattr(current, part):
                    current = getattr(current, part)
                else:
                    return False

    def has(self, key: str) -> bool:
        """检查配置键是否存在

        Args:
            key: 配置键，支持点路径，如 'app.name'

        Returns:
            bool: True 表示配置键存在，False 表示不存在
        """
        parts = key.split(".")
        current = self._settings
        
        for part in parts:
            if hasattr(current, part):
                current = getattr(current, part)
            else:
                return False
        
        return True

    def to_dict(self) -> dict:
        """将配置转换为字典

        Returns:
            dict: 配置字典
        """
        return {
            "app": self._settings.app.model_dump() if self._settings.app else None,
            "server": self._settings.server.model_dump() if self._settings.server else None,
            "database": self._settings.database.model_dump() if self._settings.database else None,
            "datasource": self._settings.datasource.model_dump() if self._settings.datasource else None,
            "jwt": self._settings.jwt.model_dump() if self._settings.jwt else None,
            "cors": self._settings.cors.model_dump() if self._settings.cors else None,
            "celery": self._settings.celery.model_dump() if self._settings.celery else None,
            "api_key": self._settings.api_key.model_dump() if self._settings.api_key else None,
            "middleware": self._settings.middleware.model_dump() if self._settings.middleware else None,
            "log": self._settings.log.model_dump() if self._settings.log else None,
        }

    def update(self, config_dict: dict):
        """更新配置

        Args:
            config_dict: 新的配置字典，用于更新现有配置
        """
        # 合并现有配置和新配置
        current_config = {
            "app": self._settings.app.model_dump(),
            "server": self._settings.server.model_dump(),
            "database": self._settings.database.model_dump() if self._settings.database else None,
            "jwt": self._settings.jwt.model_dump() if self._settings.jwt else None,
            "cors": self._settings.cors.model_dump() if self._settings.cors else None,
            "celery": self._settings.celery.model_dump() if self._settings.celery else None,
            "api_key": self._settings.api_key.model_dump() if self._settings.api_key else None,
        }

        # 过滤掉 None 值
        current_config = {k: v for k, v in current_config.items() if v is not None}

        # 合并新配置
        merged_config = DictUtils.deep_merge(current_config, config_dict)

        # 重新设置配置，保持现有数据源配置
        datasource_config = self._settings.datasource.model_dump() if self._settings.datasource else {}
        self._set_settings(merged_config, datasource_config)
        
        # 触发配置变更事件
        self._notify_config_change()

    def _with_config(self, config_name: str, config_class, **kwargs) -> "YiConfig":
        """链式配置方法的通用实现

        Args:
            config_name: 配置名称
            config_class: 配置类
            **kwargs: 配置参数

        Returns:
            YiConfig: 配置实例，用于链式调用
        """
        setattr(self._settings, config_name, config_class(**kwargs))
        # 特殊处理日志配置
        if config_name == "log":
            setup_logging(self._settings.log)
        return self

    def with_database(self, **kwargs) -> "YiConfig":
        """设置数据库配置（链式 API）

        Args:
            **kwargs: 数据库配置参数

        Returns:
            YiConfig: 配置实例，用于链式调用
        """
        return self._with_config("database", DatabaseConfig, **kwargs)

    def with_jwt(self, **kwargs) -> "YiConfig":
        """设置 JWT 配置（链式 API）

        Args:
            **kwargs: JWT 配置参数

        Returns:
            YiConfig: 配置实例，用于链式调用
        """
        return self._with_config("jwt", JWTConfig, **kwargs)

    def with_cors(self, **kwargs) -> "YiConfig":
        """设置 CORS 配置（链式 API）

        Args:
            **kwargs: CORS 配置参数

        Returns:
            YiConfig: 配置实例，用于链式调用
        """
        return self._with_config("cors", CORSConfig, **kwargs)

    def with_celery(self, **kwargs) -> "YiConfig":
        """设置 Celery 配置（链式 API）

        Args:
            **kwargs: Celery 配置参数

        Returns:
            YiConfig: 配置实例，用于链式调用
        """
        return self._with_config("celery", CeleryConfig, **kwargs)

    def with_log(self, **kwargs) -> "YiConfig":
        """设置日志配置（链式 API）

        Args:
            **kwargs: 日志配置参数

        Returns:
            YiConfig: 配置实例，用于链式调用
        """
        return self._with_config("log", LogConfig, **kwargs)

    @classmethod
    def from_file(cls, file_path: str) -> "YiConfig":
        """从指定文件创建配置实例

        Args:
            file_path: 配置文件路径

        Returns:
            YiConfig: 配置实例
        """
        return cls(config_source=file_path)

    @classmethod
    def from_dict(cls, config_dict: dict) -> "YiConfig":
        """从字典创建配置实例

        Args:
            config_dict: 配置字典

        Returns:
            YiConfig: 配置实例
        """
        return cls(config_source=config_dict)
