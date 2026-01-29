"""CLI 入口和主命令组"""

import click

# 导入日志配置（确保日志系统已初始化）
from vbt.logger import setup_logger

# 导入命令
from vbt.commands.trim import trim


@click.group()
@click.version_option(version="0.1.0", prog_name="vbt")
def cli():
    """vbt - 视频批量处理工具"""
    # 确保日志系统已初始化
    setup_logger()
    pass


# 注册子命令
cli.add_command(trim)


if __name__ == "__main__":
    cli()
