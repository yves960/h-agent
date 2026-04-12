# h-agent Quick Start

*"Time to cause some chaos."* — Ekko

h-agent is a modular AI programming agent framework supporting session management, tool calling, RAG, sub-agents, and multi-channel access.

---

## 30-Second Setup

### 1. Install

```bash
git clone https://github.com/user/h-agent.git
cd h-agent
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

### 2. Configure (First Time)

```bash
h-agent init
```

Follow the prompts to enter your API Key and select a model. Done!

### 3. Start Chatting

```bash
h-agent chat

# Or single-shot mode
h-agent run "Give me an overview of this project"

# Module mode is equivalent
python -m h_agent chat
```

Type your question and press Enter to send. Leave the session with `Ctrl+C` or `/exit`.

If you only need the published package, you can also use:

```bash
pip install h-agent
```

---

## Quick Command Reference

| Command | Description |
|---------|-------------|
| `h-agent init` | First-time setup wizard |
| `h-agent chat` | Interactive chat |
| `h-agent run "..."` | Execute single command |
| `h-agent start` | Start daemon (background) |
| `h-agent stop` | Stop daemon |
| `h-agent status` | Check daemon status |
| `h-agent logs` | View daemon logs |
| `h-agent session list` | List sessions |
| `h-agent config --show` | Show current config |
| `h-agent plugin list` | List installed plugins |
| `h-agent skill list` | List available skills |
| `h-agent rag index` | Index codebase (enable RAG) |
| `h-agent memory list` | View long-term memory |
| `.venv/bin/pytest -q` | Run tests |

---

## Chat UI Tips

### Common Interactions

```
Tab               # Complete slash commands
Up / Down         # Browse local input history
F1                # Toggle the help overlay
Ctrl+C / /exit    # Exit chat
```

Prefer `h-agent chat` over the bare entrypoint so it stays consistent with `run`, `session`, and `config`.

### Use Named Sessions

```bash
# Create a session named "review"
h-agent session create --name review

# Chat in the review session
h-agent chat --session review
```

---

## Configure Multiple Models

### DeepSeek

```bash
h-agent config --base-url https://api.deepseek.com/v1
h-agent config --model deepseek-chat
```

### Local Models (Ollama)

```bash
h-agent config --base-url http://localhost:11434/v1
h-agent config --model llama3
```

### Azure OpenAI

```bash
h-agent config --base-url https://<your-resource>.openai.azure.com/v1
h-agent config --model gpt-4o
```

---

## Automatic Tool Calling

h-agent automatically calls tools based on tasks. For example, if you say:

> *"Read config.json and then modify the debug option in it"*

The agent will:
1. Call `read` to read the file
2. Call `edit` to modify the content
3. Return the completion result

**Available tool categories**:

| Category | Tool Examples |
|----------|---------------|
| Shell | `bash`, `shell_run`, `shell_cd` |
| File | `read`, `write`, `edit`, `glob`, `file_exists` |
| Git | `git_status`, `git_commit`, `git_push`, `git_log` |
| Docker | `docker_ps`, `docker_logs`, `docker_exec` |
| HTTP | `http_get`, `http_post` |
| JSON | `json_parse`, `json_query`, `json_format` |

---

## Daemon Mode

The daemon runs in the background, maintaining session context. Ideal for frequent use.

```bash
# Start (runs in background)
h-agent start

# Check status
h-agent status

# View logs
h-agent logs --tail 50

# Stop
h-agent stop
```

After starting, all commands reuse the same agent instance, saving API calls.

---

## Session Management

```bash
# List all sessions
h-agent session list

# Create session
h-agent session create --name mytask

# Run in specified session
h-agent run --session mytask "Write a quicksort function"

# Search sessions
h-agent session search "login functionality"

# Session tags
h-agent session tag add mytask bug
h-agent session list --tag bug
```

---

## Codebase RAG

First index your codebase, then the agent can understand the entire codebase:

```bash
# Index current directory
h-agent rag index

# Index specified directory
h-agent rag index --directory ./src

# Semantic search
h-agent rag search "user authentication logic"

# View index status
h-agent rag stats
```

---

## Long-Term Memory

h-agent can remember important information:

```bash
# Add memory
h-agent memory add decision "db-choice" "PostgreSQL" --reason "Need transaction support"
h-agent memory add fact "python-version" "3.11"

# Search memory
h-agent memory search "database"

# Export memory
h-agent memory dump
```

---

## Skills

On-demand capability extensions:

```bash
# List available skills
h-agent skill list

# View skill details
h-agent skill info github

# Enable/disable
h-agent skill enable tavily
h-agent skill disable weather

# Install new skill (pip)
h-agent skill install tavily

# Run skill function
h-agent skill run github issues owner/repo --limit 5
```

---

## Plugin System

Extend h-agent capabilities:

```bash
# List plugins
h-agent plugin list

# Install plugin
h-agent plugin install https://github.com/user/h-agent-plugin

# Enable/disable
h-agent plugin enable my-plugin
h-agent plugin disable my-plugin
```

---

## Example Scenarios

### Scenario 1: Write Code for Me

```bash
$ h-agent run "Write a quicksort in Python"

def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)

print(quicksort([3, 6, 8, 10, 1, 2, 1]))
# Output: [1, 1, 2, 3, 6, 8, 10]
```

### Scenario 2: Code Review

```bash
$ h-agent chat
>> Help me review src/auth.py, focus on security
```

### Scenario 3: Git Operations

```
Check the current git status, then commit all changes with message "feat: add user authentication"
```

### Scenario 4: Docker Operations

```
Check running docker containers, then view recent logs for the web container
```

### Scenario 5: Multi-Session Comparison

```bash
# Create two sessions for different analyses
h-agent session create --name analysis-a
h-agent session create --name analysis-b

# Run different tasks in each session
h-agent run --session analysis-a "Analyze frontend code architecture"
h-agent run --session analysis-b "Analyze backend code architecture"
```

---

## More Documentation

| Document | Description |
|----------|-------------|
| [README.md](README.md) | Complete features and configuration reference |
| [docs/guides/core.md](docs/guides/core.md) | Core modules (agent_loop, config, tools) |
| [docs/guides/features.md](docs/guides/features.md) | Feature modules (sessions, channels, rag, skills, subagents) |
| [docs/guides/daemon.md](docs/guides/daemon.md) | Background services (daemon, auto-recovery, logs) |
| [docs/guides/tools.md](docs/guides/tools.md) | 36 built-in tools details |
| [docs/guides/plugins.md](docs/guides/plugins.md) | Plugin system (install, develop, manage) |
| [docs/guides/planner.md](docs/guides/planner.md) | Task planning (decomposition, scheduling, progress tracking) |
| [docs/guides/skills-office.md](docs/guides/skills-office.md) | Windows Office/Outlook automation |
| [docs/guides/cli-reference.md](docs/guides/cli-reference.md) | CLI complete command reference |
| [docs/guides/installation.md](docs/guides/installation.md) | Installation and deployment (Windows/intranet/offline) |

---

*"Don't give up until you get it right."*
