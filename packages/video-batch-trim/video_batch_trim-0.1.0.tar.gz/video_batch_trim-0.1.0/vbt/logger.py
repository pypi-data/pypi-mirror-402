"""日志配置模块 - 使用 loguru"""

from loguru import logger
import sys
from pathlib import Path


def setup_logger():
    """配置 loguru 日志系统"""
    # 移除默认处理器
    logger.remove()

    # 创建 logs 目录（如果不存在）
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # 添加控制台处理器
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO",
        colorize=True,
    )

    # 添加文件处理器
    logger.add(
        logs_dir / "vbt_{time}.log",
        rotation="10 MB",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        encoding="utf-8",
    )

    return logger


# 初始化日志系统
setup_logger()
