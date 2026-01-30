from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any

from tornado.escape import json_decode

from yitool.exceptions import YiException
from yitool.log import logger
from yitool.utils.path_utils import PathUtils


# Custom JSON encoder for handling datetime and date types
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        # Handle datetime objects
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
            # return obj.isoformat()
        # Handle date objects
        elif isinstance(obj, date):
            # return obj.isoformat()
            return obj.strftime("%Y-%m-%d")
        return super().default(obj)

class JsonUtils:
    """JSON工具类，提供处理JSON文件和数据的功能"""

    @staticmethod
    def load(json_file: str) -> Any:
        """从文件加载JSON数据

        参数:
            json_file: JSON文件的路径

        返回:
            加载的JSON数据（通常是字典或列表）

        异常:
            FileNotFoundError: 如果文件不存在
            YiException: 如果JSON解析失败
        """
        PathUtils.raise_if_not_exists(json_file)
        try:
            with open(json_file, encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as exc:
            logger.error(f"Failed to parse JSON file: {json_file}. Error: {str(exc)}")
            raise YiException(f"Failed to parse JSON file: {json_file}. Error: {str(exc)}") from exc
        except Exception as exc:
            logger.error(f"Error loading JSON file: {json_file}. Error: {str(exc)}")
            raise YiException(f"Error loading JSON file: {json_file}. Error: {str(exc)}") from exc

    @staticmethod
    def dump(json_file: str, data: dict[str, Any] | list | Any):
        """将数据保存到JSON文件

        参数:
            json_file: 输出JSON文件的路径
            data: 要保存的数据（必须是JSON可序列化的）

        异常:
            YiException: 如果保存数据失败
        """
        try:
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)
        except (TypeError, OverflowError) as exc:
            logger.error(f"Failed to serialize data to JSON. Error: {str(exc)}")
            raise YiException(f"Failed to serialize data to JSON. Error: {str(exc)}") from exc
        except Exception as exc:
            logger.error(f"Error writing to JSON file: {json_file}. Error: {str(exc)}")
            raise YiException(f"Error writing to JSON file: {json_file}. Error: {str(exc)}") from exc

    @staticmethod
    def json_decode(json_str: str) -> dict[str, Any]:
        """将JSON字符串解码为Python字典

        参数:
            json_str: JSON格式的字符串

        返回:
            解码后的Python字典

        异常:
            YiException: 如果解码失败
        """
        try:
            return json_decode(json_str)
        except Exception as exc:
            logger.error(f"Failed to decode JSON string. Error: {str(exc)}")
            raise YiException(f"Failed to decode JSON string. Error: {str(exc)}") from exc

    @staticmethod
    def json_encode(value: Any) -> str:
        """将Python对象编码为JSON字符串

        参数:
            value: 要编码的Python对象（必须是JSON可序列化的）

        返回:
            编码后的JSON字符串

        异常:
            YiException: 如果编码失败
        """
        try:
            return json.dumps(value, ensure_ascii=False, cls=DateTimeEncoder)
        except (TypeError, OverflowError) as exc:
            logger.error(f"Failed to encode data to JSON string. Error: {str(exc)}")
            raise YiException(f"Failed to encode data to JSON string. Error: {str(exc)}") from exc
