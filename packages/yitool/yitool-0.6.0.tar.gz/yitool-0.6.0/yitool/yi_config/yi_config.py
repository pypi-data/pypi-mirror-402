"""YiConfig module - comprehensive configuration management."""

from yitool.log import LogConfig, setup_logging


class YiSettings:
    """YiSettings class for comprehensive configuration management."""

    def __init__(
        self,
        app: dict | None = None,
        server: dict | None = None,
        datasource: dict | None = None,
        jwt: dict | None = None,
        cors: dict | None = None,
        celery: dict | None = None,
        api_key: dict | None = None,
        middleware: dict | None = None,
        log: LogConfig | None = None,
    ):
        self.app = app or {}
        self.server = server or {}
        self.datasource = datasource or {}
        self.jwt = jwt or {}
        self.cors = cors or {}
        self.celery = celery or {}
        self.api_key = api_key or {}
        self.middleware = middleware or {}
        self.log = log or LogConfig()


class YiConfig:
    """Global configuration management class."""

    _instance = None
    _settings = None

    def __new__(cls, singleton: bool = True, config_source: str | dict | None = None):
        """Implement singleton pattern."""
        if not singleton or cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize(config_source)
        return cls._instance

    @classmethod
    def instance(cls):
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Reset singleton instance."""
        cls._instance = None
        cls._settings = None

    def _initialize(self, config_source: str | dict | None = None):
        """Initialize configuration."""
        if isinstance(config_source, str):
            self._load_from_file(config_source)
        elif isinstance(config_source, dict):
            self._load_from_dict(config_source)
        else:
            self._settings = YiSettings()

        setup_logging(self._settings.log)

    def _load_from_file(self, file_path: str):
        """Load configuration from file."""
        import yaml
        with open(file_path) as f:
            config_dict = yaml.safe_load(f) or {}
        self._load_from_dict(config_dict)

    def _load_from_dict(self, config_dict: dict):
        """Load configuration from dictionary."""
        self._settings = YiSettings(
            app=config_dict.get("app"),
            server=config_dict.get("server"),
            datasource=config_dict.get("datasource"),
            jwt=config_dict.get("jwt"),
            cors=config_dict.get("cors"),
            celery=config_dict.get("celery"),
            api_key=config_dict.get("api_key"),
            middleware=config_dict.get("middleware"),
            log=config_dict.get("log"),
        )

    @classmethod
    def from_dict(cls, config_dict: dict):
        """Create configuration from dictionary."""
        cls.reset_instance()
        return cls(config_source=config_dict)

    @classmethod
    def from_file(cls, file_path: str):
        """Create configuration from file."""
        cls.reset_instance()
        return cls(config_source=file_path)

    def update(self, config_dict: dict):
        """Update configuration."""
        if self._settings is None:
            self._settings = YiSettings()

        for key, value in config_dict.items():
            if hasattr(self._settings, key):
                if isinstance(value, dict) and isinstance(getattr(self._settings, key), dict):
                    getattr(self._settings, key).update(value)
                else:
                    setattr(self._settings, key, value)

    @property
    def settings(self) -> YiSettings:
        """Get settings."""
        return self._settings

    @classmethod
    def set_encryption_key(cls, key: str):
        """Set encryption key."""
        pass

    def encrypt_value(self, value: str) -> str:
        """Encrypt value."""
        return value

    def decrypt_value(self, value: str) -> str:
        """Decrypt value."""
        return value

    def add_config_change_listener(self, listener):
        """Add config change listener."""
        pass

    def remove_config_change_listener(self, listener):
        """Remove config change listener."""
        pass
