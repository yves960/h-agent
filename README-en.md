# h-agent

OpenAI-powered coding agent harness with modular architecture.

*"It's not about how much time you have, but how you use it."*

## Table of Contents

- [Chapter 1: 5-Minute Quick Start](USER_GUIDE.md#chapter-1-5-minute-quick-start) - Installation, configuration, first conversation
- [Chapter 2: Daily Use (Single Agent Conversation)](USER_GUIDE.md#chapter-2-daily-use-single-agent-conversation) - Session management, history viewing, memory system
- [Chapter 3: Multi-Agent Collaboration](USER_GUIDE.md#chapter-3-multi-agent-collaboration) - Team mode, task allocation, status monitoring
  - [Agent Team Best Practices (Developer Edition)](docs/guides/agent-team-best-practices.md) - Configure multi-agent team from scratch
  - [Agent Team Configuration Guide (User Edition)](docs/guides/agent-team-user-guide.md) - Configure team via command line
  - [Agent Profile System](docs/guides/agent-team-user-guide.md#agent-profile-system) - IDENTITY/SOUL/USER.md configuration
- [Chapter 4: Skill System](USER_GUIDE.md#chapter-4-skill-system) - Built-in skills, installing new skills, creating custom skills
- [Chapter 5: MCP Tools](USER_GUIDE.md#chapter-5-mcp-tools) - Web automation, token-free login, custom MCP configuration
- [Chapter 6: Advanced Configuration](USER_GUIDE.md#chapter-6-advanced-configuration) - Multi-model switching, agent templates, offline deployment, performance tuning

> **Tip for Beginners**: Start with [Chapter 1: 5-Minute Quick Start](USER_GUIDE.md#chapter-1-5-minute-quick-start), then jump to the relevant chapter based on your needs.

---

## Installation

```bash
pip install h-agent
```

Or install from source:

```bash
git clone https://github.com/user/h-agent.git
cd h-agent
pip install -e .
```

### Windows Installation

h-agent supports Windows (PowerShell/CMD) with some considerations:

#### Prerequisites

1. **Python 3.10+** - Install from [python.org](https://www.python.org/downloads/), **make sure to check "Add Python to PATH"**
2. **Git** - Install from [git-scm.com](https://git-scm.com/download/win)

#### Installation Using PowerShell

```powershell
# Clone the project
git clone https://github.com/user/h-agent.git
cd h-agent

# Create virtual environment (recommended)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install
pip install -e .

# Initialize configuration
h-agent init
```

#### Installation Using CMD

```cmd
git clone https://github.com/user/h-agent.git
cd h-agent
python -m venv .venv
.venv\Scripts\activate.bat
pip install -e .
h-agent init
```

#### Windows Notes

- h-agent uses TCP ports (instead of Unix Sockets) for inter-process communication on Windows
- Configuration files are stored in `%APPDATA%\h-agent\` directory
- **PowerShell** is recommended over CMD for better compatibility
- Some Unix-specific commands (like `which`, `grep`) are not available on Windows; h-agent will automatically use alternatives

## Project Introduction

`h-agent` is an AI API-based programming agent framework with modular architecture, supporting CLI interaction, tool calling, session management, sub-agents, and more.

*"It's not about how much time you have, but how you use it."*

---

## Installation

```bash
pip install h-agent
```

Or install from source:

```bash
git clone https://github.com/user/h-agent.git
cd h-agent
pip install -e .
```

---

## Quick Start

### Method 1: Interactive Setup Wizard

```bash
# First time use, run the setup wizard
h-agent init

# Quick setup (minimal prompts)
h-agent init --quick
```

### Method 2: Manual Configuration

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL_ID=gpt-4o
```

### Start Conversation

```bash
# Interactive mode
h-agent

# Or
h-agent chat
```

---

## Core Commands

### h-agent init

Interactive setup wizard to guide you through API configuration.

```bash
h-agent init          # Full interactive wizard
h-agent init --quick  # Quick setup (minimal prompts)
```

The wizard will prompt you to:
1. Select API provider (OpenAI / Compatible API)
2. Enter API Key
3. Select model
4. Configure working directory

### h-agent start / stop / status

Daemon management.

```bash
h-agent start   # Start daemon
h-agent stop    # Stop daemon
h-agent status  # Check daemon status
```

The daemon runs in the background with support for multiple session management and persistent context.

### h-agent session

Session management.

```bash
h-agent session list              # List all sessions
h-agent session create            # Create new session
h-agent session create --name my  # Create named session
h-agent session history <id>       # View session history
h-agent session delete <id>       # Delete session
```

### h-agent run

Single command mode, exits after execution.

```bash
h-agent run "Write a quicksort function"
h-agent run --session my "Explain this code"
```

### h-agent chat

Interactive chat mode.

```bash
h-agent chat           # Use default session
h-agent chat --session my  # Use specified session
```

Chat mode supports the following commands:
- `/clear` - Clear history
- `/history` - View message count
- `q` / `exit` / empty line - Exit

### h-agent config

Configuration management.

```bash
h-agent config --show              # Show current configuration
h-agent config --api-key KEY       # Set API Key
h-agent config --api-key __prompt__  # Secure API Key input
h-agent config --clear-key         # Clear API Key
h-agent config --base-url URL       # Set API Base URL
h-agent config --model MODEL        # Set model
h-agent config --wizard             # Run interactive setup wizard
```

---

## Built-in Tools

h-agent provides rich built-in tools that agents can call automatically.

### Core Tools

| Tool | Description | Example |
|------|-------------|---------|
| `bash` | Execute shell commands | `bash(command="ls -la")` |
| `read` | Read file contents | `read(path="README.md", offset=1, limit=100)` |
| `write` | Write to file | `write(path="test.py", content="# hello")` |
| `edit` | Precise file editing | `edit(path="test.py", old_text="# hello", new_text="# hi")` |
| `glob` | Find matching files | `glob(pattern="**/*.py")` |

### Git Tools

| Tool | Description |
|------|-------------|
| `git_status` | View working directory status |
| `git_commit` | Commit changes |
| `git_push` | Push to remote |
| `git_pull` | Pull from remote |
| `git_log` | View commit history |
| `git_branch` | Branch management |

### File Tools

| Tool | Description |
|------|-------------|
| `file_read` | Read files (supports large file chunking) |
| `file_write` | Write files (supports append mode) |
| `file_edit` | Precise editing |
| `file_glob` | Find files |
| `file_exists` | Check if file exists |
| `file_info` | Get file metadata |

### Shell Tools

| Tool | Description |
|------|-------------|
| `shell_run` | Execute commands (with security checks) |
| `shell_env` | View environment variables |
| `shell_cd` | Change working directory |
| `shell_which` | Find executable file path |

### Docker Tools

| Tool | Description |
|------|-------------|
| `docker_ps` | List containers |
| `docker_logs` | View container logs |
| `docker_exec` | Execute commands in container |
| `docker_images` | List images |
| `docker_build` | Build image |
| `docker_pull` | Pull image |

---

## Configuration

### Configuration Priority

```
.env file > ~/.h-agent/secrets.yaml > ~/.h-agent/config.yaml > Default values
```

### Configuration File Locations

- `~/.h-agent/config.yaml` - General configuration
- `~/.h-agent/secrets.yaml` - Sensitive configuration (API Key)
- `.env` - Project-level configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | API Key | - |
| `OPENAI_BASE_URL` | API Base URL | `https://api.openai.com/v1` |
| `MODEL_ID` | Model ID | `gpt-4o` |
| `WORKSPACE_DIR` | Working directory | `.agent_workspace` |
| `CONTEXT_SAFE_LIMIT` | Context safety limit | `180000` |

---

## New Features (v2.0 Refactoring)

### Multi-Agent Team Collaboration

h-agent supports multi-agent team collaboration with different roles:

```yaml
# ~/.h-agent/team.yaml
agents:
  - id: "pm"
    name: "Product Manager"
    model: "gpt-4o"
    role: "Requirement Analysis"

  - id: "dev"
    name: "Developer"
    model: "gpt-4o"
    role: "Code Implementation"

  - id: "qa"
    name: "QA Engineer"
    model: "gpt-4o-mini"
    role: "Test Validation"
```

Usage:
```bash
h-agent team start    # Start team mode
h-agent team status   # View team status
h-agent team assign   # Assign tasks
```

### MCP Tool Integration

Support for Model Context Protocol (MCP):

```bash
/mcp add playwright   # Add Playwright MCP
/mcp list             # List added MCPs
/mcp status           # View MCP status
```

### IDE Bridge

HTTP server bridge for IDE integration:

```bash
/bridge start         # Start bridge service
/bridge status        # View status
```

### Buddy Companion System

Generate unique virtual companions for each user:

```bash
/buddy roll           # Generate new companion
/buddy show           # Show current companion
/buddy name           # Name companion
```

Companions have rarity, species, personality attributes.

### Vim Mode

Vim-style keybindings and editing:

```bash
/vim enable           # Enable Vim mode
/vim disable          # Disable Vim mode
/vim status           # View status
```

### Voice Mode

Voice input support:

```bash
/voice start          # Start recording
/voice stop           # Stop and transcribe
/voice status         # View status
```

### Task Scheduling

Cron tasks and heartbeat:

```bash
/cron add "*/5 * * * *" "echo 'hello'" "Test Task"
/cron list            # List tasks
/cron enable <id>     # Enable task
/cron disable <id>    # Disable task

/heartbeat start      # Start heartbeat
/heartbeat stop       # Stop heartbeat
/heartbeat status     # View status
```

### Plugin System

Extensible plugin architecture:

```bash
/plugin list          # List plugins
/plugin enable <name> # Enable plugin
/plugin disable <name> # Disable plugin
```

### Resilience & Fault Tolerance

Automatic failure recovery:
- Auto retry on API failure
- Auth profile auto-switch
- Cooldown to prevent frequent switching

---

## Project Structure

```
h-agent/
├── h_agent/
│   ├── __init__.py
│   ├── __main__.py
│   │
│   ├── core/                    # Core engine
│   │   ├── agent_loop.py        # Agent loop
│   │   ├── config.py            # Configuration
│   │   ├── engine.py            # Query engine
│   │   └── tools.py             # Tool definitions
│   │
│   ├── tools/                   # Tool modules (30+ tools)
│   │   ├── base.py              # Tool base class
│   │   ├── registry.py          # Tool registry
│   │   ├── git.py               # Git operations
│   │   ├── file_ops.py          # File operations
│   │   ├── shell.py             # Shell commands
│   │   ├── docker.py            # Docker operations
│   │   └── ...                  # More tools
│   │
│   ├── permissions/             # Permission system
│   │   ├── context.py           # Permission context
│   │   ├── checker.py           # Permission checker
│   │   └and rules.py            # Rule matching
│   │
│   ├── features/                # Feature modules
│   │   ├── sessions.py          # Session persistence
│   │   ├── channels.py          # Multi-channel
│   │   ├── rag.py               # Code RAG
│   │   ├── subagents.py         # Sub-agents
│   │   ├── skills.py            # Dynamic skills
│   │   └and tasks.py            # Task system
│   │
│   ├── session/                 # Session management
│   │   ├── transcript.py        # Session transcript
│   │   ├── storage.py           # Session storage
│   │   └and resume.py           # Session resume
│   │
│   ├── team/                    # Multi-agent team
│   │   ├── agent.py             # Agent definition
│   │   ├── team.py              # Team management
│   │   ├── async_team.py        # Async team
│   │   └and protocol.py         # Team protocol
│   │
│   ├── coordinator/             # Multi-agent coordinator
│   │   ├── messaging.py         # Message bus
│   │   ├── orchestrator.py      # Task orchestration
│   │   └and pool.py             # Agent pool
│   │
│   ├── mcp/                     # MCP tool integration
│   │   ├── protocol.py          # MCP protocol
│   │   ├── client.py            # MCP client
│   │   └and transport.py        # Transport layer
│   │
│   ├── bridge/                  # IDE bridge system
│   │   ├── server.py            # HTTP server
│   │   ├── protocol.py          # Message protocol
│   │   └and handlers.py         # Request handlers
│   │
│   ├── buddy/                   # Buddy companion system
│   │   ├── types.py             # Type definitions
│   │   ├── companion.py         # Companion generation
│   │   ├── sprites.py           # Sprite rendering
│   │   └and display.py          # Display formatting
│   │
│   ├── plugins/                 # Plugin system
│   │   ├── schema.py            # Plugin schema
│   │   ├── loader.py            # Plugin loader
│   │   └and registry.py         # Plugin registry
│   │
│   ├── scheduler/               # Task scheduling
│   │   ├── cron.py              # Cron tasks
│   │   ├── heartbeat.py         # Heartbeat monitor
│   │   └and store.py            # Task storage
│   │
│   ├── concurrency/             # Concurrency control
│   │   ├── lanes.py             # Lane queues
│   │   ├── heartbeat.py         # Heartbeat runner
│   │   └and cron.py             # Cron service
│   │
│   ├── resilience/              # Resilience/fault tolerance
│   │   ├── classify.py          # Failure classification
│   │   ├── profiles.py          # Auth profiles
│   │   └and runner.py           # Resilience runner
│   │
│   ├── delivery/                # Delivery system
│   │   ├── queue.py             # Delivery queue
│   │   └and runner.py           # Delivery runner
│   │
│   ├── vim/                     # Vim mode
│   │   ├── mode.py              # Vim state machine
│   │   ├── keybindings.py       # Vim keybindings
│   │   └and motions.py          # Vim motions
│   │
│   ├── voice/                   # Voice mode
│   │   ├── recorder.py          # Audio recorder
│   │   └and stt.py               # Speech-to-text
│   │
│   ├── services/                # Service layer
│   │   └and compact.py           # Message compacting
│   │
│   ├── memory/                  # Memory system
│   │   └and ...
│   │
│   ├── personality/             # Personality system
│   │   └and ...
│   │
│   ├── planner/                 # Planner
│   │   └and ...
│   │
│   ├── web/                     # Web automation
│   │   └and ...
│   │
│   ├── cli/                     # CLI entry point
│   │   ├── commands.py          # CLI commands
│   │   └and repl.py              # Interactive REPL
│   │
│   ├── commands/                # REPL commands (30+)
│   │   ├── base.py              # Command base
│   │   ├── registry.py          # Command registry
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
│   │   └and ...                  # More commands
│   │
│   ├── keybindings/             # Keybinding config
│   │   └and config.py            # Keybinding registry
│   │
│   ├── screens/                 # Full-screen UI
│   │   └and doctor.py           # Doctor diagnostic
│   │
│   ├── migrations/              # Config migration
│   │   └and core.py              # Migration core
│   │
│   ├── daemon/                  # Daemon
│   │   └and ...
│   │
│   ├── adapters/                # Adapters
│   │   └and ...
│   │
│   ├── codebase/                # Codebase indexing
│   │   └and ...
│   │
│   └and skills/                  # Skills module
│       └and ...
│
├── tests/                       # Test suite
│   ├── test_permissions.py
│   ├── test_engine.py
│   ├── test_team.py
│   ├── test_coordinator.py
│   ├── test_scheduler.py
│   ├── test_concurrency.py
│   ├── test_resilience.py
│   └and ...                      # More tests
│
├── docs/                        # Documentation
│   └ guides/                    # Detailed guides
│
├── skills/                      # Skill definitions
│
├── README.md                    # Chinese docs
├── README-en.md                 # English docs
├── USER_GUIDE.md                # Chinese user guide
├── USER_GUIDE-en.md             # English user guide
├── QUICKSTART.md                # Chinese quick start
├── QUICKSTART-en.md             # English quick start
├── CHANGELOG.md                 # Chinese changelog
├── CHANGELOG-en.md              # English changelog
└and pyproject.toml               # Project config
```

---

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Install with RAG support
pip install -e ".[rag]"
```

---

## FAQ

### Q: What do I need to configure for first-time use?

Just run `h-agent init` and enter your API Key when prompted.

### Q: Which APIs are supported?

All OpenAI-compatible APIs are supported, including:
- OpenAI (api.openai.com)
- DeepSeek (api.deepseek.com)
- Azure OpenAI
- Local models (Ollama, LM Studio, etc.)

### Q: How do I view the current configuration?

```bash
h-agent config --show
```

### Q: How do I switch models?

```bash
h-agent config --model gpt-4o-mini
```

---

*"I would rather make mistakes than do nothing."*

## License

MIT
