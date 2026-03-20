# h-agent 快速开始指南

*"该去大闹一场喽。"* — 艾克

---

## 30 秒上手

### 1. 安装

```bash
pip install h-agent
```

### 2. 配置（首次）

```bash
h-agent init
```

按提示输入 API Key，选择模型，搞定！

### 3. 开始对话

```bash
h-agent chat
```

输入你的问题，按回车发送。输入 `q` 退出。

---

## 常用命令速查

| 命令 | 说明 |
|------|------|
| `h-agent init` | 首次配置向导 |
| `h-agent chat` | 交互式对话 |
| `h-agent run "..."` | 执行单次命令 |
| `h-agent start` | 启动守护进程 |
| `h-agent status` | 查看状态 |
| `h-agent session list` | 查看会话列表 |
| `h-agent config --show` | 显示当前配置 |

---

## 场景示例

### 场景 1：帮我写代码

```bash
$ h-agent run "用 Python 写一个快速排序"

def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)

# 测试
print(quicksort([3, 6, 8, 10, 1, 2, 1]))
# 输出: [1, 1, 2, 3, 6, 8, 10]
```

### 场景 2：代码审查

```bash
$ h-agent chat
>> 帮我 review 一下 src/auth.py，重点关注安全性
```

### 场景 3：Git 操作

在对话中直接说：

```
帮我看看当前 git 状态，然后提交所有更改，提交信息写 "feat: 添加用户认证"
```

### 场景 4：Docker 操作

```
帮我查看运行中的 docker 容器，然后查看 web 容器最近的日志
```

---

## 对话模式技巧

### 切换会话

```
>> /clear          # 清空当前对话历史
>> /history        # 查看消息数量
```

### 使用命名会话

```bash
# 创建一个叫 "review" 的会话
h-agent session create --name review

# 在 review 会话中对话
h-agent chat --session review
```

---

## 配置多模型

### DeepSeek

```bash
h-agent config --base-url https://api.deepseek.com/v1
h-agent config --model deepseek-chat
```

### 本地模型 (Ollama)

```bash
h-agent config --base-url http://localhost:11434/v1
h-agent config --model llama3
```

---

## 守护进程模式

守护进程在后台运行，保持会话上下文。

```bash
# 启动
h-agent start

# 查看状态
h-agent status

# 停止
h-agent stop
```

启动后，所有 `h-agent run` 命令都会复用同一个 Agent 实例。

---

## 工具自动调用

h-agent 会根据任务自动调用工具。例如：

你说 *"帮我读取 config.json 然后修改其中的 debug 选项"*，Agent 会：

1. 调用 `file_read` 读取文件
2. 调用 `file_edit` 修改内容
3. 告诉你完成结果

你不需要手动指定工具，Agent 会理解你的意图。

---

## 下一步

- 查看 [README.md](README.md) 了解完整功能
- 查看 [命令文档](README.md#核心命令) 了解所有命令
- 查看 [内置工具](README.md#内置工具) 了解可用工具

---

*"不要放弃，直到做对为止。"*
