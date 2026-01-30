# 🚀 DrissionPage MCP 快速开始

这是一个 5 分钟快速开始指南，帮助你立即使用 DrissionPage MCP Server。

## 第一步：安装

```bash
# 进入项目目录
cd DrissionMCP

# 安装项目及所有依赖
pip install -e .
```

## 第二步：验证安装

```bash
# 运行快速验证脚本
python playground/quick_start.py
```

**预期输出**：
```
INFO: ✅ Loaded 14 tools
INFO: ✅ All tests passed!
```

如果看到这个输出，说明安装成功！

## 第三步：配置 Claude Code

### 3.1 找到配置文件

Claude Code 的 MCP 配置文件位于：
- **macOS/Linux**: `~/.config/claude-code/mcp_settings.json`
- **Windows**: `%APPDATA%\claude-code\mcp_settings.json`

### 3.2 添加配置

编辑 `mcp_settings.json`（如果不存在就创建），添加以下内容：

```json
{
  "mcpServers": {
    "drissionpage": {
      "command": "python",
      "args": ["-m", "src.cli"],
      "cwd": "/完整路径/替换为你的/DrissionMCP"
    }
  }
}
```

**重要**: 将 `cwd` 替换为你的实际项目路径！

例如：
```json
{
  "mcpServers": {
    "drissionpage": {
      "command": "python",
      "args": ["-m", "src.cli"],
      "cwd": "/Users/kunyunwu/work/code/python/DrissionMCP"
    }
  }
}
```

### 3.3 重启 Claude Code

保存配置后，重启 Claude Code 以加载 MCP 服务器。

## 第四步：开始使用！

在 Claude Code 中尝试这些命令：

### 示例 1: 简单导航和截图
```
使用 DrissionPage 访问 https://example.com 并截图
```

### 示例 2: 搜索引擎自动化
```
打开 Google，搜索 "Python web scraping"，并截图搜索结果
```

### 示例 3: 元素交互
```
访问 https://httpbin.org/forms/post，填写表单并提交
```

### 示例 4: 数据提取
```
访问 https://news.ycombinator.com，获取前 5 条新闻标题
```

## 可用工具概览

你现在可以使用 14 个浏览器自动化工具：

### 🌐 导航 (4个)
- `page_navigate` - 访问网址
- `page_go_back` - 后退
- `page_go_forward` - 前进
- `page_refresh` - 刷新

### 🎯 元素操作 (3个)
- `element_find` - 查找元素
- `element_click` - 点击元素
- `element_type` - 输入文本

### 📸 通用功能 (5个)
- `page_screenshot` - 截图
- `page_resize` - 调整窗口
- `page_click_xy` - 坐标点击
- `page_close` - 关闭浏览器
- `page_get_url` - 获取 URL

### ⏱️ 等待 (2个)
- `wait_for_element` - 等待元素出现
- `wait_time` - 延时等待

## 遇到问题？

### 问题 1: 找不到 Chrome 浏览器

DrissionPage 需要 Chrome/Chromium。如果没有安装：
- **macOS**: `brew install --cask google-chrome`
- **Ubuntu**: `sudo apt-get install chromium-browser`
- **Windows**: 下载并安装 Google Chrome

### 问题 2: 工具加载失败

运行诊断：
```bash
python playground/quick_start.py
```

检查输出中的错误信息。

### 问题 3: Claude Code 找不到工具

1. 确认配置文件路径正确
2. 确认 `cwd` 路径是完整的绝对路径
3. 重启 Claude Code
4. 查看 Claude Code 的日志

### 问题 4: 浏览器打开失败

```bash
# 手动测试 DrissionPage
python -c "from DrissionPage import ChromiumPage; p = ChromiumPage(); print('成功!')"
```

## 下一步

现在你已经成功运行 DrissionPage MCP！

- 📖 查看 [TESTING_AND_INTEGRATION.md](./TESTING_AND_INTEGRATION.md) 了解更多高级用法
- 🚀 查看 [PUBLISHING.md](./PUBLISHING.md) 学习如何发布
- 📝 查看 [REFACTORING_SUMMARY.md](./REFACTORING_SUMMARY.md) 了解项目改造详情
- 💡 查看 [playground/test_scenarios/](./playground/test_scenarios/) 获取更多示例

## 快速测试命令

以下是一些即用的测试命令，可以直接在 Claude Code 中使用：

```
1. "访问 example.com 并告诉我页面标题"
2. "打开 GitHub 主页并截图"
3. "访问 httpbin.org/html 并获取所有链接"
4. "打开 Wikipedia 首页，调整窗口为 1024x768，然后截图"
5. "访问一个网站，等待 2 秒，然后刷新页面"
```

---

**恭喜！你已经成功设置 DrissionPage MCP！** 🎉

现在你可以在 Claude Code 中使用强大的浏览器自动化功能了。

有问题？查看完整文档或在 GitHub 上提出 issue。
