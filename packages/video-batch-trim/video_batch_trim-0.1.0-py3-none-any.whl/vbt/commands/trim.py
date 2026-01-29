"""trim 子命令实现"""

import click
from pathlib import Path
from tqdm import tqdm
from loguru import logger

from vbt.config import load_config, ConfigError
from vbt.utils import scan_video_files, get_unique_filename, run_ffmpeg


@click.command()
@click.option(
    "--config",
    "-c",
    default="config.yaml",
    help="配置文件路径（默认: config.yaml）",
    type=click.Path(exists=False),
)
def trim(config: str):
    """裁剪视频开头指定秒数"""
    
    try:
        # 加载配置
        cfg = load_config(config)
        
        # 扫描视频文件
        video_files = scan_video_files(cfg["input_dir"])
        
        if not video_files:
            logger.warning("未找到任何视频文件")
            click.echo("未找到任何视频文件，请检查输入目录配置。")
            return
        
        # 统计信息
        success_count = 0
        failed_count = 0
        skipped_count = 0
        
        logger.info(f"开始处理 {len(video_files)} 个视频文件...")
        
        # 使用 tqdm 显示进度
        with tqdm(total=len(video_files), desc="处理视频", unit="个") as pbar:
            for video_file in video_files:
                try:
                    # 获取输出文件名（保持原文件名）
                    output_filename = video_file.name
                    
                    # 处理文件名冲突
                    output_path = get_unique_filename(
                        cfg["output_dir"],
                        output_filename
                    )
                    
                    # 如果文件名被修改，说明有冲突
                    if output_path.name != output_filename:
                        logger.warning(
                            f"文件名冲突，已重命名: {output_filename} -> {output_path.name}"
                        )
                    
                    # 执行 ffmpeg 裁剪
                    if run_ffmpeg(
                        cfg["ffmpeg_path"],
                        video_file,
                        output_path,
                        cfg["trim_seconds"],
                    ):
                        success_count += 1
                    else:
                        failed_count += 1
                        # 如果失败，删除可能创建的不完整文件
                        if output_path.exists():
                            try:
                                output_path.unlink()
                                logger.debug(f"已删除失败的文件: {output_path}")
                            except Exception as e:
                                logger.warning(f"删除失败文件时出错: {e}")
                
                except Exception as e:
                    logger.exception(f"处理文件时发生异常: {video_file}")
                    failed_count += 1
                
                finally:
                    pbar.update(1)
        
        # 显示处理摘要
        logger.info("=" * 50)
        logger.success(
            f"处理完成！成功: {success_count}, 失败: {failed_count}, 跳过: {skipped_count}"
        )
        logger.info("=" * 50)
        
        click.echo(f"\n处理完成！")
        click.echo(f"成功: {success_count} 个")
        click.echo(f"失败: {failed_count} 个")
        if skipped_count > 0:
            click.echo(f"跳过: {skipped_count} 个")
        
        if failed_count > 0:
            click.echo(f"\n失败的视频详细信息请查看日志文件: logs/vbt_*.log")
    
    except ConfigError as e:
        logger.error(f"配置错误: {e}")
        click.echo(f"错误: {e}", err=True)
        raise click.Abort()
    
    except KeyboardInterrupt:
        logger.warning("用户中断操作")
        click.echo("\n操作已取消")
        raise click.Abort()
    
    except Exception as e:
        logger.exception("处理过程中发生未预期的错误")
        click.echo(f"错误: {e}", err=True)
        raise click.Abort()
