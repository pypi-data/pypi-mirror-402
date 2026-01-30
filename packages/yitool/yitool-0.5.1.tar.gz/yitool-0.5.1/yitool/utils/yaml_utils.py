from __future__ import annotations

import yaml

from yitool.exceptions import YiException
from yitool.log import logger
from yitool.utils.path_utils import PathUtils


class YamlUtils:
    @staticmethod
    def load(yaml_file: str):
        """加载YAML文件并将内容作为字典返回。

        参数:
            yaml_file: YAML文件的路径

        返回:
            加载的YAML内容作为字典

        异常:
            FileNotFoundError: 如果文件不存在
            YiException: 如果解析YAML文件时出错
        """
        PathUtils.raise_if_not_exists(yaml_file)
        with open(yaml_file, encoding="utf-8") as stream:
            try:
                return yaml.full_load(stream)
            except yaml.YAMLError as exc:
                logger.error(f"Error loading YAML file: {yaml_file}, {exc}")
                raise YiException(f"Failed to load YAML file: {yaml_file}. Error: {str(exc)}") from exc

    @staticmethod
    def dump(data: dict, yaml_file: str):
        """将字典写入YAML文件。

        参数:
            data: 要写入的字典数据
            yaml_file: 输出YAML文件的路径

        异常:
            YiException: 如果写入YAML文件时出错
        """
        with open(yaml_file, "w") as stream:
            try:
                yaml.dump(data, stream, encoding="utf-8")
            except Exception as exc:
                logger.error(f"Error dumping YAML file: {yaml_file}, {exc}")
                raise YiException(f"Failed to dump data to YAML file: {yaml_file}. Error: {str(exc)}") from exc
