# DrissionPage MCP Server 项目配置

## 项目信息
DrissionPage MCP Server - 基于 DrissionPage 的 Model Context Protocol 服务器，为 LLM 提供专业的浏览器自动化能力。

**状态**: 🚧 开发中 (v0.1.0)
**许可证**: Apache-2.0
**主要功能**: 提供 14 种 Web 自动化工具，支持导航、页面操作、元素交互、等待操作

## 常用命令

### 开发和测试
- **安装依赖**: `pip install -r requirements.txt` 或 `pip install -e .`
- **安装开发依赖**: `pip install -e ".[dev]"`
- **快速启动服务器**: `python playground/quick_start.py`
- **本地测试**: `python playground/local_test.py`
- **启动 MCP 服务器**: `python -m src.cli` 或 `python src/cli.py`

### 代码质量
- **代码格式化**: `black src/ tests/`
- **导入排序**: `isort src/ tests/`
- **代码检查**: `flake8 src/ tests/`
- **类型检查**: `mypy src/`
- **运行测试**: `python -m pytest tests/`
- **测试覆盖率**: `python -m pytest tests/ --cov=src`

### MCP 配置示例
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

## 权限配置
Claude 可以自动执行以下操作而无需额外确认：
- 读取和编辑项目源码文件 (src/, tests/, playground/)
- 运行开发和测试命令
- 执行代码质量检查工具
- 安装 Python 包和依赖
- Git 操作（除了 push）
- 创建和修改配置文件
- 启动和测试 MCP 服务器

## 项目架构

### 核心组件
- **`src/server.py`**: MCP 服务器主实现，处理工具调用和标准 handlers
- **`src/context.py`**: 浏览器上下文和会话管理，DrissionPage 生命周期
- **`src/response.py`**: 工具响应格式化和内容管理  
- **`src/cli.py`**: 命令行入口点和服务器启动
- **`src/tab.py`**: 页面标签抽象和管理

### 工具系统 (tools/)
- **`base.py`**: 工具定义框架，类型安全和装饰器注册系统
- **`navigate.py`**: 导航工具 (navigate, go_back, go_forward, refresh)
- **`common.py`**: 通用页面操作 (screenshot, resize, close, get_url, click_xy)
- **`element.py`**: 元素交互工具 (find, click, type)
- **`wait.py`**: 等待操作 (wait_for_element, wait_time)

### 测试和示例
- **`playground/`**: 快速测试和示例场景
  - `quick_start.py`: 服务器功能验证
  - `local_test.py`: 无 Claude 本地测试
  - `test_scenarios/`: 详细测试用例
- **`tests/`**: 单元测试和集成测试

## 项目依赖

### 核心依赖
- **DrissionPage >= 4.0.0**: 浏览器自动化引擎
- **mcp >= 1.0.0**: Model Context Protocol SDK
- **pydantic >= 2.0.0**: 数据验证和类型安全
- **typing-extensions >= 4.0.0**: Python 类型扩展

### 开发依赖
- **pytest**: 测试框架
- **black**: 代码格式化
- **isort**: 导入排序
- **flake8**: 代码检查
- **mypy**: 静态类型检查

## 开发环境
- **Python**: 3.8+ (目标版本 3.8)
- **浏览器**: Chrome/Chromium (DrissionPage 需要)
- **MCP 客户端**: Claude Desktop, VS Code, Cursor 等

## 当前待办事项 (Roadmap)

### 高优先级 🔥
1. **MCP SDK 兼容性**: 更新到最新 MCP Python SDK APIs
2. **错误处理**: 改进错误处理和恢复机制
3. **浏览器管理**: 更好的浏览器生命周期管理和清理
4. **配置系统**: 添加浏览器设置、超时等配置选项

### 中等优先级 ⚡
5. **高级元素选择**: 支持更复杂的选择器和查找策略
6. **表单处理**: 专门的表单填写和提交工具
7. **文件上传**: 支持文件上传操作
8. **会话管理**: 更好的会话持久化和状态管理
9. **并行操作**: 支持并发浏览器操作
10. **性能优化**: 优化响应时间

### 已知问题 ⚠️
1. **MCP 服务器集成**: 当前 MCP 服务器实现可能与最新 MCP 协议不完全兼容
2. **DrissionPage 依赖**: 需要正确的 DrissionPage 和 Chrome 安装
3. **异步操作**: 某些操作可能不是完全异步的
4. **资源清理**: 服务器关闭时的浏览器清理需要改进

## 设计模式和原则
- **类型安全**: 使用 Pydantic schemas 进行工具定义
- **装饰器注册**: 清洁的代码组织和工具注册
- **标准化分类**: READ_ONLY vs DESTRUCTIVE 工具类型
- **一致错误处理**: 统一的响应格式
- **模块化设计**: 易于扩展的工具加载系统

## 快速测试指南
```bash
# 1. 验证工具加载
python playground/quick_start.py

# 2. 本地功能测试  
python playground/local_test.py

# 3. 启动 MCP 服务器
python -m src.cli

# 4. 在 Claude Desktop 中测试
"Navigate to https://example.com and take a screenshot"
"Click the submit button"
"Get all text from the page"
```