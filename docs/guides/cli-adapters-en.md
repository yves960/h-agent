# CLI Adapters Guide

External CLI Agent adapters that allow h-agent to invoke various AI programming tools.

## Overview

Adapters wrap external CLI tools (such as opencode, Claude CLI) into a unified interface.

```
h-agent
├── opencode_adapter  →  opencode CLI
├── claude_adapter   →  Claude CLI  
├── zoo_adapter      →  agent-zoo
└── [you can add more]
```

## Quick Start

```python
from h_agent.adapters import get_adapter, list_adapters

# List all available adapters
print(list_adapters())
# ['opencode', 'claude', 'zoo', 'zoo:xueqiu', 'zoo:liuliu', ...]

# Get adapter
adapter = get_adapter("opencode")

# Send message
response = adapter.chat("Implement a calculator")
print(response.content)
```

## Opencode Adapter

### Basic Usage

```python
from h_agent.adapters import get_adapter

# Get opencode adapter
adapter = get_adapter("opencode")

# Send message
response = adapter.chat("""
Create a simple todo app:
- Add todo
- List todos
- Delete todo
""")

print(response.content)
print(f"Tool calls: {len(response.tool_calls)}")
```

### Configuration Options

```python
from h_agent.adapters.opencode_adapter import OpencodeAdapter

adapter = OpencodeAdapter(
    cwd="/path/to/project",     # Working directory
    timeout=300,                # Timeout in seconds
    agent="code",               # Agent to use
    model="gpt-4o",             # Model
    opencode_path="opencode",   # CLI path
)

# Continue previous session
adapter.attach_session("session-id")

# List all sessions
sessions = adapter.get_session_list()
```

### Streaming Response

```python
for token in adapter.stream_chat("write a hello world"):
    print(token, end="", flush=True)
```

## Claude Adapter

### Basic Usage

```python
from h_agent.adapters import get_adapter

adapter = get_adapter("claude")

response = adapter.chat("""
Review the following code and suggest improvements:
```python
def get_user(id):
    return db.query(id)
```
""")

print(response.content)
```

### Configuration Options

```python
from h_agent.adapters.claude_adapter import ClaudeAdapter

adapter = ClaudeAdapter(
    cwd="/path/to/project",
    timeout=300,
    model="claude-sonnet-4-20250514",  # Claude model
    claude_path="claude",              # CLI path
    extra_args=["--no-stream"],         # Extra arguments
)
```

### Session Management

```python
# Get session ID
print(adapter.session_id)

# Continue session
adapter.attach_session("previous-session-id")

# Stop running request
adapter.stop()
```

## Zoo Adapter

### Basic Usage

```python
from h_agent.adapters import get_adapter

# Use specific animal
adapter = get_adapter("zoo:xueqiu")

response = adapter.chat("Search best practices for React hooks")
print(response.content)
```

### Available Animals

| Adapter Name | Animal | Characteristics |
|-----------|------|------|
| zoo:xueqiu | Snowball Monkey | Research, search |
| zoo:liuliu | Flowing Otter | Architecture, design |
| zoo:xiaohuang | Little Yellow Dog | Testing, debugging |
| zoo:heibai | Black White Bear | Documentation |
| zoo:xiaozhu | Little Pig | DevOps |

### Configuration

```python
from h_agent.adapters.zoo_adapter import ZooAdapter

adapter = ZooAdapter(
    animal="xueqiu",         # Animal name
    cwd="/path/to/project",
    timeout=300,
    model="glm-4",           # Model
    zoo_path="zoo",          # CLI path
)
```

## Team Integration

### Register as Team Member

```python
from h_agent.team.team import AgentTeam, AgentRole

team = AgentTeam("my-project")

# Register as adapter
team.register_adapter(
    name="coder",
    role=AgentRole.CODER,
    adapter_name="opencode",
    adapter_kwargs={"agent": "code"},
)

# Use
result = team.delegate("coder", "task", "Implement login feature")
```

### Zoo Quick Registration

```python
# Zoo members
team.register_zoo_animal("xueqiu")     # Auto select role
team.register_zoo_animal("liuliu", AgentRole.CODER)
```

## Adapter Status

```python
adapter = get_adapter("opencode")

# View status
print(adapter.status)  # AdapterStatus.IDLE

# View uptime
print(f"Uptime: {adapter.uptime:.1f}s")

# Stop
adapter.stop()
```

## Error Handling

```python
from h_agent.adapters import get_adapter
from h_agent.adapters.base import AgentResponse

adapter = get_adapter("opencode")
response = adapter.chat("Execute dangerous operation")

# Check for errors
if response.has_error():
    print(f"Error: {response.error}")
else:
    print(response.content)

# Check if complete (no tool calls)
if response.is_complete():
    print("Complete")
else:
    print(f"Need to execute {len(response.tool_calls)} tools")
```

## Tool Calls

```python
response = adapter.chat("Create file")

# Iterate tool calls
for tool in response.tool_calls:
    print(f"Tool: {tool.name}")
    print(f"Arguments: {tool.arguments}")
    print(f"Result: {tool.result}")
```

## Custom Adapters

### Create New Adapter

```python
from h_agent.adapters.base import (
    BaseAgentAdapter,
    AgentResponse,
    ToolCall,
    AdapterStatus,
)

class MyAdapter(BaseAgentAdapter):
    
    @property
    def name(self) -> str:
        return "my-adapter"
    
    def chat(self, message: str, **kwargs) -> AgentResponse:
        # Implement chat logic
        return AgentResponse(
            content="Response content",
            tool_calls=[],
        )
    
    def stream_chat(self, message: str, **kwargs):
        # Implement streaming response
        yield "partial"
        yield "response"
    
    def stop(self):
        # Stop running process
        pass
```

### Register Adapter

```python
from h_agent.adapters import ADAPTER_REGISTRY

# Manual registration
ADAPTER_REGISTRY["my-adapter"] = MyAdapter

# Or use decorator
@ADAPTER_REGISTRY.register("my-adapter")
class MyAdapter(BaseAgentAdapter):
    ...
```

## CLI Usage

```bash
# Use adapter
h-agent chat --adapter opencode "Implement feature"

# List adapters
h-agent list-adapters

# Test adapter
h-agent test-adapter opencode
```

## Configuration

### Environment Variables

```bash
# Opencode
export OPENCODE_PATH=/usr/local/bin/opencode
export OPENCODE_MODEL=gpt-4o

# Claude
export CLAUDE_PATH=/usr/local/bin/claude
export CLAUDE_MODEL=claude-sonnet-4-20250514

# Zoo
export ZOO_PATH=zoo
export ZOO_TIMEOUT=300
export ZOO_API_KEY=your_key
```

### Adapter Priority

```python
ADAPTER_PRIORITY = [
    "opencode",    # Prefer opencode
    "claude",
    "zoo",
]
```

## Best Practices

### 1. Use Context Manager

```python
from h_agent.adapters import get_adapter

with get_adapter("opencode") as adapter:
    response = adapter.chat("Implement feature")
    # Auto cleanup
```

### 2. Handle Timeout

```python
adapter = get_adapter("opencode")
adapter.timeout = 60  # 1 minute timeout

try:
    response = adapter.chat("Complex task")
except Exception as e:
    print(f"Failed: {e}")
```

### 3. Concurrency Limit

```python
import threading

# Same adapter instance should not be used concurrently
adapter = get_adapter("opencode")

lock = threading.Lock()
with lock:
    response = adapter.chat("task")
```

### 4. Session Management

```python
# For adapters that need context, use sessions
adapter = get_adapter("opencode")
session_id = None

for message in conversation:
    if session_id:
        adapter.attach_session(session_id)
    response = adapter.chat(message)
    session_id = adapter.session_id
```
