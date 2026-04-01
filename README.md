# h-agent

OpenAI-powered coding agent harness with modular architecture.

*"时间不在于你拥有多少，而在于你如何使用。"*

## 📖 用户指南目录

- [第一章：5 分钟快速开始](USER_GUIDE.md#第一章5-分钟快速开始) - 安装、配置、首次对话
- [第二章：日常使用（单 agent 对话）](USER_GUIDE.md#第二章日常使用单-agent-对话) - 会话管理、历史查看、记忆系统  
- [第三章：多 Agent 协作](USER_GUIDE.md#第三章多-agent-协作) - 团队模式、任务分配、状态监控
  - [Agent Team 最佳实践（开发版）](docs/guides/agent-team-best-practices.md) - 从零配置多Agent团队
  - [Agent Team 配置指南（用户版）](docs/guides/agent-team-user-guide.md) - 通过命令行配置团队
  - [Agent Profile 系统](docs/guides/agent-team-user-guide.md#九完整agent配置新版) - IDENTITY/SOUL/USER.md 配置
- [第四章：技能系统（Skill）](USER_GUIDE.md#第四章技能系统skill) - 内置技能、安装新技能、创建自定义技能
- [第五章：MCP 工具](USER_GUIDE.md#第五章mcp-工具) - Web 自动化、Token 免登录、自定义 MCP 配置
- [第六章：高级配置](USER_GUIDE.md#第六章高级配置) - 多模型切换、Agent 模板、离线部署、性能调优

> 💡 **新手推荐**：从[第一章：5 分钟快速开始](USER_GUIDE.md#第一章5-分钟快速开始)开始，然后根据需求跳转到对应章节。

---

## 安装

```bash
pip install h-agent
```

或从源码安装：

```bash
git clone https://github.com/user/h-agent.git
cd h-agent
pip install -e .
```

### Windows 安装

h-agent 支持 Windows (PowerShell/CMD)，但有一些注意事项：

#### 前置依赖

1. **Python 3.10+** - 从 [python.org](https://www.python.org/downloads/) 安装，**务必勾选 "Add Python to PATH"**
2. **Git** - 从 [git-scm.com](https://git-scm.com/download/win) 安装

#### 使用 PowerShell 安装

```powershell
# 克隆项目
git clone https://github.com/user/h-agent.git
cd h-agent

# 创建虚拟环境（推荐）
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 安装
pip install -e .

# 初始化配置
h-agent init
```

#### 使用 CMD 安装

```cmd
git clone https://github.com/user/h-agent.git
cd h-agent
python -m venv .venv
.venv\Scripts\activate.bat
pip install -e .
h-agent init
```

#### Windows 注意事项

- h-agent 在 Windows 上使用 TCP 端口（而非 Unix Socket）进行进程间通信
- 配置文件存储在 `%APPDATA%\h-agent\` 目录
- 推荐使用 **PowerShell** 而非 CMD 以获得更好的兼容性
- 部分 Unix 特定命令（如 `which`, `grep`）在 Windows 上不可用，h-agent 会自动使用替代方案

## 项目介绍

`h-agent` 是一个基于 AI API 的编程智能体框架，提供模块化架构，支持 CLI 交互、工具调用、会话管理、子智能体等特性。

*"时间不在于你拥有多少，而在于你如何使用。"*

---

## 安装

```bash
pip install h-agent
```

或从源码安装：

```bash
git clone https://github.com/user/h-agent.git
cd h-agent
pip install -e .
```

---

## 快速开始

### 方式一：交互式设置向导

```bash
# 首次使用，运行设置向导
h-agent init

# 快速设置（最小化提示）
h-agent init --quick
```

### 方式二：手动配置

在项目根目录创建 `.env`：

```env
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL_ID=gpt-4o
```

### 开始对话

```bash
# 交互模式
h-agent

# 或
h-agent chat
```

---

## 核心命令

### h-agent init

交互式设置向导，引导你完成 API 配置。

```bash
h-agent init          # 完整交互式向导
h-agent init --quick  # 快速设置（最小化提示）
```

向导会提示你：
1. 选择 API 提供商（OpenAI / 兼容 API）
2. 输入 API Key
3. 选择模型
4. 配置工作目录

### h-agent start / stop / status

守护进程管理。

```bash
h-agent start   # 启动守护进程
h-agent stop    # 停止守护进程
h-agent status  # 查看守护进程状态
```

守护进程在后台运行，支持多会话管理和持续上下文。

### h-agent session

会话管理。

```bash
h-agent session list              # 列出所有会话
h-agent session create            # 创建新会话
h-agent session create --name my  # 创建命名会话
h-agent session history <id>       # 查看会话历史
h-agent session delete <id>       # 删除会话
```

### h-agent run

单次命令模式，执行完即退出。

```bash
h-agent run "帮我写一个快速排序"
h-agent run --session my "解释这段代码"
```

### h-agent chat

交互式对话模式。

```bash
h-agent chat           # 使用默认会话
h-agent chat --session my  # 使用指定会话
```

聊天模式支持以下命令：
- `/clear` - 清空历史
- `/history` - 查看消息数量
- `/sessions` - 列出所有保存的会话
- `/resume [id]` - 恢复指定会话（或最新会话）
- `q` / `exit` / 空行 - 退出

> 💡 **会话持久化**：h-agent 自动保存每次对话到 `~/.h-agent/sessions/`，重启后可使用 `/resume` 恢复上下文。

### h-agent config

配置管理。

```bash
h-agent config --show              # 显示当前配置
h-agent config --api-key KEY       # 设置 API Key
h-agent config --api-key __prompt__  # 安全输入 API Key
h-agent config --clear-key         # 清除 API Key
h-agent config --base-url URL       # 设置 API Base URL
h-agent config --model MODEL        # 设置模型
h-agent config --wizard             # 运行交互式设置向导
```

---

## 内置工具

h-agent 提供丰富的内置工具，Agent 可自动调用。

> 💡 **并发安全**：部分工具（`read`）标记为只读并发安全，可与其他只读工具并行执行。写入类工具（`write`, `bash`）会串行执行以避免竞态条件。

### 核心工具

| 工具 | 说明 | 示例 |
|------|------|------|
| `bash` | 执行 Shell 命令 | `bash(command="ls -la")` |
| `read` | 读取文件内容 | `read(path="README.md", offset=1, limit=100)` |
| `write` | 写入文件 | `write(path="test.py", content="# hello")` |
| `edit` | 精确编辑文件 | `edit(path="test.py", old_text="# hello", new_text="# hi")` |
| `glob` | 查找匹配文件 | `glob(pattern="**/*.py")` |

### Git 工具

| 工具 | 说明 |
|------|------|
| `git_status` | 查看工作区状态 |
| `git_commit` | 提交更改 |
| `git_push` | 推送到远程 |
| `git_pull` | 从远程拉取 |
| `git_log` | 查看提交历史 |
| `git_branch` | 分支管理 |

### 文件工具

| 工具 | 说明 |
|------|------|
| `file_read` | 读取文件（支持大文件分片） |
| `file_write` | 写入文件（支持追加模式） |
| `file_edit` | 精确编辑 |
| `file_glob` | 查找文件 |
| `file_exists` | 检查文件是否存在 |
| `file_info` | 获取文件元信息 |

### Shell 工具

| 工具 | 说明 |
|------|------|
| `shell_run` | 执行命令（带安全检查） |
| `shell_env` | 查看环境变量 |
| `shell_cd` | 切换工作目录 |
| `shell_which` | 查找可执行文件路径 |

### Docker 工具

| 工具 | 说明 |
|------|------|
| `docker_ps` | 列出容器 |
| `docker_logs` | 查看容器日志 |
| `docker_exec` | 在容器中执行命令 |
| `docker_images` | 列出镜像 |
| `docker_build` | 构建镜像 |
| `docker_pull` | 拉取镜像 |

---

## REPL 命令参考

在交互式对话模式中，可以使用以下斜杠命令：

### 核心命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `/help [command]` | 显示帮助信息 | `/help memory` |
| `/exit` / `/quit` | 退出 REPL | `/exit` |
| `/clear` | 清空对话历史 | `/clear` |
| `/history` | 显示历史记录 | `/history` |
| `/status` | 显示会话状态 | `/status` |

### 信息命令

| 命令 | 说明 |
|------|------|
| `/tools [list]` | 列出可用工具 |
| `/model` | 显示当前模型 |
| `/cost` | 显示 token 使用和成本 |
| `/usage` | 显示详细使用统计 |
| `/config [key]` | 显示配置信息 |
| `/sessions` | 列出保存的会话 |

### 记忆命令

| 命令 | 说明 |
|------|------|
| `/memory list` | 列出所有记忆 |
| `/memory add <text>` | 添加新记忆 |
| `/memory search <query>` | 搜索记忆 |
| `/memory stats` | 显示记忆统计 |
| `/memory clear` | 清空所有记忆 |

### 开发命令

| 命令 | 说明 |
|------|------|
| `/commit` | 创建 Git 提交 |
| `/diff` | 显示更改差异 |
| `/review` | 代码审查 |
| `/tasks` | 任务管理 |

### 高级命令

| 命令 | 说明 |
|------|------|
| `/doctor` | 运行环境诊断 |
| `/compact` | 压缩上下文 |
| `/resume [id]` | 恢复会话 |
| `/mcp` | MCP 服务器管理 |
| `/skills` | 技能管理 |
| `/theme` | 主题设置 |
| `/vim` | Vim 模式 |
| `/voice` | 语音模式 |
| `/plugin` | 插件管理 |
| `/bridge` | 桥接模式 |

### 系统命令

| 命令 | 说明 |
|------|------|
| `/upgrade` | 检查更新 |
| `/feedback` | 发送反馈 |

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+C` | 中断当前操作 |
| `Ctrl+D` | 退出 REPL |
| `Ctrl+L` | 清屏 |
| `Ctrl+R` | 重试 |
| `Tab` | 自动补全 |
| `↑/↓` | 历史记录导航 |

---

## 权限系统

h-agent 提供了细粒度的权限控制系统，确保工具执行安全可控。

### PermissionMode

```python
from h_agent.permissions import PermissionContext, PermissionMode, PermissionChecker

# 创建权限上下文
ctx = PermissionContext(mode=PermissionMode.AUTO)

# 添加白名单规则
ctx.add_always_allow("bash", "ls", "pwd", "git status")
ctx.add_always_allow("read", "*.py", "*.txt", "*.md")

# 添加黑名单规则
ctx.add_always_deny("bash", "rm -rf*", "dd", "mkfs")
ctx.add_always_deny("bash", "DROP DATABASE*")

# 限制工作目录
ctx.working_dirs = ["/home/user/project", "~/code"]

# 执行权限检查
checker = PermissionChecker(ctx)
result = checker.check("bash", {"command": "ls -la"})
print(result.decision)  # allow/deny/ask
print(result.risk_level)  # low/medium/high/critical
```

### 权限模式

| 模式 | 说明 |
|------|------|
| `DEFAULT` | 每次询问用户确认 |
| `AUTO` | 自动允许安全操作，询问危险操作 |
| `BYPASS` | 允许所有操作（危险！） |
| `DENY` | 拒绝所有工具执行 |

### 危险操作检测

系统自动检测以下危险操作：
- `rm -rf /` - 递归删除
- `DROP DATABASE` - 数据库删除
- `dd` - 直接磁盘写入
- `mkfs` - 文件系统创建
- `sudo su` - 权限提升

### 集成到 QueryEngine

```python
from h_agent.core.engine import QueryEngine
from h_agent.permissions import PermissionContext, PermissionMode

ctx = PermissionContext(mode=PermissionMode.AUTO)

engine = QueryEngine(
    model="gpt-4o",
    tools=tool_schemas,
    permission_context=ctx,
)
```

### 工具权限检查

```python
from h_agent.tools.base import Tool

class MyTool(Tool):
    name = "my_tool"
    description = "My custom tool"
    
    async def execute(self, args):
        # 执行前检查权限
        result = self.check_permissions(args, permission_context)
        if result.is_denied:
            return ToolResult.err("Permission denied")
        # ... 继续执行
```

---

## Thinking 模式支持

h-agent 支持推理模型的思考过程显示，如 DeepSeek Reasoner。

### 支持的模型

- `deepseek-reasoner` - DeepSeek 推理模型
- 其他输出 `reasoning_content` 的模型

### REPL 显示

思考内容在 REPL 中以灰色显示：

```
[User]
解释快速排序算法

[AI Thinking (gray text)...]
这是关于快速排序的解释...

[Final Response]
快速排序是一种分治排序算法...
```

### 事件处理

```python
from h_agent.core.engine import QueryEngine, StreamEventType

def handle_event(event):
    if event.type == StreamEventType.THINKING:
        print(f"\033[90m{event.content}\033[0m", end="")  # 灰色
    elif event.type == StreamEventType.CONTENT:
        print(event.content, end="")

result = await engine.run_tool_loop(
    messages=messages,
    event_callback=handle_event,
)
```

---

## 配置

### 配置优先级

```
.env 文件 > ~/.h-agent/secrets.yaml > ~/.h-agent/config.yaml > 默认值
```

### 配置文件位置

- `~/.h-agent/config.yaml` - 普通配置
- `~/.h-agent/secrets.yaml` - 敏感配置（API Key）
- `.env` - 项目级配置

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OPENAI_API_KEY` | API Key | - |
| `OPENAI_BASE_URL` | API Base URL | `https://api.openai.com/v1` |
| `MODEL_ID` | 模型 ID | `gpt-4o` |
| `WORKSPACE_DIR` | 工作目录 | `.agent_workspace` |
| `CONTEXT_SAFE_LIMIT` | 上下文安全限制 | `180000` |

---

## 项目结构

```
h-agent/
├── h_agent/
│   ├── __init__.py
│   ├── __main__.py
│   ├── core/
│   │   ├── agent_loop.py    # 核心智能体循环
│   │   ├── config.py        # 配置管理
│   │   ├── engine.py        # 查询引擎（流式、工具调用）
│   │   └── tools.py         # 工具定义
│   ├── tools/               # 扩展工具模块
│   │   ├── base.py          # 工具基类
│   │   ├── registry.py      # 工具注册表
│   │   ├── git.py           # Git 操作
│   │   ├── file_ops.py      # 文件操作
│   │   ├── shell.py         # Shell 命令
│   │   └── docker.py        # Docker 操作
│   ├── permissions/         # 权限系统
│   │   ├── context.py       # 权限上下文、模式、规则
│   │   ├── checker.py       # 权限检查器
│   │   └── rules.py         # 规则匹配、危险操作检测
│   ├── features/
│   │   ├── sessions.py      # 会话持久化
│   │   ├── channels.py      # 多渠道支持
│   │   ├── rag.py           # 代码 RAG
│   │   ├── subagents.py     # 子智能体
│   │   └── skills.py        # 动态技能
│   ├── cli/
│   │   ├── commands.py      # CLI 命令
│   │   └── repl.py          # 交互式 REPL
│   ├── commands/           # REPL 命令系统
│   │   ├── base.py          # 命令基类
│   │   ├── registry.py      # 命令注册表
│   │   ├── help.py         # /help 命令
│   │   ├── memory.py       # /memory 命令
│   │   ├── usage.py         # /usage 命令
│   │   ├── upgrade.py      # /upgrade 命令
│   │   ├── feedback.py      # /feedback 命令
│   │   └── ...              # 更多命令
│   ├── keybindings/        # 键绑定配置
│   │   └── config.py       # 键绑定注册表
│   ├── screens/            # 全屏 UI 组件
│   │   └── doctor.py       # Doctor 诊断界面
│   ├── migrations/         # 配置迁移系统
│   │   └── core.py        # 迁移核心
│   └── daemon/             # 守护进程
├── tests/
│   ├── test_permissions.py  # 权限系统测试
│   ├── test_engine.py       # 引擎测试
│   ├── test_keybindings.py  # 键绑定测试
│   ├── test_migrations.py   # 迁移测试
│   ├── test_screens.py      # 屏幕测试
│   └── test_tools_*.py      # 工具测试
├── README.md
├── QUICKSTART.md
└── pyproject.toml
```

---

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/

# 带 RAG 支持安装
pip install -e ".[rag]"
```

---

## 常见问题

### Q: 首次使用需要配置什么？

只需运行 `h-agent init`，按提示输入 API Key 即可。

### Q: 支持哪些 API？

支持所有 OpenAI 兼容 API，包括：
- OpenAI (api.openai.com)
- DeepSeek (api.deepseek.com)
- Azure OpenAI
- 本地模型 (Ollama, LM Studio 等)

### Q: 如何查看当前配置？

```bash
h-agent config --show
```

### Q: 如何切换模型？

```bash
h-agent config --model gpt-4o-mini
```

---

*"我宁愿犯错，也不愿什么都不做。"*

## License

MIT
