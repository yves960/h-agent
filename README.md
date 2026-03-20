# h-agent

OpenAI-powered coding agent harness with modular architecture.

## Features

- **Core Agent Loop** - OpenAI chat completions with tool support
- **Multi-Tool System** - bash, read, write, edit, glob tools
- **Session Management** - JSONL-based conversation persistence
- **Multi-Channel Support** - CLI, extensible to other platforms
- **Codebase RAG** - Semantic code search and retrieval
- **Subagent Spawning** - Task isolation with clean contexts
- **On-Demand Skills** - Load specialized knowledge when needed

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

## Quick Start

```bash
# Interactive mode
python -m h_agent

# Or using the installed command
h-agent
```

## Project Structure

```
h-agent/
├── h_agent/
│   ├── __init__.py
│   ├── __main__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── agent_loop.py    # Core agent loop
│   │   ├── tools.py         # Tool definitions and handlers
│   │   └── config.py        # Configuration
│   ├── features/
│   │   ├── __init__.py
│   │   ├── sessions.py      # Session persistence
│   │   ├── channels.py      # Multi-channel support
│   │   ├── rag.py           # Codebase RAG
│   │   ├── subagents.py     # Subagent spawning
│   │   └── skills.py        # On-demand skill loading
│   └── cli/
│       ├── __init__.py
│       └── commands.py      # CLI commands
├── pyproject.toml
├── README.md
└── tests/
```

## Configuration

Set environment variables in `.env`:

```env
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL_ID=gpt-4o
```

## Modules

### Core

- `h_agent.core.agent_loop` - Core agent loop with tool execution
- `h_agent.core.tools` - Tool definitions (bash, read, write, edit, glob)
- `h_agent.core.config` - Configuration management

### Features

- `h_agent.features.sessions` - Session persistence and context management
- `h_agent.features.channels` - Multi-channel communication (CLI, etc.)
- `h_agent.features.rag` - Codebase indexing and semantic search
- `h_agent.features.subagents` - Isolated subagent execution
- `h_agent.features.skills` - Dynamic skill loading

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run with RAG support
pip install -e ".[rag]"
```

## License

MIT