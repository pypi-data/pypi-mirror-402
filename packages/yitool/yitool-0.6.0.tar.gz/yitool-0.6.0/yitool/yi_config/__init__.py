"""Configuration module - simplified with focused responsibilities."""

from .app import AppConfig
from .loader import load, load_env, load_yaml, merge_configs
from .settings import Settings
from .watcher import ConfigWatcher
from .yi_config import YiConfig, YiSettings

__all__ = [
    "AppConfig",
    "Settings",
    "ConfigWatcher",
    "YiConfig",
    "YiSettings",
    "load",
    "load_env",
    "load_yaml",
    "merge_configs",
]


# Legacy compatibility placeholder (for gradual migration)
class _LegacyConfig:
    """Placeholder for legacy config - use new APIs instead."""

    @property
    def settings(self) -> Settings:
        """Return empty settings for legacy compatibility."""
        return Settings()


config = _LegacyConfig()
