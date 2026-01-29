# 发布到 PyPI 指南

本文档说明如何将 `video-batch-trim` 发布到 PyPI。

## 前置要求

1. 注册 PyPI 账户
   - 访问 https://pypi.org/account/register/ 注册账户
   - 如果要发布到测试仓库，访问 https://test.pypi.org/account/register/

2. 安装发布工具

```bash
# 使用 uv（推荐）
uv pip install build twine

# 或使用 pip
pip install build twine
```

## 发布步骤

### 1. 更新版本号

在 `pyproject.toml` 和 `setup.py` 中更新版本号：

```toml
version = "0.1.0"  # 改为新版本号，如 "0.1.1"
```

### 2. 构建分发包

```bash
# 使用 build 工具（推荐）
python -m build

# 或使用 uv
uv build
```

这会在 `dist/` 目录生成：
- `video-batch-trim-0.1.0.tar.gz` (源分发包)
- `video_batch_trim-0.1.0-py3-none-any.whl` (wheel 包)

### 3. 检查分发包

```bash
# 使用 twine 检查
twine check dist/*

# 查看要上传的文件列表
twine upload --repository testpypi dist/* --dry-run
```

### 4. 上传到测试仓库（推荐先测试）

```bash
# 上传到 TestPyPI
twine upload --repository testpypi dist/*

# 测试安装
pip install --index-url https://test.pypi.org/simple/ video-batch-trim
```

### 5. 上传到正式 PyPI

```bash
# 上传到正式 PyPI
twine upload dist/*

# 安装验证
pip install video-batch-trim
```

## 使用 token 认证（推荐）

1. 在 PyPI 账户设置中创建 API token：https://pypi.org/manage/account/token/
2. 创建 `~/.pypirc` 文件：

```ini
[pypi]
username = __token__
password = pypi-你的token-这里

[testpypi]
username = __token__
password = pypi-你的测试token-这里
```

或者直接在命令行中使用环境变量：

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-your-token-here
twine upload dist/*
```

## 更新项目信息

在 `pyproject.toml` 中，请更新以下 URL：

```toml
[project.urls]
Homepage = "https://github.com/yourusername/video-batch-trim"  # 改为实际的 GitHub 地址
Documentation = "https://github.com/yourusername/video-batch-trim#readme"
Repository = "https://github.com/yourusername/video-batch-trim"
Issues = "https://github.com/yourusername/video-batch-trim/issues"
```

## 验证发布

发布后，访问以下 URL 验证：

- PyPI: https://pypi.org/project/video-batch-trim/
- 测试 PyPI: https://test.pypi.org/project/video-batch-trim/

## 后续更新

1. 更新版本号
2. 更新 `CHANGELOG.md`（如有）
3. 运行 `python -m build`
4. 运行 `twine upload dist/*`

## 故障排除

- **错误：文件已存在** - 需要升级版本号
- **错误：认证失败** - 检查 token 是否正确
- **错误：缺少必要字段** - 检查 `pyproject.toml` 是否完整

## 参考资料

- [Python 打包用户指南](https://packaging.python.org/en/latest/)
- [Twine 文档](https://twine.readthedocs.io/)
- [PyPI 使用指南](https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/)
