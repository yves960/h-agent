# h-agent 用户使用指南

*"时间不在于你拥有多少，而在于你如何使用。"*

> **注意**：本指南从用户视角出发，专注于**如何使用**而非技术原理。如需了解架构设计，请参考 [ARCHITECTURE.md](ARCHITECTURE.md)。

## 目录

- [第一章：5 分钟快速开始](#第一章5-分钟快速开始)
  - [场景描述](#场景描述)
  - [快速上手](#快速上手)
  - [详细步骤](#详细步骤)
  - [示例](#示例)
  - [深入阅读](#深入阅读)
- [第二章：日常使用（单 agent 对话）](#第二章日常使用单-agent-对话)
  - [场景描述](#场景描述-1)
  - [快速上手](#快速上手-1)
  - [详细步骤](#详细步骤-1)
  - [示例](#示例-1)
  - [深入阅读](#深入阅读-1)
- [第三章：多 Agent 协作](#第三章多-agent-协作)
  - [场景描述](#场景描述-2)
  - [快速上手](#快速上手-2)
  - [详细步骤](#详细步骤-2)
  - [示例](#示例-2)
- [第四章：技能系统（Skill）](#第四章技能系统skill)
  - [场景描述](#场景描述-3)
  - [快速上手](#快速上手-3)
  - [详细步骤](#详细步骤-3)
  - [示例](#示例-3)
  - [深入阅读](#深入阅读-3)
- [第五章：MCP 工具](#第五章mcp-工具)
  - [场景描述](#场景描述-4)
  - [快速上手](#快速上手-4)
  - [详细步骤](#详细步骤-3)
  - [示例](#示例-4)
  - [深入阅读](#深入阅读-4)
- [第六章：高级配置](#第六章高级配置)
  - [场景描述](#场景描述-5)
  - [快速上手](#快速上手-5)
  - [详细步骤](#详细步骤-4)
  - [示例](#示例-5)
  - [深入阅读](#深入阅读-5)
- [第七章：Buddy伴侣系统](#第七章buddy伴侣系统)
  - [场景描述](#场景描述-6)
  - [快速上手](#快速上手-6)
  - [详细步骤](#详细步骤-5)
  - [示例](#示例-6)
- [第八章：Vim模式](#第八章vim模式)
  - [场景描述](#场景描述-7)
  - [快速上手](#快速上手-7)
  - [详细步骤](#详细步骤-6)
  - [示例](#示例-7)
- [第九章：语音模式](#第九章语音模式)
  - [场景描述](#场景描述-8)
  - [快速上手](#快速上手-8)
  - [详细步骤](#详细步骤-7)
  - [示例](#示例-8)
- [第十章：IDE桥接](#第十章ide桥接)
  - [场景描述](#场景描述-9)
  - [快速上手](#快速上手-9)
  - [详细步骤](#详细步骤-8)
  - [示例](#示例-9)
- [第十一章：任务调度](#第十一章任务调度)
  - [场景描述](#场景描述-10)
  - [快速上手](#快速上手-10)
  - [详细步骤](#详细步骤-9)
  - [示例](#示例-10)
- [第十二章：插件系统](#第十二章插件系统)
  - [场景描述](#场景描述-11)
  - [快速上手](#快速上手-11)
  - [详细步骤](#详细步骤-10)
  - [示例](#示例-11)
- [附录：命令速查表](#附录命令速查表)

---

## 第一章：5 分钟快速开始

### 场景描述
你想快速体验 h-agent 的基本功能，完成安装、配置并进行第一次对话。

### 快速上手
```bash
# 1. 安装
pip install h-agent

# 2. 初始化配置（按提示输入 API Key）
h-agent init

# 3. 开始对话
h-agent chat
```

### 详细步骤

#### Windows/内网安装
对于 Windows 用户或内网环境：

**Windows PowerShell:**
```powershell
# 克隆项目（如果 pip 安装不可用）
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

**内网环境:**
如果无法访问外网，可以：
1. 在有网络的机器上下载 wheel 包
2. 通过内网传输到目标机器
3. 使用 `pip install h_agent-x.x.x-py3-none-any.whl` 安装

#### 初始化配置
运行 `h-agent init` 后，向导会引导你：
1. 选择 API 提供商（OpenAI/兼容 API）
2. 输入 API Key（支持安全输入模式）
3. 选择默认模型（如 gpt-4o）
4. 配置工作目录

#### 第一次对话
```bash
# 启动交互式聊天
h-agent chat

# 或者直接运行单次命令
h-agent run "写一个 Python 快速排序函数"
```

#### Web UI 启动
h-agent 内置 Web UI：
```bash
# 启动 Web 界面
h-agent web

# 默认在 http://localhost:8080 访问
```

### 示例
```bash
# 完整的快速开始流程
$ pip install h-agent
$ h-agent init
? 选择 API 提供商: OpenAI
? 输入 API Key: ********************************
? 选择默认模型: gpt-4o
? 工作目录: .agent_workspace
配置完成！

$ h-agent chat
> 你好！
你好！我是 h-agent，有什么我可以帮你的吗？
> 写一个冒泡排序
[Agent 自动调用 write 工具创建 bubble_sort.py]
```

### 深入阅读
- [安装详细说明](#安装)
- [配置文件详解](#配置)
- [核心命令参考](#核心命令)

---

## 第二章：日常使用（单 agent 对话）

### 场景描述
你已经完成初始设置，现在想了解如何高效地与单个 agent 进行日常对话、管理会话和利用记忆功能。

### 快速上手
```bash
# 查看所有会话
h-agent session list

# 创建新会话
h-agent session create --name coding

# 在指定会话中对话
h-agent chat --session coding

# 查看会话历史
h-agent session history coding
```

### 详细步骤

#### 与 agent 对话
h-agent 支持多种对话模式：
- **交互模式**: `h-agent chat` - 持续对话
- **单次命令**: `h-agent run "任务描述"` - 执行后退出
- **Web UI**: `h-agent web` - 图形界面

在新的聊天界面中，优先使用这些交互方式：
- `Tab` - 补全 slash 命令
- `Up` / `Down` - 浏览本地输入历史
- `F1` - 打开帮助覆盖层
- `Ctrl+C` 或 `/exit` - 退出聊天

会话清理、历史查看和切换建议使用显式 CLI 命令：

```bash
h-agent session list
h-agent session history my-session
h-agent session create --name project-x
h-agent chat --session project-x
```

#### 会话管理
会话是持久化的对话上下文：
```bash
# 列出所有会话
h-agent session list

# 创建命名会话
h-agent session create --name project-x

# 切换到特定会话
h-agent chat --session project-x

# 删除不再需要的会话
h-agent session delete old-session
```

#### 查看历史
每个会话的历史都保存在本地：
```bash
# 查看完整历史
h-agent session history my-session

# 查看最近 10 条消息
h-agent session history my-session --limit 10

# 导出历史到文件
h-agent session history my-session --export history.json
```

#### 记忆系统
h-agent 具有长期记忆能力：
- **自动记忆**: 重要的决策、代码结构会被自动记住
- **手动记忆**: 在对话中说 "请记住这个配置" 
- **记忆查询**: "之前我们讨论过什么关于数据库的内容？"

记忆存储在 `~/.h-agent/memory/` 目录，按会话隔离。

### 示例
```bash
# 日常使用示例
$ h-agent session create --name web-dev
Session 'web-dev' created with ID: sess_abc123

$ h-agent chat --session web-dev
> 帮我创建一个 React 组件
[Agent 创建了 MyComponent.jsx]

> 记住我喜欢用 TypeScript 而不是 JavaScript
好的！我会记住你喜欢 TypeScript。

> 现在帮我创建另一个组件
[Agent 自动使用 TypeScript 创建 MyComponent.tsx]

$ h-agent session history web-dev --limit 3
1. 用户: 帮我创建一个 React 组件
2. Agent: [创建了 MyComponent.jsx]
3. 用户: 记住我喜欢用 TypeScript 而不是 JavaScript
```

### 深入阅读
- [会话持久化机制](features/sessions.md)
- [记忆系统设计](features/memory.md)
- [CLI 命令完整列表](cli/commands.md)

---

## 第三章：多 Agent 协作

### 场景描述
你需要处理复杂任务，希望多个 agent 协同工作，比如一个负责规划、一个负责编码、一个负责审查。

### 快速上手
```bash
# 初始化团队（注册默认 agent）
h-agent team init

# 查看团队成员
h-agent team list

# 和特定 agent 对话
h-agent team talk planner "分析一下如何实现用户登录功能"
h-agent team talk coder "用 Python 实现一个快速排序"
```

### 详细步骤

#### 什么是多 agent
多 agent 协作允许你：
- **角色分工**: 每个 agent 有特定专长（planner 规划、coder 编码、reviewer 审查、devops 运维）
- **独立对话**: 可以单独和某个 agent 交互
- **团队意识**: 多个 agent 知道彼此的存在，可以协调

#### 如何初始化团队
```bash
# 初始化团队，注册默认 agent
h-agent team init

# 默认会注册以下 agent：
#   planner   — 任务规划师
#   coder     — 主程序员
#   reviewer  — 代码审查员
#   devops    — 运维工程师

# 查看团队状态
h-agent team status
```

#### 如何与 agent 对话
```bash
# 和规划师讨论任务分解
h-agent team talk planner "帮我分解一下开发博客系统需要哪些步骤"

# 和程序员讨论实现
h-agent team talk coder "用 Flask 实现一个简单的 REST API"

# 和审查员讨论代码质量
h-agent team talk reviewer "帮我审查一下这段代码"

# 和运维讨论部署
h-agent team talk devops "如何用 Docker 部署这个应用"
```

#### 如何注册自定义 agent
除了默认 agent，你也可以编程方式注册自己的 agent：

```python
from h_agent.team import AgentTeam, AgentRole

team = AgentTeam()

def my_handler(msg):
    # msg.content 是收到的消息内容
    # 返回 TaskResult
    from h_agent.team.team import TaskResult
    return TaskResult(
        agent_name="my-agent",
        role=AgentRole.CODER,
        success=True,
        content=f"处理了: {msg.content}",
    )

team.register("my-agent", AgentRole.CODER, my_handler,
              description="我的自定义 agent")
```

#### 查看团队状态
```bash
# 查看团队成员
h-agent team list

# 查看团队状态
h-agent team status
```

### 示例
```bash
$ h-agent team init
Initializing team workspace...
Registering default agents:
  ✅ planner [planner] — 任务规划师
  ✅ coder [coder] — 主程序员
  ✅ reviewer [reviewer] — 代码审查员
  ✅ devops [devops] — 运维工程师
✅ Team initialized with default agents!

$ h-agent team list
Team members (4):
  ✅ planner [planner] — 任务规划师，负责分析需求和分解任务
  ✅ coder [coder] — 主程序员，负责代码实现
  ✅ reviewer [reviewer] — 代码审查员，负责代码质量把关
  ✅ devops [devops] — 运维工程师，负责部署和自动化

$ h-agent team talk coder "用 Python 实现快速排序"
[Talking to coder] 用 Python 实现快速排序

[coder]:
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)

# 示例
print(quicksort([3, 6, 8, 10, 1, 2, 1]))  # [1, 1, 2, 3, 6, 8, 10]
```

---

## 第四章：技能系统（Skill）

### 场景描述
你想扩展 h-agent 的能力，使用内置的 Office/Outlook 技能，或者安装第三方技能，甚至创建自己的自定义技能。

### 快速上手
```bash
# 查看可用技能
h-agent skill list

# 安装新技能
h-agent skill install office-skill

# 使用技能（在对话中）
> 使用 Outlook 发送邮件给 john@example.com
```

### 详细步骤

#### 什么是 Skill
Skill 是 h-agent 的能力扩展模块：
- **预构建功能**: 封装特定领域的操作（如 Office、Git、Docker）
- **标准化接口**: 统一的调用方式和参数格式
- **自动发现**: Agent 能自动识别可用技能
- **权限控制**: 敏感操作需要用户确认

#### 使用内置 Skill（Office/Outlook）
内置的 Office 技能支持：
- **Outlook**: 发送邮件、读取收件箱、管理日历
- **Excel**: 读写表格、数据分析、图表生成
- **Word**: 文档创建、格式化、内容提取
- **PowerPoint**: 幻灯片生成、模板应用

使用示例：
```bash
# 在聊天中直接使用
> 用 Outlook 给团队发送会议邀请，主题"项目评审"，时间明天下午2点

> 从 sales.xlsx 中提取 Q1 数据并生成图表
```

#### 如何安装新 Skill
技能安装方式：
```bash
# 从官方仓库安装
h-agent skill install git-skill

# 从 GitHub 安装
h-agent skill install github:user/repo

# 从本地路径安装
h-agent skill install ./my-custom-skill

# 批量安装
h-agent skill install -f skills.txt
```

#### 如何创建自定义 Skill
创建自定义技能的步骤：
1. 创建技能目录结构
2. 编写 `SKILL.md` 描述文件
3. 实现工具函数
4. 配置权限和依赖

技能目录结构：
```
my-skill/
├── SKILL.md          # 技能描述和使用说明
├── tools.py          # 工具实现
├── requirements.txt  # 依赖包
└── config.yaml       # 配置文件模板
```

#### Skill 配置文件详解
`config.yaml` 示例：
```yaml
name: "my-custom-skill"
version: "1.0.0"
description: "我的自定义技能"
tools:
  - name: "custom_tool"
    description: "执行自定义操作"
    parameters:
      - name: "param1"
        type: "string"
        required: true
        description: "第一个参数"
    permissions:
      - "read_files"
      - "network_access"
dependencies:
  - "requests>=2.25.0"
  - "pandas>=1.3.0"
```

### 示例
```bash
# 技能系统使用示例
$ h-agent skill list
内置技能:
- office-skill (已启用)
- git-skill (已启用)  
- docker-skill (未启用)

$ h-agent skill install jira-skill
安装 jira-skill...
配置 Jira 凭据: https://your-company.atlassian.net
用户名: your-email@company.com
API Token: ********************************

$ h-agent chat
> 创建 Jira ticket，标题"修复登录bug"，优先级高
[Jira 技能自动调用，创建 ticket ABC-123]
```

### 深入阅读
- [技能开发指南](features/skills.md)
- [内置技能参考](tools/built-in-skills.md)
- [权限模型说明](security/permissions.md)

---

## 第五章：MCP 工具

### 场景描述
你需要让 h-agent 与 Web 应用交互，比如自动化登录内部系统、提取网页数据，或者配置自定义的 MCP 工具来处理特定业务流程。

### 快速上手
```bash
# 启用 Playwright Web 自动化
h-agent mcp enable playwright

# 配置网站免登录
h-agent mcp auth add --site internal.company.com --token your-token

# 在对话中使用
> 登录 internal.company.com 并提取销售数据
```

### 详细步骤

#### 什么是 MCP
MCP (Multi-Channel Protocol) 是 h-agent 的外部工具协议：
- **标准化接口**: 统一的工具调用协议
- **多渠道支持**: Web、API、桌面应用等
- **安全沙箱**: 工具在受限环境中运行
- **自动认证**: 支持 Token 提取和免登录

#### 使用 Playwright Web 自动化
Playwright 集成提供：
- **浏览器自动化**: 自动点击、输入、导航
- **截图和录屏**: 可视化操作过程
- **网络拦截**: 监控和修改网络请求
- **多浏览器支持**: Chromium、Firefox、WebKit

启用和使用：
```bash
# 启用 Playwright
h-agent mcp enable playwright

# 配置浏览器选项
h-agent mcp config playwright --headless false --slow-mo 100

# 在对话中使用
> 打开 https://example.com 并截图
> 填写登录表单并提交
```

#### Token 提取和免登录
自动处理认证：
```bash
# 添加网站认证信息
h-agent mcp auth add --site example.com --cookie "session=abc123"
h-agent mcp auth add --site api.example.com --header "Authorization: Bearer xyz789"

# 从浏览器提取现有 Token
h-agent mcp auth extract --site example.com

# 查看所有认证配置
h-agent mcp auth list
```

#### 如何配置自定义 MCP
创建自定义 MCP 工具：
1. 创建 MCP 配置文件
2. 定义工具接口
3. 实现业务逻辑
4. 注册到 h-agent

MCP 配置文件 (`mcp-config.yaml`)：
```yaml
name: "custom-business-tool"
version: "1.0"
protocol: "mcp-v1"
tools:
  - name: "get_sales_data"
    description: "获取销售数据"
    input_schema:
      type: "object"
      properties:
        date_range:
          type: "string"
          description: "日期范围，如 '2024-01-01 to 2024-01-31'"
    output_schema:
      type: "object"
      properties:
        total_sales:
          type: "number"
        transactions:
          type: "array"
auth:
  type: "bearer_token"
  token_env: "BUSINESS_API_TOKEN"
```

#### MCP 配置文件详解
关键配置项：
- **name**: 工具名称
- **protocol**: MCP 协议版本
- **tools**: 可用工具列表
- **input_schema**: 输入参数验证
- **output_schema**: 输出格式定义
- **auth**: 认证方式配置
- **rate_limits**: 速率限制设置

### 示例
```bash
# MCP 工具使用示例
$ h-agent mcp enable playwright
Playwright MCP 已启用

$ h-agent mcp auth add --site crm.internal.com --cookie-file ./cookies.json
CRM 认证配置完成

$ h-agent chat
> 登录 crm.internal.com 并导出本月客户列表
[Agent 使用 Playwright 自动登录 CRM]
[提取客户数据并保存为 customers.csv]

> 使用自定义业务工具获取销售统计
[调用 custom-business-tool/get_sales_data]
返回: {"total_sales": 125000, "transactions": 45}
```

### 深入阅读
- [MCP 协议规范](protocols/mcp.md)
- [Playwright 集成文档](tools/playwright.md)
- [认证管理指南](security/authentication.md)

---

## 第六章：高级配置

### 场景描述
你需要优化 h-agent 的性能，切换不同的 AI 模型，使用自定义 Agent 模板，或者在离线环境中部署。

### 快速上手
```bash
# 切换到不同模型
h-agent config --model claude-3-sonnet

# 应用 Agent 模板
h-agent template apply coding-expert

# 离线部署
h-agent deploy offline --models local-models/

# 性能调优
h-agent config --max-tokens 4096 --temperature 0.7
```

### 详细步骤

#### 多模型切换
支持的模型类型：
- **OpenAI**: gpt-4o, gpt-4o-mini, gpt-4-turbo
- **Anthropic**: claude-3-opus, claude-3-sonnet, claude-3-haiku  
- **开源模型**: Llama 3, Mistral, Gemma (通过 Ollama/LM Studio)
- **Azure**: Azure OpenAI 服务

配置多模型：
```bash
# 设置默认模型
h-agent config --model gpt-4o

# 为特定会话设置模型
h-agent session create --name cheap --model gpt-4o-mini

# 模型路由规则
h-agent config --model-routing '
  simple_tasks: gpt-4o-mini
  code_review: gpt-4o  
  creative_writing: claude-3-sonnet
'
```

#### Agent 模板
预定义的 Agent 配置模板：
```bash
# 查看可用模板
h-agent template list

# 应用模板
h-agent template apply coding-expert

# 创建自定义模板
h-agent template create my-template --from current

# 模板包含:
# - 系统提示词
# - 工具权限
# - 模型配置
# - 记忆策略
```

常用模板：
- **coding-expert**: 专注于代码生成和调试
- **research-assistant**: 学术研究和文献分析
- **business-analyst**: 数据分析和商业洞察
- **creative-writer**: 内容创作和文案写作

#### 插件系统
扩展 h-agent 功能：
```bash
# 安装插件
h-agent plugin install advanced-rag

# 启用插件
h-agent plugin enable advanced-rag

# 插件配置
h-agent plugin config advanced-rag --chunk-size 512

# 查看插件状态
h-agent plugin list
```

插件类型：
- **RAG 插件**: 增强检索能力
- **记忆插件**: 高级记忆管理
- **安全插件**: 额外的安全检查
- **UI 插件**: Web 界面扩展

#### 离线部署
完全离线运行配置：
```bash
# 下载模型到本地
h-agent models download --provider ollama --models llama3:8b,phi3

# 配置本地 API 端点
h-agent config --base-url http://localhost:11434/v1 --api-key local

# 离线模式部署
h-agent deploy offline --workspace /opt/h-agent-offline

# 验证离线功能
h-agent run --offline "测试离线模式"
```

离线部署要求：
- 本地运行的模型服务 (Ollama, LM Studio, vLLM)
- 预下载的嵌入模型（用于 RAG）
- 本地工具依赖

#### 性能调优
关键性能参数：
```bash
# 上下文长度优化
h-agent config --max-context 32000 --context-strategy truncate

# 生成参数调优  
h-agent config --temperature 0.3 --top-p 0.9 --max-tokens 2048

# 并发控制
h-agent config --max-concurrent-agents 3 --tool-timeout 30

# 缓存优化
h-agent config --enable-cache true --cache-size 1GB

# 内存管理
h-agent config --memory-limit 4GB --swap-enabled false
```

性能监控：
```bash
# 查看性能统计
h-agent stats

# 实时监控
h-agent monitor

# 生成性能报告
h-agent report performance
```

### 示例
```bash
# 高级配置示例
$ h-agent config --model gpt-4o --temperature 0.2 --max-tokens 4096
配置更新完成

$ h-agent template apply coding-expert
应用 coding-expert 模板:
- 系统提示: "你是一个经验丰富的软件工程师..."
- 工具权限: 全部代码相关工具
- 记忆策略: 代码结构优先

$ h-agent deploy offline --models ./local-models --workspace /opt/h-agent-prod
离线部署完成!
配置文件: /opt/h-agent-prod/config.yaml
模型路径: /opt/h-agent-prod/models/
服务端口: 8080

$ h-agent stats
=== 性能统计 ===
平均响应时间: 2.3s
Token 使用量: 156MB/天  
并发会话数: 3/5
缓存命中率: 78%
```

### 深入阅读
- [配置参考手册](config/reference.md)
- [性能优化指南](performance/optimization.md)
- [离线部署最佳实践](deployment/offline.md)
- [插件开发文档](plugins/development.md)

---

## 第七章：Buddy伴侣系统

### 场景描述
你想要一个有趣的虚拟伴侣，增添日常使用的趣味性。

### 快速上手
```bash
# 生成伴侣
/buddy roll

# 查看伴侣
/buddy show
```

### 详细步骤

#### 伴侣生成
Buddy系统为每个用户生成独特的虚拟伴侣：
- **稀有度**: Common(★), Rare(★★), Epic(★★★), Legendary(★★★★)
- **种类**: 狐狸、猫、狗、龙、兔子等多种生物
- **外观**: 不同的眼睛、帽子、颜色组合
- **属性**: 攻击、防御、速度、智力等

```bash
/buddy roll           # 随机生成伴侣
/buddy roll --seed    # 使用固定种子（可复现）
```

#### 伴侣命名
```bash
/buddy name "小狐狸"   # 命名伴侣
/buddy personality    # 设置性格
```

#### 伴侣显示
```bash
/buddy show           # 显示完整卡片
/buddy mini           # 显示迷你版
/buddy bubble         # 显示气泡形式
```

### 示例
```
$ /buddy roll
✨ 生成新伴侣!

╔════════════════════════════════╗
║  ★★ Epic ★★                   ║
║                                ║
║    🐕 🎩 👀                    ║
║                                ║
║  名字: 未命名                   ║
║  种类: 狗                       ║
║  属性:                          ║
║    ATK: 78  DEF: 45            ║
║    SPD: 62  INT: 89            ║
╚════════════════════════════════╝

$ /buddy name "旺财"
伴侣已命名为: 旺财

$ /buddy show
╔════════════════════════════════╗
║  ★★ Epic ★★                   ║
║                                ║
║    🐕 🎩 👀                    ║
║                                ║
║  名字: 旺财                     ║
║  种类: 狗                       ║
║  性格: 勇敢、忠诚                ║
║  属性:                          ║
║    ATK: 78  DEF: 45            ║
║    SPD: 62  INT: 89            ║
╚════════════════════════════════╝
```

---

## 第八章：Vim模式

### 场景描述
你是Vim用户，想要在h-agent中使用熟悉的Vim键绑定。

### 快速上手
```bash
/vim enable    # 启用Vim模式
/vim status    # 查看状态
```

### 详细步骤

#### Vim模式状态
h-agent支持三种Vim状态：
- **Normal模式**: 默认状态，可执行Vim命令
- **Insert模式**: 输入文本
- **Command模式**: 执行 slash 命令

#### 键绑定
Normal模式常用键：
```
i      - 进入Insert模式
:      - 进入Command模式
h/j/k/l - 方向移动
w/b    - 词间跳转
dd     - 删除行
yy     - 复制行
p      - 粘贴
u      - 撤销
Esc    - 返回Normal模式
```

Insert模式：
```
Esc    - 返回Normal模式
Ctrl+C - 中断
```

Command模式：
```
Enter  - 执行命令
Esc    - 取消命令
```

### 示例
```
$ /vim enable
Vim模式已启用
当前状态: Normal

[Normal模式]
按 i 开始输入...

[Insert模式]
输入你的问题...

[按Esc返回Normal]
按 :help 查看帮助...
```

---

## 第九章：语音模式

### 场景描述
你想要通过语音输入问题，而不是打字。

### 快速上手
```bash
/voice start    # 开始录音
/voice stop     # 停止并转文本
```

### 详细步骤

#### 录音控制
```bash
/voice start          # 开始录音
/voice stop           # 停止录音并转文本
/voice cancel         # 取消录音
/voice status         # 查看录音状态
```

#### 配置
```bash
# 设置语音识别服务
h-agent config --stt-provider openai  # OpenAI Whisper
h-agent config --stt-provider local   # 本地模型

# 设置录音时长限制
h-agent config --voice-max-duration 60  # 最大60秒
```

### 示例
```
$ /voice start
🎤 开始录音...
[录音中: 3s]

$ /voice stop
🎤 录音结束，正在转文本...
转录结果: "帮我写一个Python函数，计算斐波那契数列"

[AI回复]
好的，我来帮你写一个斐波那契函数...
```

---

## 第十章：IDE桥接

### 场景描述
你想要在IDE（VS Code、JetBrains等）中直接使用h-agent。

### 快速上手
```bash
/bridge start    # 启动桥接服务
```

然后在IDE中配置连接。

### 详细步骤

#### 启动桥接
```bash
/bridge start           # 启动HTTP服务器（默认端口8080）
/bridge start --port 9000  # 自定义端口
/bridge status          # 查看状态
/bridge stop            # 停止服务
```

#### API端点
桥接服务提供以下API：
```
POST /chat              # 发送消息
GET /status             # 查看状态
GET /sessions           # 列出会话
POST /session/create    # 创建会话
GET /history/<id>       # 获取历史
```

#### IDE集成
VS Code扩展配置：
```json
{
  "h-agent.bridge.url": "http://localhost:8080",
  "h-agent.bridge.enabled": true
}
```

### 示例
```
$ /bridge start
桥接服务已启动
端口: 8080
状态: 运行中

$ curl http://localhost:8080/chat -d '{"message": "hello"}'
{"response": "你好！有什么可以帮助你的？"}

$ /bridge status
服务状态: 运行中
端口: 8080
活跃连接: 2
消息数: 156
```

---

## 第十一章：任务调度

### 场景描述
你想要定期执行某些任务，或者保持心跳监控。

### 快速上手
```bash
/cron add "*/5 * * * *" "echo 'hello'" "测试"
/heartbeat start
```

### 详细步骤

#### Cron任务
```bash
/cron add <表达式> <命令> <名称>   # 添加任务
/cron list                        # 列出任务
/cron enable <id>                 # 启用任务
/cron disable <id>                # 禁用任务
/cron delete <id>                 # 删除任务
/cron history <id>                # 查看执行历史
```

Cron表达式格式：
```
* * * * *
│ │ │ │ │
│ │ │ │ └── 星期几 (0-6)
│ │ │ └──── 月份 (1-12)
│ │ └────── 日期 (1-31)
│ └──────── 小时 (0-23)
└────────── 分钟 (0-59)
```

示例表达式：
```
*/5 * * * *    - 每5分钟
0 9 * * *      - 每天9:00
0 */2 * * *    - 每2小时
30 14 * * 1-5  - 工作日14:30
```

#### Heartbeat
```bash
/heartbeat start     # 启动心跳监控
/heartbeat stop      # 停止心跳
/heartbeat status    # 查看状态
```

心跳功能：
- 定期检查系统状态
- 执行HEARTBEAT.md中的任务
- 自动更新检查

### 示例
```
$ /cron add "*/10 * * * *" "h-agent run '检查邮件'" "邮件检查"
任务已添加: cron-001
表达式: */10 * * * *
下次执行: 10:10

$ /cron list
ID         表达式          名称        状态    下次执行
cron-001   */10 * * * *   邮件检查    active  10:10
cron-002   0 9 * * *      每日报告    active  09:00

$ /heartbeat start
心跳已启动
间隔: 30分钟
状态: 运行中

$ /heartbeat status
心跳状态: 运行中
PID: 12345
开始时间: 08:00
执行次数: 5
最后执行: 09:30
```

---

## 第十二章：插件系统

### 场景描述
你想要扩展h-agent的功能，安装或开发插件。

### 快速上手
```bash
/plugin list           # 列出插件
/plugin enable <name>  # 启用插件
```

### 详细步骤

#### 插件管理
```bash
/plugin list              # 列出所有插件
/plugin enable <name>     # 启用插件
/plugin disable <name>    # 禁用插件
/plugin info <name>       # 查看插件信息
/plugin install <path>    # 安装本地插件
/plugin uninstall <name>  # 卸载插件
```

#### 插件目录
插件存放在 `~/.h-agent/plugins/` 目录：
```
~/.h-agent/plugins/
├── my-plugin/
│   ├── manifest.yaml    # 插件清单
│   ├── main.py          # 插件入口
│   └── tools.py         # 工具定义
│   └── handlers.py      # 命令处理
```

#### 插件清单格式
```yaml
name: my-plugin
version: 1.0.0
description: 我的自定义插件
author: your-name
tools:
  - my_custom_tool
commands:
  - /mycommand
dependencies:
  - requests
```

### 示例
```
$ /plugin list
名称           版本    状态      描述
web-ui         1.2.0   enabled   Web界面
advanced-rag   2.0.1   enabled   高级RAG
code-review    0.9.0   disabled  代码审查
my-plugin      1.0.0   enabled   自定义插件

$ /plugin enable code-review
插件已启用: code-review
新增工具: review_code, check_style
新增命令: /review

$ /plugin info web-ui
名称: web-ui
版本: 1.2.0
作者: h-agent-team
描述: Web界面插件
工具: web_start, web_stop
命令: /web
依赖: flask, websocket
```

---

## 附录：命令速查表

### 基础命令
| 命令 | 说明 |
|------|------|
| `/help [command]` | 显示帮助 |
| `/exit` | 退出 |
| `/sessions` | 列出会话 |
| `/resume [id]` | 恢复会话 |
| `/status` | 会话状态 |

### Agent命令
| 命令 | 说明 |
|------|------|
| `/model` | 显示当前模型 |
| `/cost` | Token使用和成本 |
| `/usage` | 详细使用统计 |
| `/config [key]` | 显示配置 |
| `/sessions` | 列出保存的会话 |

### 记忆命令
| 命令 | 说明 |
|------|------|
| `/memory list` | 列出所有记忆 |
| `/memory add <text>` | 添加新记忆 |
| `/memory search <query>` | 搜索记忆 |
| `/memory stats` | 记忆统计 |
| `/memory clear` | 清空记忆 |

### 团队命令
| 命令 | 说明 |
|------|------|
| `/team start` | 启动团队模式 |
| `/team status` | 团队状态 |
| `/team assign <agent>` | 分配任务 |

### MCP命令
| 命令 | 说明 |
|------|------|
| `/mcp add <name>` | 添加MCP服务器 |
| `/mcp list` | 列出MCP |
| `/mcp status` | MCP状态 |

### Buddy命令
| 命令 | 说明 |
|------|------|
| `/buddy roll` | 生成伴侣 |
| `/buddy show` | 显示伴侣 |
| `/buddy name <name>` | 命名伴侣 |
| `/buddy personality` | 设置性格 |

### Vim命令
| 命令 | 说明 |
|------|------|
| `/vim enable` | 启用Vim模式 |
| `/vim disable` | 禁用Vim模式 |
| `/vim status` | Vim状态 |

### 语音命令
| 命令 | 说明 |
|------|------|
| `/voice start` | 开始录音 |
| `/voice stop` | 停止并转文本 |
| `/voice cancel` | 取消录音 |
| `/voice status` | 录音状态 |

### 桥接命令
| 命令 | 说明 |
|------|------|
| `/bridge start` | 启动桥接 |
| `/bridge stop` | 停止桥接 |
| `/bridge status` | 桥接状态 |

### 调度命令
| 命令 | 说明 |
|------|------|
| `/cron add` | 添加Cron任务 |
| `/cron list` | 列出任务 |
| `/cron enable/disable` | 启用/禁用 |
| `/heartbeat start` | 启动心跳 |
| `/heartbeat stop` | 停止心跳 |
| `/heartbeat status` | 心跳状态 |

### 插件命令
| 命令 | 说明 |
|------|------|
| `/plugin list` | 列出插件 |
| `/plugin enable/disable` | 启用/禁用 |
| `/plugin info` | 插件信息 |
| `/plugin install` | 安装插件 |

---

*"我宁愿犯错，也不愿什么都不做。"*
