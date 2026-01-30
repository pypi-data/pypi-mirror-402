# DrissionPage MCP 测试和集成指南

本指南将帮助你测试、集成和使用 DrissionPage MCP Server。

## 目录
1. [本地测试](#本地测试)
2. [Claude Code 集成](#claude-code-集成)
3. [其他 MCP 客户端集成](#其他-mcp-客户端集成)
4. [常见问题](#常见问题)

---

## 本地测试

### 1. 安装依赖

首先，确保你安装了所有必需的依赖：

```bash
# 克隆或进入项目目录
cd DrissionMCP

# 安装项目（开发模式）
pip install -e .

# 或者安装开发依赖
pip install -e ".[dev]"
```

### 2. 快速验证

运行快速验证脚本，确保工具加载正常：

```bash
python playground/quick_start.py
```

**预期输出**：
```
INFO: 🧪 Testing DrissionPage MCP Server
INFO: ✅ Loaded 14 tools
INFO:    - page_navigate: Navigate to a specific URL in the browser
INFO:    - page_go_back: Go back to the previous page in browser history
INFO:    - page_go_forward: Go forward to the next page in browser history
INFO:    ... and 11 more tools
INFO: ✅ All tests passed!
```

### 3. 本地功能测试

运行本地测试工具，无需 MCP 客户端即可测试所有功能：

```bash
python playground/local_test.py
```

这个脚本提供了两种测试模式：

#### 模式 1: 运行测试场景
自动运行一系列预定义的测试场景：
- 页面导航
- 截图
- 元素点击
- 元素查找
- 等待操作

#### 模式 2: 交互模式
手动测试特定工具：
```
> list              # 显示所有可用工具
> test page_navigate  # 测试特定工具
> scenarios         # 运行所有测试场景
> quit              # 退出
```

### 4. 单元测试

运行单元测试套件：

```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_server.py

# 运行测试并显示覆盖率
pytest tests/ --cov=src --cov-report=html
```

---

## Claude Code 集成

### 前置条件

1. **安装 Claude Code CLI**
   ```bash
   # 如果还没有安装
   npm install -g @anthropic/claude-code
   ```

2. **确保 Chrome/Chromium 已安装**
   DrissionPage 需要 Chrome 或 Chromium 浏览器。

### 集成步骤

#### 步骤 1: 找到 MCP 配置文件

Claude Code 的 MCP 配置文件位于：
- **macOS/Linux**: `~/.config/claude-code/mcp_settings.json`
- **Windows**: `%APPDATA%\claude-code\mcp_settings.json`

如果文件不存在，创建它。

#### 步骤 2: 添加 DrissionPage MCP 配置

编辑 `mcp_settings.json`，添加 DrissionPage MCP 服务器配置：

```json
{
  "mcpServers": {
    "drissionpage": {
      "command": "python",
      "args": ["-m", "src.cli"],
      "cwd": "/完整/路径/到/DrissionMCP",
      "env": {}
    }
  }
}
```

**重要**：将 `cwd` 路径替换为你的实际项目路径！

例如：
```json
{
  "mcpServers": {
    "drissionpage": {
      "command": "python",
      "args": ["-m", "src.cli"],
      "cwd": "/Users/kunyunwu/work/code/python/DrissionMCP",
      "env": {}
    }
  }
}
```

#### 步骤 3: 重启 Claude Code

保存配置后，重启 Claude Code 以加载 MCP 服务器。

#### 步骤 4: 验证集成

在 Claude Code 中，尝试以下命令来验证 DrissionPage MCP 是否正常工作：

```
请使用 DrissionPage 导航到 https://example.com 并截图
```

或者：

```
使用浏览器自动化工具访问 https://www.google.com，然后获取页面标题
```

### 可用工具列表

集成成功后，Claude Code 将可以使用以下 14 个工具：

#### 导航工具 (4个)
- `page_navigate` - 导航到指定 URL
- `page_go_back` - 返回上一页
- `page_go_forward` - 前进到下一页
- `page_refresh` - 刷新页面

#### 通用操作 (5个)
- `page_resize` - 调整浏览器窗口大小
- `page_screenshot` - 截取页面截图
- `page_click_xy` - 在坐标点击
- `page_close` - 关闭浏览器
- `page_get_url` - 获取当前 URL

#### 元素交互 (3个)
- `element_find` - 查找元素
- `element_click` - 点击元素
- `element_type` - 输入文本到元素

#### 等待操作 (2个)
- `wait_for_element` - 等待元素出现
- `wait_time` - 等待指定时间

---

## 其他 MCP 客户端集成

### Claude Desktop

Claude Desktop 的配置方式类似，配置文件位于：
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

配置格式：
```json
{
  "mcpServers": {
    "drissionpage": {
      "command": "python",
      "args": ["-m", "src.cli"],
      "cwd": "/完整/路径/到/DrissionMCP"
    }
  }
}
```

### Cursor IDE

在 Cursor 中，你可以通过设置添加 MCP 服务器：

1. 打开 Cursor 设置
2. 找到 "MCP Servers" 部分
3. 添加新的服务器配置，使用上述相同的配置格式

### 自定义 MCP 客户端

如果你正在开发自己的 MCP 客户端，可以这样启动 DrissionPage MCP：

```python
import subprocess

# 启动 MCP 服务器
process = subprocess.Popen(
    ["python", "-m", "src.cli"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd="/path/to/DrissionMCP"
)

# 通过 stdio 与服务器通信
# 使用 MCP 协议发送和接收消息
```

---

## 常见问题

### Q: 服务器无法启动

**A**: 检查以下几点：
1. 确保安装了所有依赖：`pip install -e .`
2. 确认 Chrome/Chromium 已安装
3. 检查 Python 版本 >= 3.8
4. 查看日志输出以获取详细错误信息

### Q: 工具加载失败

**A**: 运行快速验证：
```bash
python playground/quick_start.py
```
如果失败，检查导入路径和依赖安装。

### Q: 浏览器无法打开

**A**: 这通常是 DrissionPage 配置问题：
1. 确认 Chrome/Chromium 已正确安装
2. 尝试手动启动浏览器测试
3. 检查是否有防火墙或安全软件阻止

### Q: Claude Code 找不到 DrissionPage 工具

**A**:
1. 确认 `mcp_settings.json` 中的 `cwd` 路径正确
2. 重启 Claude Code
3. 检查服务器日志：
   ```bash
   python -m src.cli --log-level DEBUG
   ```

### Q: 元素查找失败

**A**:
1. 确保选择器语法正确（支持 CSS 选择器和 XPath）
2. 增加超时时间
3. 使用 `wait_for_element` 等待元素加载
4. 尝试使用更具体的选择器

### Q: 截图功能不工作

**A**:
1. 确保浏览器窗口没有被最小化
2. 检查文件权限
3. 尝试使用完整页面截图：`page_screenshot(full_page=True)`

---

## 调试技巧

### 启用调试日志

启动服务器时使用 DEBUG 级别日志：
```bash
python -m src.cli --log-level DEBUG
```

### 查看工具执行详情

在本地测试模式下，可以看到每个工具的详细执行过程：
```bash
python playground/local_test.py
# 选择 "2. Interactive mode"
# 然后测试特定工具
```

### 检查 MCP 通信

如果需要调试 MCP 协议通信，可以修改 `src/cli.py` 添加更详细的日志。

---

## 下一步

- 查看 [发布指南](./PUBLISHING.md) 了解如何发布你的 MCP 服务器
- 查看 [开发指南](./CLAUDE.md) 了解如何添加新工具
- 查看 [DrissionPage 文档](https://DrissionPage.org/) 了解更多浏览器自动化功能

---

## 获取帮助

如果遇到问题：
1. 查看项目 README.md
2. 运行 `python playground/local_test.py` 进行本地调试
3. 查看服务器日志输出
4. 检查 DrissionPage 和 MCP SDK 版本兼容性

祝使用愉快！🚀
