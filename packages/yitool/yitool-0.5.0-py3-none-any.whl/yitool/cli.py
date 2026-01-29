"""命令行入口"""

from __future__ import annotations

import importlib
import sys
from os import path

import click

from yitool.const import __VERSION__
from yitool.log import logger, setup_logging

# 设置日志
setup_logging()


@click.group(invoke_without_command=True, help="功能丰富的 Python 工具包，让开发更高效、更简单")
@click.option("-h", "--help", is_flag=True, help="显示此命令的简要帮助")
@click.option("-v", "--version", is_flag=True, help="显示 yi 版本")
def cli(help, version):
    """主命令组"""
    if version:
        click.echo(f"yi v{__VERSION__}")
        return

    if help:
        click.echo(cli.get_help(click.Context(cli)))
        return

    # 如果没有提供命令，显示帮助
    click.echo(cli.get_help(click.Context(cli)))


# 工具模块映射
utils_commands = {
    "arr": ("arr_utils", "数组/列表处理工具"),
    "class": ("class_utils", "类操作工具"),
    "convert": ("convert_utils", "类型转换工具"),
    "date": ("date_utils", "日期时间工具"),
    "dict": ("dict_utils", "字典处理工具"),
    "env": ("env_utils", "环境变量工具"),
    "fun": ("fun_utils", "函数处理工具"),
    "id": ("id_utils", "ID 生成工具"),
    "json": ("json_utils", "JSON 处理工具"),
    "path": ("path_utils", "文件路径工具"),
    "random": ("random_utils", "随机数工具"),
    "str": ("str_utils", "字符串处理工具"),
    "system": ("system_utils", "系统信息工具"),
    "url": ("url_utils", "URL 处理工具"),
    "yaml": ("yaml_utils", "YAML 处理工具"),
}


def create_utils_command(cmd_name, module_name, help_text):
    """创建工具命令"""

    @cli.command(name=cmd_name, help=help_text)
    @click.argument("method")
    @click.argument("args", nargs=-1)
    @click.option("--kwargs", multiple=True, help="关键字参数，格式为 key=value")
    def utils_command(method, args, kwargs):
        """工具命令处理函数"""
        try:
            # 导入工具模块
            module = importlib.import_module(f"yitool.utils.{module_name}")
        except ImportError:
            logger.error(f"无法导入模块: {module_name}")
            sys.exit(1)

        # 获取工具类
        class_name = f'{module_name.split("_")[0].capitalize()}Utils'
        utils_class = getattr(module, class_name, None)
        if not utils_class:
            logger.error(f"在模块 {module_name} 中未找到类 {class_name}")
            sys.exit(1)

        # 获取方法
        method_name = method
        method = getattr(utils_class, method_name, None)
        if not method or not callable(method):
            logger.error(f"在类 {class_name} 中未找到可调用的方法 {method_name}")
            sys.exit(1)

        # 解析关键字参数
        parsed_kwargs = {}
        for kwarg in kwargs:
            if "=" in kwarg:
                key, value = kwarg.split("=", 1)
                parsed_kwargs[key] = value

        # 执行方法
        try:
            # 使用method_name而不是method.__name__，避免NoneType错误
            logger.info(f"执行工具方法: {module_name}.{class_name}.{method_name}")
            result = method(*args, **parsed_kwargs)
            if result is not None:
                click.echo(result)
        except Exception as e:
            logger.error(f"方法执行失败: {str(e)}")
            sys.exit(1)

    return utils_command


# 注册所有工具命令
for cmd_name, (module_name, help_text) in utils_commands.items():
    create_utils_command(cmd_name, module_name, help_text)


# 数据库命令组
@cli.group(help="数据库操作")
def db():
    """数据库命令组"""
    pass


@db.command(help="连接数据库")
@click.argument("args", nargs=-1)
def connect(args):
    """连接数据库"""
    logger.info(f"执行数据库连接操作: {args}")
    click.echo(f"数据库连接: {args}")


@db.command(help="执行查询")
@click.argument("args", nargs=-1)
def query(args):
    """执行查询"""
    logger.info(f"执行数据库查询操作: {args}")
    click.echo(f"数据库查询: {args}")


@db.command(help="插入数据")
@click.argument("args", nargs=-1)
def insert(args):
    """插入数据"""
    logger.info(f"执行数据库插入操作: {args}")
    click.echo(f"数据库插入: {args}")


@db.command(help="更新数据")
@click.argument("args", nargs=-1)
def update(args):
    """更新数据"""
    logger.info(f"执行数据库更新操作: {args}")
    click.echo(f"数据库更新: {args}")


@db.command(help="删除数据")
@click.argument("args", nargs=-1)
def delete(args):
    """删除数据"""
    logger.info(f"执行数据库删除操作: {args}")
    click.echo(f"数据库删除: {args}")


# Redis命令组
@cli.group(help="Redis操作")
def redis():
    """Redis命令组"""
    pass


@redis.command(help="获取Redis值")
@click.argument("args", nargs=-1)
def get(args):
    """获取Redis值"""
    logger.info(f"执行Redis获取操作: {args}")
    click.echo(f"Redis获取: {args}")


@redis.command(help="设置Redis值")
@click.argument("args", nargs=-1)
def set(args):
    """设置Redis值"""
    logger.info(f"执行Redis设置操作: {args}")
    click.echo(f"Redis设置: {args}")


@redis.command(help="删除Redis值")
@click.argument("args", nargs=-1)
def redis_delete(args):
    """删除Redis值"""
    logger.info(f"执行Redis删除操作: {args}")
    click.echo(f"Redis删除: {args}")


@redis.command(help="获取Redis键")
@click.argument("args", nargs=-1)
def keys(args):
    """获取Redis键"""
    logger.info(f"执行Redis键获取操作: {args}")
    click.echo(f"Redis键获取: {args}")


@redis.command(help="清空Redis")
@click.argument("args", nargs=-1)
def flush(args):
    """清空Redis"""
    logger.info(f"执行Redis清空操作: {args}")
    click.echo(f"Redis清空: {args}")


@cli.command(help="显示命令文档")
@click.argument("command", required=False)
def help(command):
    """显示命令文档"""
    if command:
        if command in cli.commands:
            click.echo(cli.commands[command].get_help(click.Context(cli.commands[command])))
        else:
            click.echo(f"未知命令: {command}")
            click.echo(cli.get_help(click.Context(cli)))
    else:
        click.echo(cli.get_help(click.Context(cli)))


@cli.command(help="解析配置文件")
@click.argument("file_path", required=False)
def parse_config_file(file_path):
    """解析配置文件"""
    from tornado import options

    if file_path is None or not path.exists(file_path):
        cli_conf = "cli.conf"
        file_path = path.join(path.dirname(__file__), cli_conf)
    options.parse_config_file(file_path)
    click.echo(f"已解析配置文件: {file_path}")


def main():
    """主入口函数"""
    # 解析配置文件（保持原有逻辑）
    from tornado import options
    cli_conf = "cli.conf"
    default_file_path = path.join(path.dirname(__file__), cli_conf)
    if path.exists(default_file_path):
        options.parse_config_file(default_file_path)

    # 执行CLI
    cli()


if __name__ == "__main__":
    main()
