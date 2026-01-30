# DrissionPage MCP 发布指南

本指南将帮助你发布 DrissionPage MCP Server，让其他用户可以轻松使用。

## 目录
1. [发布前准备](#发布前准备)
2. [PyPI 发布](#pypi-发布)
3. [GitHub 发布](#github-发布)
4. [MCP 服务器注册](#mcp-服务器注册)
5. [文档和推广](#文档和推广)

---

## 发布前准备

### 1. 代码质量检查

运行所有质量检查工具：

```bash
# 代码格式化
black src/ tests/
isort src/ tests/

# 代码检查
flake8 src/ tests/

# 类型检查
mypy src/

# 运行测试
pytest tests/ --cov=src
```

### 2. 版本更新

更新版本号（遵循语义化版本 Semantic Versioning）：

**pyproject.toml**:
```toml
[project]
version = "0.1.0"  # 更新版本号
```

**src/cli.py**:
```python
parser.add_argument(
    "--version",
    action="version",
    version="%(prog)s 0.1.0"  # 更新版本号
)
```

**src/server.py**:
```python
def __init__(self, name: str = "DrissionPage MCP", version: str = "0.1.0"):
    # 更新版本号
```

### 3. 更新 README

确保 README.md 包含：
- 清晰的项目描述
- 安装说明
- 快速开始示例
- 功能列表
- 配置示例
- 常见问题解答

### 4. 创建 CHANGELOG

创建 `CHANGELOG.md` 记录版本变更：

```markdown
# Changelog

## [0.1.0] - 2024-01-22

### Added
- 初始版本发布
- 14 个浏览器自动化工具
- 支持导航、元素交互、截图等功能
- MCP 协议集成
- 完整的测试套件

### Fixed
- 修复方法缺失问题
- 修复 MCP SDK 集成
- 修复导入路径问题
```

---

## PyPI 发布

### 1. 准备发布文件

确保以下文件存在且正确：
- `pyproject.toml` - 项目配置
- `README.md` - 项目说明
- `LICENSE` - 许可证文件
- `requirements.txt` - 依赖列表

### 2. 构建分发包

```bash
# 安装构建工具
pip install build twine

# 清理旧构建
rm -rf dist/ build/ *.egg-info

# 构建分发包
python -m build
```

这将在 `dist/` 目录下生成：
- `drissionpage-mcp-0.1.0.tar.gz` (源码分发)
- `drissionpage_mcp-0.1.0-py3-none-any.whl` (wheel 分发)

### 3. 测试上传到 TestPyPI（推荐）

首先在 TestPyPI 测试上传：

```bash
# 上传到 TestPyPI
python -m twine upload --repository testpypi dist/*

# 测试安装
pip install --index-url https://test.pypi.org/simple/ drissionpage-mcp
```

### 4. 正式发布到 PyPI

确认测试无误后，发布到正式 PyPI：

```bash
# 上传到 PyPI
python -m twine upload dist/*
```

**注意**：你需要在 PyPI 注册账号并配置 API Token。

### 5. 配置 PyPI 凭证

创建 `~/.pypirc` 文件：

```ini
[pypi]
username = __token__
password = pypi-your-api-token-here

[testpypi]
username = __token__
password = pypi-your-test-api-token-here
```

或者使用环境变量：
```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-your-api-token
```

---

## GitHub 发布

### 1. 创建 Git 标签

```bash
# 创建版本标签
git tag -a v0.1.0 -m "Release version 0.1.0"

# 推送标签到远程
git push origin v0.1.0

# 或推送所有标签
git push origin --tags
```

### 2. 创建 GitHub Release

在 GitHub 上：
1. 进入你的仓库
2. 点击 "Releases" → "Create a new release"
3. 选择刚创建的标签 (v0.1.0)
4. 填写 Release 信息：

```markdown
## DrissionPage MCP v0.1.0

### 功能特性

DrissionPage MCP Server 为 Claude Code 和其他 MCP 客户端提供专业的浏览器自动化能力。

#### 核心功能
- 🌐 **导航工具** (4个): 页面导航、前进、后退、刷新
- 🎯 **元素交互** (3个): 查找、点击、输入文本
- 📸 **通用操作** (5个): 截图、调整窗口、获取 URL 等
- ⏱️ **等待操作** (2个): 等待元素、延时等待

#### 技术特性
- ✅ 基于 DrissionPage 4.x 最新 API
- ✅ 完整的 MCP 协议支持
- ✅ 类型安全的工具定义
- ✅ 完善的错误处理
- ✅ 详细的文档和示例

### 安装

```bash
pip install drissionpage-mcp
```

### 快速开始

1. 安装包
2. 配置 MCP 客户端（见文档）
3. 开始使用浏览器自动化功能

### 文档

- [完整文档](./README.md)
- [测试和集成指南](./TESTING_AND_INTEGRATION.md)
- [发布指南](./PUBLISHING.md)

### 变更日志

完整变更日志请查看 [CHANGELOG.md](./CHANGELOG.md)

---

**完整代码**: [GitHub Repository](https://github.com/your-username/DrissionMCP)
**PyPI Package**: [drissionpage-mcp](https://pypi.org/project/drissionpage-mcp/)
```

5. 附加构建的分发文件（可选）
6. 点击 "Publish release"

### 3. 设置 GitHub Actions 自动发布（可选）

创建 `.github/workflows/release.yml`：

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine

    - name: Build package
      run: python -m build

    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
      run: python -m twine upload dist/*

    - name: Create GitHub Release
      uses: softprops/action-gh-release@v1
      with:
        files: dist/*
        generate_release_notes: true
```

---

## MCP 服务器注册

### 1. 提交到 MCP 服务器目录

提交你的 MCP 服务器到官方目录（如果存在）：
- 访问 MCP 服务器目录仓库
- 提交 PR 添加你的服务器信息

### 2. 创建服务器清单

创建 `mcp-manifest.json`：

```json
{
  "name": "drissionpage",
  "displayName": "DrissionPage Browser Automation",
  "description": "Professional browser automation tools powered by DrissionPage",
  "version": "0.1.0",
  "author": "Your Name",
  "repository": "https://github.com/your-username/DrissionMCP",
  "license": "Apache-2.0",
  "homepage": "https://github.com/your-username/DrissionMCP",
  "keywords": [
    "browser-automation",
    "web-scraping",
    "drissionpage",
    "mcp",
    "claude"
  ],
  "installation": {
    "pypi": "drissionpage-mcp"
  },
  "configuration": {
    "mcpServers": {
      "drissionpage": {
        "command": "python",
        "args": ["-m", "src.cli"]
      }
    }
  },
  "tools": [
    {
      "name": "page_navigate",
      "description": "Navigate to a URL"
    },
    {
      "name": "element_click",
      "description": "Click an element"
    },
    {
      "name": "page_screenshot",
      "description": "Take a screenshot"
    }
  ]
}
```

---

## 文档和推广

### 1. 完善文档

确保以下文档完整：
- ✅ README.md - 项目主文档
- ✅ TESTING_AND_INTEGRATION.md - 测试和集成指南
- ✅ PUBLISHING.md - 发布指南（本文档）
- ✅ CHANGELOG.md - 变更日志
- ✅ CONTRIBUTING.md - 贡献指南（可选）
- ✅ API_REFERENCE.md - API 参考（可选）

### 2. 创建示例和教程

创建 `examples/` 目录，包含：
- 基础使用示例
- 高级功能示例
- 集成教程
- 最佳实践

### 3. 推广渠道

- **GitHub**: 确保 README 吸引人，添加 badges
- **PyPI**: 完善项目描述和分类
- **社交媒体**: 在相关社区分享
- **博客文章**: 撰写使用教程
- **视频教程**: 录制演示视频
- **MCP 社区**: 在 MCP 相关论坛/Discord 分享

### 4. 添加项目 Badges

在 README.md 顶部添加：

```markdown
[![PyPI version](https://badge.fury.io/py/drissionpage-mcp.svg)](https://badge.fury.io/py/drissionpage-mcp)
[![Python Version](https://img.shields.io/pypi/pyversions/drissionpage-mcp.svg)](https://pypi.org/project/drissionpage-mcp/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Downloads](https://pepy.tech/badge/drissionpage-mcp)](https://pepy.tech/project/drissionpage-mcp)
```

---

## 维护和更新

### 1. 持续集成

设置 CI/CD pipeline：
- 自动运行测试
- 代码质量检查
- 自动构建和发布

### 2. 版本管理

遵循语义化版本：
- **MAJOR**: 不兼容的 API 变更
- **MINOR**: 向后兼容的新功能
- **PATCH**: 向后兼容的问题修复

例如：
- `0.1.0` → `0.1.1` (bug 修复)
- `0.1.1` → `0.2.0` (新功能)
- `0.2.0` → `1.0.0` (重大变更)

### 3. 问题跟踪

- 及时回复 GitHub Issues
- 标记和分类问题
- 维护问题解决路线图

### 4. 社区参与

- 欢迎贡献
- 审查 Pull Requests
- 更新文档
- 发布定期更新

---

## 发布检查清单

发布前确认：

- [ ] 所有测试通过
- [ ] 代码质量检查通过
- [ ] 版本号已更新
- [ ] CHANGELOG 已更新
- [ ] README 文档完整
- [ ] 所有依赖正确声明
- [ ] 许可证文件存在
- [ ] 构建包成功
- [ ] TestPyPI 测试成功
- [ ] Git 标签已创建
- [ ] GitHub Release 已发布
- [ ] PyPI 发布成功
- [ ] 文档已更新
- [ ] 通知相关社区

---

## 常见发布问题

### Q: PyPI 上传失败

**A**:
- 检查版本号是否已存在
- 确认 API Token 正确
- 验证包名称是否可用
- 检查 `pyproject.toml` 配置

### Q: 安装后导入失败

**A**:
- 检查 `pyproject.toml` 中的 `packages.find`
- 确认 `__init__.py` 文件存在
- 验证模块结构正确

### Q: 依赖安装失败

**A**:
- 确保所有依赖在 PyPI 上可用
- 检查版本约束是否合理
- 测试在干净环境中安装

---

## 资源链接

- [PyPI Packaging Guide](https://packaging.python.org/)
- [Semantic Versioning](https://semver.org/)
- [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github)
- [MCP Protocol Spec](https://github.com/anthropics/mcp)
- [DrissionPage Docs](https://drissionpage.org/)

---

恭喜你准备发布 DrissionPage MCP! 🎉

如有问题，请参考上述文档或在社区寻求帮助。
