# Feature Modules

*"Don't surrender until it's right."* — Ekko

h-agent provides five major feature modules: sessions management, multi-channel (channels), codebase RAG, dynamic skills, and subagents.

---

## 1. sessions — Session Persistence

### Feature Overview

Session system is based on JSONL file persistent storage, supporting:
- Multi-session parallel management
- Automatic context load/save
- Automatic summarization compression on context overflow
- Session tagging and grouping management

### Core Components

```
SessionStore   — JSONL persistence (append write, replay read)
ContextGuard   — Three-phase overflow retry (truncate → summarize → retry)
```

### Command Line Usage

```bash
# List all sessions
h-agent session list

# Create new session
h-agent session create
h-agent session create --name myproject

# Create session with group
h-agent session create --name review --group code

# View session history
h-agent session history <session_id>

# Delete session
h-agent session delete <session_id>

# Search sessions
h-agent session search "login feature"

# Rename session
h-agent session rename <session_id> new-name

# Tag management
h-agent session tag list           # List all tags
h-agent session tag add <id> bug   # Add tag
h-agent session tag remove <id> bug # Remove tag
h-agent session tag get <id>       # View session tags

# Group management
h-agent session group list         # List all groups
h-agent session group set <id> frontend  # Set group
h-agent session group sessions frontend   # View sessions in group
```

### Programmatic Usage

```python
from h_agent.session.manager import SessionManager, get_manager

mgr = get_manager()

# Create session
session_id = mgr.create_session(name="my-task", group="work")
print(f"Created: {session_id}")

# Save user message
mgr.save_turn(session_id, role="user", content="Help me implement user login")

# Save assistant reply
mgr.save_turn(session_id, role="assistant", content="Sure, starting implementation...")

# Get session history
messages = mgr.load_session(session_id)
for msg in messages:
    print(f"[{msg['role']}]: {msg['content'][:50]}")

# List all sessions
sessions = mgr.list_sessions()
for s in sessions:
    print(f"{s['session_id']} - {s.get('name', 'unnamed')}")

# Delete session
mgr.delete_session(session_id)
```

### Session Filtering

```bash
# Filter by tag
h-agent session list --tag bug

# Filter by group
h-agent session list --group frontend
```

### Notes

- Session files are stored in `~/.agent_workspace/sessions/<agent_id>/`
- Automatic summarization compression when context exceeds limit
- Session ID supports name matching (exact match first, then name match)
- JSONL format supports append write, no data loss on power failure

---

## 2. channels — Multi-Channel Support

### Feature Overview

Same Agent brain, multiple communication channels. Channel abstraction unifies message formats across different platforms.

### Supported Channels

| Channel | Description | Trigger Condition |
|------|------|---------|
| CLI | Standard input/output | Directly run `h-agent chat` |
| Telegram | Telegram bot | Set `TELEGRAM_BOT_TOKEN` |
| Extension channels | Pluggable | Implement `Channel` abstract class |

### Message Format Abstraction

```python
from h_agent.features.channels import InboundMessage, OutboundMessage, Channel

@dataclass
class InboundMessage:
    text: str          # Message text
    sender_id: str     # Sender ID
    channel: str        # Channel name
    account_id: str     # Account identifier
    peer_id: str        # Group/channel ID
    is_group: bool      # Whether group message
    metadata: dict      # Additional metadata
```

### Implement Custom Channel

```python
from h_agent.features.channels import Channel, InboundMessage

class MyChannel(Channel):
    def __init__(self, account_id: str = "default"):
        super().__init__(account_id)
    
    def start(self):
        # Start channel listening
        pass
    
    def stop(self):
        # Stop channel
        pass
    
    def send(self, message: OutboundMessage):
        # Send message to target
        pass
```

### Telegram Channel Configuration

```bash
export TELEGRAM_BOT_TOKEN=your-bot-token
export TELEGRAM_ADMIN_IDS=123456,789012  # Admin ID list
h-agent start
```

### Notes

- Channel abstraction unifies platform differences, Agent loop only sees `InboundMessage`
- Extending new channels only requires implementing `Channel` abstract class and registering
- Telegram channel needs publicly accessible Webhook or long polling

---

## 3. rag — Codebase RAG

### Feature Overview

Add codebase understanding and semantic search capabilities to h-agent:
- File structure and symbol indexing
- Semantic vector search (depends on ChromaDB)
- Code snippet retrieval

### Command Line Usage

```bash
# Index codebase
h-agent rag index --directory ./src

# Search codebase
h-agent rag search "user authentication logic"
h-agent rag search "email sending" --limit 10

# View index statistics
h-agent rag stats
h-agent rag stats --directory ./src
```

### Programmatic Usage

```python
from h_agent.features.rag import (
    CodebaseRAG, get_rag_dir, get_rag_index_path
)

# Initialize RAG
rag = CodebaseRAG()

# Index directory
rag.index_directory("./src", file_types=[".py", ".js", ".go"])

# Semantic search
results = rag.search("User login verification", top_k=5)
for r in results:
    print(f"{r['file']}:{r['line']} - {r['preview']}")

# Search by file path
results = rag.search_by_path("./src/auth.py")

# Extract code symbols
symbols = rag.extract_symbols("./src/models.py")
for s in symbols:
    print(f"{s['type']}: {s['name']}")
```

### Notes

- Vector search requires installing ChromaDB: `pip install chromadb`
- Semantic embedding requires OpenAI API Key (for generating embedding)
- Large codebase indexing shows progress
- Index files stored in `~/.h-agent/rag/`

---

## 4. skills — Dynamic Skills

### Feature Overview

Skills are on-demand loaded knowledge modules. Unlike loading everything at startup, skills are injected into context when needed.

### Built-in Skills

| Skill | Description |
|------|------|
| `coding-agent` | Delegate coding tasks to Codex/Claude Code |
| `github` | GitHub operations (issues, PRs, CI) |
| `gog` | Google Workspace (Gmail, Calendar, Drive) |
| `weather` | Weather query |
| `tavily` | AI-optimized web search |
| `find-skills` | Skill discovery and installation |

### Command Line Usage

```bash
# List all skills
h-agent skill list

# Complete list including disabled skills
h-agent skill list --all

# View skill details
h-agent skill info coding-agent

# Enable/disable skill
h-agent skill enable github
h-agent skill disable weather

# Install skill (via pip)
h-agent skill install tavily

# Uninstall skill
h-agent skill uninstall old-skill

# Run skill function
h-agent skill run github issues --repo owner/repo --limit 5
```

### Programmatic Usage

```python
from h_agent.features.skills import (
    list_available_skills, load_skill_content, get_skill_info,
    call_skill_function, load_all_skills
)

# List available skills
skills = list_available_skills()
print(skills)

# Get skill info
info = get_skill_info("github")
print(info)

# Load skill content (inject into Agent context)
content = load_skill_content("github")
print(content)

# Call skill function
load_all_skills()
result = call_skill_function("github", "list_issues", repo="owner/repo", limit=5)
print(result)
```

### Skill File Format

Skills are stored as Markdown files in `skills/` directory:

```markdown
# Skill Name

Skill description.

## Usage

### Function Name

```python
def my_function(arg1: str, arg2: int) -> str:
    # Implementation
    pass
```

## Examples

...
```

### Notes

- Skills exist as `.md` files in `skills/` directory
- Skills are loaded into Agent context on-demand via `load_skill()` tool
- Installed pip package skills are named `h_agent_skill_<name>`

---

## 5. subagents — Subagents

### Feature Overview

Decompose complex tasks into independent subtasks. Each subtask executes in a clean context, only returning result summary.

### Core Features

- Independent message history (clean context)
- Focused task description
- Configurable tool set
- Execution step limit
- Error handling and timeout

### Programmatic Usage

```python
from h_agent.features.subagents import run_subagent, SubagentResult

# Basic usage
result: SubagentResult = run_subagent(
    task="Implement user login API",
    context="Reference existing implementation in src/auth/login.py",
    max_steps=20,
)

if result.success:
    print(f"Complete! Used {result.steps} steps")
    print(result.content)
else:
    print(f"Failed: {result.error}")

# Specify tools
result = run_subagent(
    task="Review code security",
    tools=[bash_tool, read_tool, git_tool],  # Only give these tools
    max_steps=10,
)

# Run with detailed logs
result = run_subagent(
    task="Refactor UserService class",
    context="src/services/user.py needs extraction to independent module",
    max_steps=30,
)
```

### Return Value

```python
@dataclass
class SubagentResult:
    success: bool       # Whether successful
    content: str        # Execution result content
    steps: int          # Steps consumed
    error: Optional[str] = None  # Error message (if any)
```

### Notes

- Subagents have independent context, main Agent's conversation history won't be contaminated
- Suitable for multi-step exploratory tasks (e.g., research, review)
- Not suitable for short tasks, overhead too high
- `max_steps` defaults to 20, too small will cause task unable to complete

---

## Module Relationship Diagram

```
features/
├── sessions.py   ← Persistence + context management (foundation for all features)
├── channels.py   ← Multi-channel access (Telegram, etc.)
├── rag.py        ← Codebase understanding (called by Agent)
├── skills.py     ← On-demand loaded knowledge (called by Agent)
└── subagents.py  ← Task isolation execution (called by Agent)
```

All feature modules work together around `agent_loop`. Sessions provides persistence foundation, while channels/skills/rag/subagents solve different scenario problems respectively.
