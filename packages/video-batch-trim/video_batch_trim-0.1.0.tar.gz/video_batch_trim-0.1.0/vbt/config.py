"""配置文件读取和验证模块"""

import yaml
from pathlib import Path
from typing import Dict, Any
import shutil
from loguru import logger


class ConfigError(Exception):
    """配置错误异常"""
    pass


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    加载并验证配置文件
    
    Args:
        config_path: 配置文件路径，默认为当前目录的 config.yaml
        
    Returns:
        配置字典
        
    Raises:
        ConfigError: 配置文件不存在或配置无效
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise ConfigError(f"配置文件不存在: {config_path}")
    
    logger.info(f"正在加载配置文件: {config_path}")
    
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"配置文件格式错误: {e}")
    except Exception as e:
        raise ConfigError(f"读取配置文件失败: {e}")
    
    # 验证必需字段
    required_fields = ["input_dir", "output_dir", "ffmpeg_path", "trim_seconds"]
    missing_fields = [field for field in required_fields if field not in config]
    
    if missing_fields:
        raise ConfigError(f"配置文件缺少必需字段: {', '.join(missing_fields)}")
    
    # 验证路径
    input_dir = Path(config["input_dir"]).expanduser().resolve()
    if not input_dir.exists():
        raise ConfigError(f"输入目录不存在: {input_dir}")
    if not input_dir.is_dir():
        raise ConfigError(f"输入路径不是目录: {input_dir}")
    
    logger.debug(f"输入目录: {input_dir}")
    
    # 验证输出目录（如果不存在则创建）
    output_dir = Path(config["output_dir"]).expanduser().resolve()
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"输出目录: {output_dir}")
    except Exception as e:
        raise ConfigError(f"无法创建输出目录 {output_dir}: {e}")
    
    # 验证 ffmpeg 路径
    ffmpeg_path = config["ffmpeg_path"]
    if not shutil.which(ffmpeg_path):
        # 如果是绝对路径，直接检查文件是否存在
        ffmpeg_abs = Path(ffmpeg_path).expanduser()
        if not ffmpeg_abs.exists() or not ffmpeg_abs.is_file():
            raise ConfigError(f"ffmpeg 可执行文件不存在或不可执行: {ffmpeg_path}")
        ffmpeg_path = str(ffmpeg_abs.resolve())
    else:
        ffmpeg_path = shutil.which(ffmpeg_path)
    
    logger.debug(f"ffmpeg 路径: {ffmpeg_path}")
    
    # 验证 trim_seconds
    try:
        trim_seconds = float(config["trim_seconds"])
        if trim_seconds < 0:
            raise ConfigError(f"trim_seconds 必须 >= 0，当前值: {trim_seconds}")
    except (ValueError, TypeError):
        raise ConfigError(f"trim_seconds 必须是数字，当前值: {config['trim_seconds']}")
    
    # 构建验证后的配置
    validated_config = {
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "ffmpeg_path": ffmpeg_path,
        "trim_seconds": trim_seconds,
    }
    
    logger.success(f"配置文件加载成功")
    logger.info(f"输入目录: {validated_config['input_dir']}")
    logger.info(f"输出目录: {validated_config['output_dir']}")
    logger.info(f"裁剪秒数: {validated_config['trim_seconds']} 秒")
    
    return validated_config
