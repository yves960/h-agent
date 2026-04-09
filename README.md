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
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

如果你要跑完整配置、测试和异步用例，建议安装开发依赖：

```bash
pip install -e .[dev]
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

## 快速开始

完整体验与验收流程见：

- [完整体验流程](docs/guides/full-experience-flow.md)
- `scripts/verify_full_experience.py`

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
h-agent chat

# 或单次执行
h-agent run "帮我解释当前目录结构"

# 模块方式与 h-agent 等价
python -m h_agent chat
```

说明：
- 推荐统一使用 `h-agent <subcommand>` 或 `python -m h_agent <subcommand>`
- `python -m h_agent` 现在与 `h-agent` 使用同一套完整 CLI
- `h-agent chat` 比裸 `h-agent` 更清晰，文档默认使用它

### 运行测试

```bash
.venv/bin/pytest -q
```

如果直接运行系统环境里的 `pytest`，可能因为缺少异步插件而出现误报。

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

### python -m h_agent

模块方式等价于完整 CLI：

```bash
python -m h_agent --help
python -m h_agent chat
python -m h_agent run "hello"
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

## 新特性（v2.0重构）

### 多Agent团队协作

h-agent 支持多Agent团队协作，可以配置不同角色的Agent共同完成任务：

```yaml
# ~/.h-agent/team.yaml
agents:
  - id: "pm"
    name: "产品经理"
    model: "gpt-4o"
    role: "需求分析"

  - id: "dev"
    name: "开发工程师"
    model: "gpt-4o"
    role: "代码实现"

  - id: "qa"
    name: "测试工程师"
    model: "gpt-4o-mini"
    role: "测试验证"
```

使用：
```bash
h-agent team start    # 启动团队模式
h-agent team status   # 查看团队状态
h-agent team assign   # 分配任务
```

### MCP工具集成

支持 Model Context Protocol (MCP)，可以接入外部工具：

```bash
/mcp add playwright   # 添加Playwright MCP
/mcp list             # 列出已添加的MCP
/mcp status           # 查看MCP状态
```

### IDE桥接

通过HTTP服务器桥接IDE：

```bash
/bridge start         # 启动桥接服务
/bridge status        # 查看状态
```

IDE可以通过HTTP API与h-agent交互。

### Buddy伴侣系统

为每个用户生成独特的虚拟伴侣：

```bash
/buddy roll           # 生成新伴侣
/buddy show           # 显示当前伴侣
/buddy name           # 命名伴侣
```

伴侣有稀有度、种类、个性等属性，增添趣味性。

### Vim模式

支持Vim风格的键绑定和编辑模式：

```bash
/vim enable           # 启用Vim模式
/vim disable          # 禁用Vim模式
/vim status           # 查看状态
```

### 语音模式

支持语音输入：

```bash
/voice start          # 开始录音
/voice stop           # 停止并转文本
/voice status         # 查看状态
```

### 任务调度

支持Cron任务和Heartbeat：

```bash
/cron add "*/5 * * * *" "echo 'hello'" "测试任务"
/cron list            # 列出任务
/cron enable <id>     # 启用任务
/cron disable <id>    # 禁用任务

/heartbeat start      # 启动心跳
/heartbeat stop       # 停止心跳
/heartbeat status     # 查看状态
```

### 插件系统

可扩展的插件架构：

```bash
/plugin list          # 列出插件
/plugin enable <name> # 启用插件
/plugin disable <name> # 禁用插件
```

### 弹性容错

自动故障恢复和冷却机制：
- API失败自动重试
- 认证Profile自动切换
- 冷却时间防止频繁切换

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
│   │
│   ├── core/                    # 核心引擎
│   │   ├── agent_loop.py        # Agent循环
│   │   ├── config.py            # 配置管理
│   │   ├── engine.py            # 查询引擎（流式、工具调用）
│   │   └── tools.py             # 工具定义
│   │
│   ├── tools/                   # 工具模块（30+工具）
│   │   ├── base.py              # 工具基类
│   │   ├── registry.py          # 工具注册表
│   │   ├── git.py               # Git操作
│   │   ├── file_ops.py          # 文件操作
│   │   ├── shell.py             # Shell命令
│   │   ├── docker.py            # Docker操作
│   │   └── ...                  # 更多工具
│   │
│   ├── permissions/             # 权限系统
│   │   ├── context.py           # 权限上下文、模式、规则
│   │   ├── checker.py           # 权限检查器
│   │   └── rules.py             # 规则匹配、危险操作检测
│   │
│   ├── features/                # 特性模块
│   │   ├── sessions.py          # 会话持久化
│   │   ├── channels.py          # 多渠道支持
│   │   ├── rag.py               # 代码RAG
│   │   ├── subagents.py         # 子智能体
│   │   ├── skills.py            # 动态技能
│   │   └── tasks.py             # 任务系统
│   │
│   ├── session/                 # 会话管理（独立模块）
│   │   ├── transcript.py        # 会话记录
│   │   ├── storage.py           # 会话存储
│   │   └── resume.py            # 会话恢复
│   │
│   ├── team/                    # 多Agent团队
│   │   ├── agent.py             # Agent定义
│   │   ├── team.py              # 团队管理
│   │   ├── async_team.py        # 异步团队
│   │   └── protocol.py          # 团队协议
│   │
│   ├── coordinator/             # 多Agent协调器
│   │   ├── messaging.py         # 消息总线
│   │   ├── orchestrator.py      # 任务编排
│   │   └── pool.py              # Agent池
│   │
│   ├── mcp/                     # MCP工具集成
│   │   ├── protocol.py          # MCP协议
│   │   ├── client.py            # MCP客户端
│   │   └── transport.py         # 传输层
│   │
│   ├── bridge/                  # IDE桥接系统
│   │   ├── server.py            # HTTP服务器
│   │   ├── protocol.py          # 消息协议
│   │   └── handlers.py          # 请求处理
│   │
│   ├── buddy/                   # Buddy伴侣系统
│   │   ├── types.py             # 类型定义
│   │   ├── companion.py         # 伴侣生成
│   │   ├── sprites.py           # 精灵渲染
│   │   └── display.py           # 显示格式
│   │
│   ├── plugins/                 # 插件系统
│   │   ├── schema.py            # 插件规范
│   │   ├── loader.py            # 插件加载器
│   │   └── registry.py          # 插件注册表
│   │
│   ├── scheduler/               # 任务调度
│   │   ├── cron.py              # Cron任务
│   │   ├── heartbeat.py         # Heartbeat监控
│   │   └── store.py             # 任务存储
│   │
│   ├── concurrency/             # 并发控制
│   │   ├── lanes.py             # Lane队列
│   │   ├── heartbeat.py         # Heartbeat运行器
│   │   └── cron.py              # Cron服务
│   │
│   ├── resilience/              # 弹性/容错
│   │   ├── classify.py          # 故障分类
│   │   ├── profiles.py          # 认证Profile
│   │   └── runner.py            # 弹性运行器
│   │
│   ├── delivery/                # 交付系统
│   │   ├── queue.py             # 交付队列
│   │   └── runner.py            # 交付运行器
│   │
│   ├── vim/                     # Vim模式
│   │   ├── mode.py              # Vim状态机
│   │   ├── keybindings.py       # Vim键绑定
│   │   └── motions.py           # Vim移动
│   │
│   ├── voice/                   # 语音模式
│   │   ├── recorder.py          # 音频录制
│   │   └── stt.py               # 语音转文本
│   │
│   ├── services/                # 服务层
│   │   └── compact.py           # 消息压缩
│   │
│   ├── memory/                  # 记忆系统
│   │   └── ...
│   │
│   ├── personality/             # 人格系统
│   │   └── ...
│   │
│   ├── planner/                 # 规划器
│   │   └── ...
│   │
│   ├── web/                     # Web自动化
│   │   └── ...
│   │
│   ├── cli/                     # CLI入口
│   │   ├── commands.py          # CLI命令
│   │   └── repl.py              # 交互式REPL
│   │
│   ├── commands/                # REPL命令系统（30+命令）
│   │   ├── base.py              # 命令基类
│   │   ├── registry.py          # 命令注册表
│   │   ├── help.py              # /help
│   │   ├── memory.py            # /memory
│   │   ├── usage.py             # /usage
│   │   ├── upgrade.py           # /upgrade
│   │   ├── feedback.py          # /feedback
│   │   ├── bridge.py            # /bridge
│   │   ├── buddy.py             # /buddy
│   │   ├── voice.py             # /voice
│   │   ├── vim.py               # /vim
│   │   ├── mcp.py               # /mcp
│   │   ├── plugin.py            # /plugin
│   │   ├── cron.py              # /cron
│   │   └── ...                  # 更多命令
│   │
│   ├── keybindings/             # 键绑定配置
│   │   └── config.py            # 键绑定注册表
│   │
│   ├── screens/                 # 全屏UI组件
│   │   └── doctor.py            # Doctor诊断界面
│   │
│   ├── migrations/              # 配置迁移系统
│   │   └── core.py              # 迁移核心
│   │
│   ├── daemon/                  # 守护进程
│   │   └── ...
│   │
│   ├── adapters/                # 适配器
│   │   └── ...
│   │
│   ├── codebase/                # 代码库索引
│   │   └── ...
│   │
│   └── skills/                  # 技能模块
│       └── ...
│
├── tests/                       # 测试套件
│   ├── test_permissions.py      # 权限系统测试
│   ├── test_engine.py           # 引擎测试
│   ├── test_keybindings.py      # 键绑定测试
│   ├── test_migrations.py       # 迁移测试
│   ├── test_screens.py          # 屏幕测试
│   ├── test_tools_*.py          # 工具测试
│   ├── test_team.py             # 团队测试
│   ├── test_coordinator.py      # 协调器测试
│   ├── test_scheduler.py        # 调度器测试
│   ├── test_concurrency.py      # 并发测试
│   ├── test_resilience.py       # 弹性测试
│   └── ...                      # 更多测试
│
├── docs/                        # 文档
│   └ guides/                    # 详细指南
│
├── skills/                      # 技能定义
│
├── README.md                    # 中文文档
├── README-en.md                 # 英文文档
├── USER_GUIDE.md                # 中文用户指南
├── USER_GUIDE-en.md             # 英文用户指南
├── QUICKSTART.md                # 中文快速开始
├── QUICKSTART-en.md             # 英文快速开始
├── CHANGELOG.md                 # 中文变更日志
├── CHANGELOG-en.md              # 英文变更日志
├── TEST_REPORT_PHASE1.md        # 阶段1测试报告
├── TEST_REPORT_PHASE7_8.md      # 阶段7-8测试报告
└── pyproject.toml               # 项目配置
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
