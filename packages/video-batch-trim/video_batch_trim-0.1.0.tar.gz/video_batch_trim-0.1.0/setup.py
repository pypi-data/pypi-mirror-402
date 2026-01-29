"""
setup.py - 兼容性设置文件

注意：此项目使用 pyproject.toml 进行配置（PEP 517/518）。
此 setup.py 仅用于向后兼容旧版工具。
实际构建配置请参考 pyproject.toml。
"""

from setuptools import setup

# 读取 README 文件
try:
    with open("README.md", "r", encoding="utf-8") as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "视频批量裁剪命令行工具"

setup(
    name="video-batch-trim",
    version="0.1.0",
    description="视频批量裁剪命令行工具 - 使用 ffmpeg 批量删除视频开头指定秒数",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="VBT Developer",
    license="MIT",
    python_requires=">=3.8",
    packages=["vbt", "vbt.commands"],
    install_requires=[
        "click>=8.0",
        "pyyaml>=6.0",
        "tqdm>=4.65",
        "loguru>=0.7.0",
    ],
    entry_points={
        "console_scripts": [
            "vbt=vbt.cli:cli",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Video",
        "Topic :: Utilities",
    ],
    keywords="video ffmpeg trim batch video-processing cli command-line",
    project_urls={
        "Homepage": "https://github.com/yourusername/video-batch-trim",
        "Documentation": "https://github.com/yourusername/video-batch-trim#readme",
        "Repository": "https://github.com/yourusername/video-batch-trim",
        "Issues": "https://github.com/yourusername/video-batch-trim/issues",
    },
)
