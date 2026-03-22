# Core Modules

*"It's not about how much time you have, it's about how you use it."* — Ekko

This document introduces h-agent's core architecture modules:

| Module | File | Responsibilities |
|------|------|------|
| `client` | `h_agent/core/client.py` | Singleton OpenAI client, unified connection pool |
| `config` | `h_agent/core/config.py` | Configuration management, multi-layer priority |
| `loop` | `h_agent/core/loop.py` | Shared agent loop, supports parallel tool execution |
| `tools` | `h_agent/core/tools.py` | Tool system, lazy loading extensions and plugins |

---

## 1. agent_loop — Core Agent Loop

### Feature Overview

`agent_loop` is h-agent's core engine, responsible for:
- Calling LLM API and processing responses
- Detecting and executing tool calls
- Managing multi-turn conversation message flow
- Handling OpenAI-compatible format tool calls

### How It Works

```
User input → Message history → LLM (with tools) → 
  ├─ No tool_calls → Return final response
  └─ Has tool_calls → Execute tools → Result as tool message → Call LLM again → ...
```

### Basic Usage

```python
from h_agent.core.agent_loop import agent_loop

# Prepare message history
messages = [
    {"role": "system", "content": "You are a coding assistant."},
    {"role": "user", "content": "Please read the current README.md"}
]

# Start agent loop
agent_loop(messages)

# Message history has been modified, includes complete tool call records
print(messages[-1]["content"])
```

### Programmatic Invocation

```python
from h_agent.core.agent_loop import agent_loop, client, MODEL

messages = [{"role": "user", "content": "List all .py files in current directory"}]
agent_loop(messages)
```

### Manual Single-step Invocation

```python
from openai import OpenAI
import os, json

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)

response = client.chat.completions.create(
    model=os.getenv("MODEL_ID", "gpt-4o"),
    messages=[{"role": "user", "content": "Hello"}],
    tools=[],  # No tool calls
)
print(response.choices[0].message.content)
```

### Notes

- `agent_loop` **modifies the passed `messages` list**, appending assistant and tool messages
- Dangerous commands (`rm -rf /`, `mkfs`, etc.) are automatically intercepted
- Default timeout is 120 seconds, can be adjusted via `timeout` parameter (max 300 seconds)
- Output exceeding 50000 characters is truncated
- Supports all OpenAI-compatible APIs (DeepSeek, Azure, Ollama, etc.)

---

## 2. config — Configuration Management System

### Feature Overview

Configuration system supports three-layer priority: configuration profiles, environment variables, YAML files:

```
Environment variables (.env) > ~/.h-agent/secrets.yaml > ~/.h-agent/config.yaml > Defaults
```

### Core Configuration Items

| Variable | Description | Default |
|------|------|--------|
| `OPENAI_API_KEY` | API Key | - |
| `OPENAI_BASE_URL` | API Base URL | `https://api.openai.com/v1` |
| `MODEL_ID` | Model ID | `gpt-4o` |
| `WORKSPACE_DIR` | Working directory | `.agent_workspace` |
| `CONTEXT_SAFE_LIMIT` | Context safety limit | `180000` tokens |
| `H_AGENT_PORT` | Daemon communication port | `19527` |
| `H_AGENT_TOOL_TIMEOUT` | Tool default timeout | `120` seconds |
| `MAX_TOOL_OUTPUT` | Max tool output length | `50000` characters |

### View Configuration

```bash
# Show current full configuration
h-agent config --show

# List all configuration profiles
h-agent config --list-all

# Export configuration as JSON
h-agent config --export
```

### Set Configuration

```bash
# Set API Key (direct input)
h-agent config --api-key sk-xxxx

# Secure API Key input (interactive prompt)
h-agent config --api-key __prompt__

# Set Base URL (for DeepSeek, Ollama, etc.)
h-agent config --base-url https://api.deepseek.com/v1

# Set model
h-agent config --model deepseek-chat

# Clear API Key
h-agent config --clear-key

# Interactive setup wizard
h-agent config --wizard
```

### Programmatic Usage

```python
from h_agent.core.config import (
    MODEL, OPENAI_BASE_URL, OPENAI_API_KEY,
    list_config, get_current_profile, set_current_profile,
    create_profile
)

# Read current configuration
print(f"Model: {MODEL}")
print(f"API URL: {OPENAI_BASE_URL}")

# View all configuration items
all_config = list_config()
print(all_config)

# Switch profile
set_current_profile("deepseek")

# Create new profile
create_profile("azure", copy_from="default")
```

### Multi-profile Management

```bash
# Create new profile
h-agent config --profile-create work

# Switch to specified profile
h-agent config --profile work

# Delete profile
h-agent config --profile-delete old-profile
```

### Notes

- API Key is recommended to be entered interactively via `h-agent config --api-key __prompt__` to avoid leakage
- Profile configuration files are stored in `~/.h-agent/config.<name>.yaml`
- `.env` file has highest priority, suitable for project-level configuration override
- Windows configuration files are in `%APPDATA%\h-agent\`

---

## 3. tools — Tool System

### Feature Overview

h-agent's tool system is based on **Dispatch Map** architecture:

```
Tool definitions (TOOLS) + Tool handlers (TOOL_HANDLERS) = Complete tool
```

Adding a new tool only requires registering a handler, loop logic remains unchanged.

### Lazy Loading

Tool system uses lazy loading strategy:
- Extension tools and plugins are loaded on first use, not at module import
- Avoids unnecessary startup delays

### Built-in Core Tools

| Tool Name | Description | Core Parameters |
|--------|------|---------|
| `bash` | Execute Shell commands | `command`, `timeout` |
| `read` | Read file | `path`, `offset`, `limit` |
| `write` | Write file | `path`, `content` |
| `edit` | Precise file editing | `path`, `old_text`, `new_text` |
| `glob` | Find matching files | `pattern`, `path` |

### Tool Call Execution

```python
from h_agent.core.tools import execute_tool_call, TOOL_HANDLERS

# Single tool call
tool_call = ...  # Get from LLM response
result = execute_tool_call(tool_call)
print(result)
```

### Extension Tool Registration

```python
from h_agent.core.tools import TOOL_HANDLERS, TOOLS

# Register custom tool handler
def my_tool(arg1: str, arg2: int) -> str:
    return f"Processed {arg1}, {arg2}"

TOOL_HANDLERS["my_tool"] = my_tool

# Register tool definition (OpenAI format)
TOOLS.append({
    "type": "function",
    "function": {
        "name": "my_tool",
        "description": "My custom tool",
        "parameters": {
            "type": "object",
            "properties": {
                "arg1": {"type": "string"},
                "arg2": {"type": "integer"}
            },
            "required": ["arg1"]
        }
    }
})
```

### Extension Tool Modules

Extension modules under `h_agent/tools/` are automatically merged:

```python
# Actually equivalent to performing these merges:
from h_agent.tools import ALL_TOOLS, ALL_HANDLERS
# ALL_TOOLS = GIT_TOOLS + FILE_TOOLS + SHELL_TOOLS + DOCKER_TOOLS + HTTP_TOOLS + JSON_TOOLS
# ALL_HANDLERS contains handlers for all tools
```

### Notes

- Tool names must be globally unique, duplicates will be overwritten
- `bash` tool dangerous command blacklist: `rm -rf /`, `sudo rm`, `mkfs`, `dd if=`, `> /dev/sd`
- Large files (>10MB) reading automatically streams and shows progress bar
- Plugin tools are also automatically loaded into the tool list

### Parallel Tool Execution

Read-only tools support parallel execution, improving performance in multi-tool call scenarios:

```python
from h_agent.core.tools import execute_tool_calls_parallel, READ_ONLY_TOOLS

# READ_ONLY_TOOLS contains 12 read-only tools
print(READ_ONLY_TOOLS)
# {'read', 'glob', 'git_status', 'git_log', 'git_branch', 'docker_ps', 
#  'docker_images', 'shell_which', 'shell_env', 'file_exists', 'file_info', 'file_glob'}

# Execute multiple read-only tool calls in parallel
results = execute_tool_calls_parallel(tool_calls)
```

**Execution strategy:**
- Read-only tools (read, glob, git_status, etc.): Use `ThreadPoolExecutor` for parallel execution
- Write operations (bash, write, edit, git_commit, etc.): Execute sequentially to ensure correctness

---

## The Three Relationships

```
client.py          ← Singleton OpenAI client (@lru_cache lazy load)
     ↓
config.py          ← Configuration loading (API Key, model, timeout, etc.)
     ↓
loop.py            ← Shared agent loop (single source for all agent_loop)
     ↓
tools.py           ← Tool execution (bash/read/write/edit/glob + extensions + plugins)
```

`client.py` provides unified OpenAI connection pool, `config` provides runtime parameters, `loop.py` drives conversation flow, and `tools` provides actual operation capability. These four work together to form h-agent's core skeleton.

---

## 4. client — Singleton OpenAI Client

### Feature Overview

`client.py` uses `@lru_cache` to implement lazy-loading singleton pattern. All modules share one OpenAI client instance, avoiding repeated creation of connection pools.

### How It Works

```python
from h_agent.core.client import get_client

# Create client on first call
client = get_client()

# Subsequent calls return the same instance
client2 = get_client()
assert client is client2  # True — same instance
```

### Advantages

| Traditional Method | Singleton Pattern |
|----------|----------|
| Each module creates independent client | All modules share one client |
| Multiple connection pools | Single connection pool, connection reuse |
| Memory waste | Memory usage reduced by ~50% |

### Programmatic Usage

```python
from h_agent.core.client import get_client

client = get_client()
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Lazy Loading Characteristics

- Client is created on first `get_client()` call, not at module import
- `load_dotenv()` is called once at client creation, not repeated for each module
- Cache can be cleared during testing via `get_client.cache_clear()`

---

## 5. loop — Shared Agent Loop

### Feature Overview

`loop.py` extracts the common `run_agent_loop()` function, eliminating code duplication and supporting parallel tool execution.

### How It Works

```
User input → Message history → LLM (with tools) → 
  ├─ No tool_calls → Return final response
  └─ Has tool_calls → 
      ├─ Read-only tools (read, glob, etc.) → Execute in parallel
      └─ Write operations (bash, write, edit) → Execute sequentially
      → Result as tool message → Call LLM again → ...
```

### Parallel Tool Execution

Read-only tools use `ThreadPoolExecutor` for parallel execution:

| Tool Type | Examples | Execution Method |
|----------|------|------|
| Read-only tools | `read`, `glob`, `git_status`, `docker_ps` | Parallel (ThreadPoolExecutor) |
| Write operations | `bash`, `write`, `edit`, `git_commit` | Sequential (for correctness) |

### Basic Usage

```python
from h_agent.core.loop import run_agent_loop
from h_agent.core.client import get_client

messages = [{"role": "user", "content": "Help me view project structure"}]
run_agent_loop(
    messages=messages,
    client=get_client(),
    tools=TOOLS,
    tool_handlers=TOOL_HANDLERS,
)
```

### Deprecation Notice

The `agent_loop()` function in the following files is marked as DEPRECATED, please use `h_agent.core.loop.run_agent_loop()`:
- `h_agent/core/agent_loop.py`
- `h_agent/features/skills.py`
- `h_agent/features/subagents.py`
