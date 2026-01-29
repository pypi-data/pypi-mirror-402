"""工具函数模块"""

import random
from pathlib import Path
from typing import List
from loguru import logger


# 支持的视频格式（常见视频格式扩展名）
VIDEO_EXTENSIONS = {
    # 最常见的格式
    ".mp4", ".avi", ".mkv", ".mov", ".flv", ".wmv", ".m4v", ".ts",
    # MPEG 系列
    ".mpg", ".mpeg", ".m2v", ".vob", ".m2ts",
    # 移动设备格式
    ".3gp", ".3g2", ".f4v",
    # Web 格式
    ".webm", ".ogv", ".ogg",
    # RealMedia 格式
    ".rm", ".rmvb",
    # Windows Media 格式
    ".asf", ".wtv",
    # 其他格式
    ".mts", ".mxf", ".divx", ".xvid", ".vro", ".dat", ".amv", ".drc",
    ".gifv", ".svi", ".viv", ".nsv",
}


def scan_video_files(input_dir: str) -> List[Path]:
    """
    递归扫描输入目录下的所有视频文件
    
    Args:
        input_dir: 输入目录路径
        
    Returns:
        视频文件路径列表（绝对路径）
    """
    input_path = Path(input_dir)
    video_files = []
    
    logger.info(f"开始扫描视频文件: {input_path}")
    
    # 递归遍历所有文件
    for file_path in input_path.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in VIDEO_EXTENSIONS:
            video_files.append(file_path.resolve())
            logger.debug(f"找到视频文件: {file_path}")
    
    logger.info(f"扫描完成，共找到 {len(video_files)} 个视频文件")
    
    return video_files


def get_unique_filename(output_dir: str, filename: str) -> Path:
    """
    生成唯一的文件名，如果文件已存在则添加随机 5 位数字
    
    Args:
        output_dir: 输出目录
        filename: 原始文件名（包含扩展名）
        
    Returns:
        唯一的文件路径
    """
    output_path = Path(output_dir)
    file_path = output_path / filename
    
    # 如果文件不存在，直接返回
    if not file_path.exists():
        return file_path
    
    # 文件存在，需要生成新文件名
    logger.warning(f"文件名冲突: {filename}，生成新文件名")
    
    # 分离文件名和扩展名
    stem = file_path.stem
    suffix = file_path.suffix
    
    # 尝试生成唯一文件名（最多尝试 100 次）
    max_attempts = 100
    for _ in range(max_attempts):
        # 生成 5 位随机数字
        random_suffix = f"_{random.randint(10000, 99999)}"
        new_filename = f"{stem}{random_suffix}{suffix}"
        new_path = output_path / new_filename
        
        if not new_path.exists():
            logger.debug(f"生成新文件名: {new_filename}")
            return new_path
    
    # 如果 100 次都失败（极不可能），使用时间戳
    import time
    timestamp = int(time.time())
    new_filename = f"{stem}_{timestamp}{suffix}"
    new_path = output_path / new_filename
    logger.warning(f"使用时间戳生成文件名: {new_filename}")
    
    return new_path


def run_ffmpeg(
    ffmpeg_path: str,
    input_file: Path,
    output_file: Path,
    trim_seconds: float,
) -> bool:
    """
    使用 ffmpeg 裁剪视频
    
    Args:
        ffmpeg_path: ffmpeg 可执行文件路径
        input_file: 输入视频文件路径
        output_file: 输出视频文件路径
        trim_seconds: 要删除的开头秒数
        
    Returns:
        是否成功
    """
    import subprocess
    
    # 构建 ffmpeg 命令
    # -ss: 跳过开头的秒数
    # -i: 输入文件
    # -c copy: 使用流复制，不重新编码（速度快）
    # -y: 自动覆盖输出文件（虽然我们已经处理了文件名冲突，但保留此选项更安全）
    cmd = [
        ffmpeg_path,
        "-ss", str(trim_seconds),
        "-i", str(input_file),
        "-c", "copy",
        "-y",
        str(output_file),
    ]
    
    logger.debug(f"执行命令: {' '.join(cmd)}")
    
    try:
        # 执行命令，捕获输出
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,  # 不自动抛出异常，我们自己处理
        )
        
        if result.returncode == 0:
            logger.success(f"处理成功: {input_file.name} -> {output_file.name}")
            return True
        else:
            error_msg = result.stderr or result.stdout or "未知错误"
            logger.error(f"ffmpeg 处理失败: {input_file.name}")
            logger.debug(f"错误信息: {error_msg}")
            return False
            
    except Exception as e:
        logger.exception(f"执行 ffmpeg 时发生异常: {input_file.name}")
        return False
