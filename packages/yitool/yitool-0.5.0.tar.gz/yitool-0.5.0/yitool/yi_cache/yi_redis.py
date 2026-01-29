from __future__ import annotations

import redis

from yitool.const import __ENV__
from yitool.enums import DB_TYPE
from yitool.log import logger
from yitool.utils.dict_utils import DictUtils
from yitool.utils.env_utils import EnvUtils


class YiRedis(redis.Redis):
    def __init__(self, host: str, port: int = 6379, db: int = 0, password: str | None = None, **kwargs) -> None:
        super().__init__(host=host, port=port, db=db, password=password, **kwargs)
        logger.debug(f"Connected to Redis at {host}:{port}, DB: {db}")

    def clear(self, pattern: str | None = None) -> int:
        if not pattern:
            return 0
        cursor: int = 0
        total_deleted: int = 0
        while True:
            cursor, keys = self.scan(cursor=cursor, match=pattern)
            if keys:
                self.delete(*keys)
                total_deleted += len(keys)
            if cursor == 0:
                break
        return total_deleted

    def hclear(self, name: str) -> int:
        """清空hash表"""
        result = self.delete(name)
        return 1 if result else 0

    @staticmethod
    def load_env_values(values: dict[str, str]) -> dict[str, str]:
        db_type = DB_TYPE.REDIS.value.upper()
        return {
            "host": DictUtils.get_value_or_raise(values, f"{db_type}_HOST"),
            "port": DictUtils.get(values, f"{db_type}_PORT", default="6379"),
            "db": DictUtils.get(values, f"{db_type}_DB", default="0"),
            "password": DictUtils.get(values, f"{db_type}_PASSWORD"),
        }

    @classmethod
    def from_env(cls, env_path: str | None = __ENV__) -> YiRedis:
        values = EnvUtils.dotenv_values(env_path)
        redis_values = cls.load_env_values(values)
        try:
            return cls(
                host=redis_values["host"],
                port=int(redis_values["port"]),
                db=int(redis_values["db"]),
                password=redis_values["password"]
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize YiRedis from environment variables: {e}") from e



