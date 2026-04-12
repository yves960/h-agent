# h-agent User Guide

*"It's not about how much time you have, but how you use it."*

> **Note**: This guide is written from a user perspective, focusing on **how to use** rather than technical principles. For architecture design, please refer to [ARCHITECTURE.md](ARCHITECTURE.md).

## Table of Contents

- [Chapter 1: 5-Minute Quick Start](#chapter-1-5-minute-quick-start)
  - [Scenario](#scenario)
  - [Quick Start](#quick-start)
  - [Detailed Steps](#detailed-steps)
  - [Examples](#examples)
  - [Further Reading](#further-reading)
- [Chapter 2: Daily Use (Single Agent Conversation)](#chapter-2-daily-use-single-agent-conversation)
  - [Scenario](#scenario-1)
  - [Quick Start](#quick-start-1)
  - [Detailed Steps](#detailed-steps-1)
  - [Examples](#examples-1)
  - [Further Reading](#further-reading-1)
- [Chapter 3: Multi-Agent Collaboration](#chapter-3-multi-agent-collaboration)
  - [Scenario](#scenario-2)
  - [Quick Start](#quick-start-2)
  - [Detailed Steps](#detailed-steps-2)
  - [Examples](#examples-2)
- [Chapter 4: Skill System](#chapter-4-skill-system)
  - [Scenario](#scenario-3)
  - [Quick Start](#quick-start-3)
  - [Detailed Steps](#detailed-steps-3)
  - [Examples](#examples-3)
  - [Further Reading](#further-reading-3)
- [Chapter 5: MCP Tools](#chapter-5-mcp-tools)
  - [Scenario](#scenario-4)
  - [Quick Start](#quick-start-4)
  - [Detailed Steps](#detailed-steps-4)
  - [Examples](#examples-4)
  - [Further Reading](#further-reading-4)
- [Chapter 6: Advanced Configuration](#chapter-6-advanced-configuration)
  - [Scenario](#scenario-5)
  - [Quick Start](#quick-start-5)
  - [Detailed Steps](#detailed-steps-5)
  - [Examples](#examples-5)
  - [Further Reading](#further-reading-5)
- [Chapter 7: Buddy Companion System](#chapter-7-buddy-companion-system)
- [Chapter 8: Vim Mode](#chapter-8-vim-mode)
- [Chapter 9: Voice Mode](#chapter-9-voice-mode)
- [Chapter 10: IDE Bridge](#chapter-10-ide-bridge)
- [Chapter 11: Task Scheduling](#chapter-11-task-scheduling)
- [Chapter 12: Plugin System](#chapter-12-plugin-system)
- [Appendix: Command Reference](#appendix-command-reference)

---

## Chapter 1: 5-Minute Quick Start

### Scenario
You want to quickly experience h-agent's basic features: complete installation, configuration, and have your first conversation.

### Quick Start
```bash
# 1. Install
pip install h-agent

# 2. Initialize configuration (enter API Key when prompted)
h-agent init

# 3. Start conversation
h-agent chat
```

### Detailed Steps

#### Windows/Intranet Installation
For Windows users or intranet environments:

**Windows PowerShell:**
```powershell
# Clone project (if pip install is not available)
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

**Intranet Environment:**
If you cannot access external networks:
1. Download the wheel package on a machine with network access
2. Transfer to the target machine via intranet
3. Install using `pip install h_agent-x.x.x-py3-none-any.whl`

#### Initialize Configuration
After running `h-agent init`, the wizard will guide you through:
1. Select API provider (OpenAI/Compatible API)
2. Enter API Key (supports secure input mode)
3. Select default model (e.g., gpt-4o)
4. Configure working directory

#### First Conversation
```bash
# Start interactive chat
h-agent chat

# Or run a single command directly
h-agent run "Write a Python quicksort function"
```

#### Web UI Startup
h-agent has a built-in Web UI:
```bash
# Start web interface
h-agent web

# Access at http://localhost:8080 by default
```

### Examples
```bash
# Complete quick start flow
$ pip install h-agent
$ h-agent init
? Select API provider: OpenAI
? Enter API Key: ********************************
? Select default model: gpt-4o
? Working directory: .agent_workspace
Configuration complete!

$ h-agent chat
> Hello!
Hello! I'm h-agent. How can I help you?
> Write a bubble sort
[Agent automatically calls write tool to create bubble_sort.py]
```

### Further Reading
- [Detailed Installation Instructions](#installation)
- [Configuration File Details](#configuration)
- [Core Commands Reference](#core-commands)

---

## Chapter 2: Daily Use (Single Agent Conversation)

### Scenario
You have completed the initial setup and want to know how to efficiently have daily conversations with a single agent, manage sessions, and use the memory functionality.

### Quick Start
```bash
# View all sessions
h-agent session list

# Create new session
h-agent session create --name coding

# Chat in specified session
h-agent chat --session coding

# View session history
h-agent session history coding
```

### Detailed Steps

#### Chatting with Agent
h-agent supports multiple chat modes:
- **Interactive Mode**: `h-agent chat` - Continuous conversation
- **Single Command**: `h-agent run "task description"` - Exits after execution
- **Web UI**: `h-agent web` - Graphical interface

In the new chat UI, prefer these interactions:
- `Tab` - complete slash commands
- `Up` / `Down` - browse local input history
- `F1` - open the lightweight help overlay
- `Ctrl+C` or `/exit` - leave chat

Use explicit CLI commands for session cleanup, inspection, and switching:

```bash
h-agent session list
h-agent session history my-session
h-agent session create --name project-x
h-agent chat --session project-x
```

#### Session Management
Sessions are persistent conversation contexts:
```bash
# List all sessions
h-agent session list

# Create named session
h-agent session create --name project-x

# Switch to specific session
h-agent chat --session project-x

# Delete sessions you no longer need
h-agent session delete old-session
```

#### Viewing History
Each session's history is saved locally:
```bash
# View full history
h-agent session history my-session

# View last 10 messages
h-agent session history my-session --limit 10

# Export history to file
h-agent session history my-session --export history.json
```

#### Memory System
h-agent has long-term memory capabilities:
- **Automatic Memory**: Important decisions and code structures are automatically remembered
- **Manual Memory**: Say "please remember this configuration" in conversation
- **Memory Query**: "What did we discuss about databases before?"

Memory is stored in `~/.h-agent/memory/` directory, isolated by session.

### Examples
```bash
# Daily usage example
$ h-agent session create --name web-dev
Session 'web-dev' created with ID: sess_abc123

$ h-agent chat --session web-dev
> Help me create a React component
[Agent created MyComponent.jsx]

> Remember I prefer using TypeScript instead of JavaScript
Got it! I'll remember you prefer TypeScript.

> Now help me create another component
[Agent automatically uses TypeScript to create MyComponent.tsx]

$ h-agent session history web-dev --limit 3
1. User: Help me create a React component
2. Agent: [Created MyComponent.jsx]
3. User: Remember I prefer TypeScript instead of JavaScript
```

### Further Reading
- [Session Persistence Mechanism](features/sessions.md)
- [Memory System Design](features/memory.md)
- [CLI Command Full List](cli/commands.md)

---

## Chapter 3: Multi-Agent Collaboration

### Scenario
You need to handle complex tasks and want multiple agents to work together - for example, one for planning, one for coding, and one for review.

### Quick Start
```bash
# Initialize team (register default agents)
h-agent team init

# View team members
h-agent team list

# Talk to specific agent
h-agent team talk planner "Analyze how to implement user login functionality"
h-agent team talk coder "Implement quicksort in Python"
```

### Detailed Steps

#### What is Multi-Agent
Multi-agent collaboration allows you to:
- **Role Division**: Each agent has specific expertise (planner, coder, reviewer, devops)
- **Independent Conversation**: You can interact with a specific agent individually
- **Team Awareness**: Multiple agents know each other's existence and can coordinate

#### How to Initialize Team
```bash
# Initialize team, register default agents
h-agent team init

# Default agents registered:
#   planner   — Task Planner
#   coder     — Lead Programmer
#   reviewer  — Code Reviewer
#   devops    — DevOps Engineer

# View team status
h-agent team status
```

#### How to Talk to Agents
```bash
# Discuss task decomposition with planner
h-agent team talk planner "Help me break down what steps are needed to develop a blog system"

# Discuss implementation with coder
h-agent team talk coder "Implement a simple REST API with Flask"

# Discuss code quality with reviewer
h-agent team talk reviewer "Help me review this code"

# Discuss deployment with devops
h-agent team talk devops "How to deploy this app with Docker"
```

#### How to Register Custom Agents
In addition to default agents, you can programmatically register your own agents:

```python
from h_agent.team import AgentTeam, AgentRole

team = AgentTeam()

def my_handler(msg):
    # msg.content is the received message content
    # Return TaskResult
    from h_agent.team.team import TaskResult
    return TaskResult(
        agent_name="my-agent",
        role=AgentRole.CODER,
        success=True,
        content=f"Processed: {msg.content}",
    )

team.register("my-agent", AgentRole.CODER, my_handler,
              description="My custom agent")
```

#### Viewing Team Status
```bash
# View team members
h-agent team list

# View team status
h-agent team status
```

### Examples
```bash
$ h-agent team init
Initializing team workspace...
Registering default agents:
  ✅ planner [planner] — Task Planner
  ✅ coder [coder] — Lead Programmer
  ✅ reviewer [reviewer] — Code Reviewer
  ✅ devops [devops] — DevOps Engineer
✅ Team initialized with default agents!

$ h-agent team list
Team members (4):
  ✅ planner [planner] — Task Planner, responsible for analyzing requirements and breaking down tasks
  ✅ coder [coder] — Lead Programmer, responsible for code implementation
  ✅ reviewer [reviewer] — Code Reviewer, responsible for code quality control
  ✅ devops [devops] — DevOps Engineer, responsible for deployment and automation

$ h-agent team talk coder "Implement quicksort in Python"
[Talking to coder] Implement quicksort in Python

[coder]:
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)

# Example
print(quicksort([3, 6, 8, 10, 1, 2, 1]))  # [1, 1, 2, 3, 6, 8, 10]
```

---

## Chapter 4: Skill System

### Scenario
You want to extend h-agent's capabilities, use built-in Office/Outlook skills, install third-party skills, or even create your own custom skills.

### Quick Start
```bash
# View available skills
h-agent skill list

# Install new skill
h-agent skill install office-skill

# Use skill (in conversation)
> Use Outlook to send an email to john@example.com
```

### Detailed Steps

#### What is Skill
Skill is h-agent's capability extension module:
- **Pre-built Functions**: Encapsulated domain-specific operations (Office, Git, Docker)
- **Standardized Interface**: Unified calling method and parameter format
- **Auto-discovery**: Agent can automatically recognize available skills
- **Permission Control**: Sensitive operations require user confirmation

#### Using Built-in Skills (Office/Outlook)
Built-in Office skills support:
- **Outlook**: Send emails, read inbox, manage calendar
- **Excel**: Read/write spreadsheets, data analysis, chart generation
- **Word**: Document creation, formatting, content extraction
- **PowerPoint**: Slide generation, template application

Usage examples:
```bash
# Use directly in chat
> Send a meeting invitation to the team using Outlook, subject "Project Review", tomorrow at 2pm

> Extract Q1 data from sales.xlsx and generate a chart
```

#### How to Install New Skills
Skill installation methods:
```bash
# Install from official repository
h-agent skill install git-skill

# Install from GitHub
h-agent skill install github:user/repo

# Install from local path
h-agent skill install ./my-custom-skill

# Batch install
h-agent skill install -f skills.txt
```

#### How to Create Custom Skills
Steps to create custom skills:
1. Create skill directory structure
2. Write `SKILL.md` description file
3. Implement tool functions
4. Configure permissions and dependencies

Skill directory structure:
```
my-skill/
├── SKILL.md          # Skill description and usage instructions
├── tools.py          # Tool implementation
├── requirements.txt  # Dependencies
└── config.yaml       # Configuration file template
```

#### Skill Configuration File Details
`config.yaml` example:
```yaml
name: "my-custom-skill"
version: "1.0.0"
description: "My custom skill"
tools:
  - name: "custom_tool"
    description: "Execute custom operations"
    parameters:
      - name: "param1"
        type: "string"
        required: true
        description: "First parameter"
    permissions:
      - "read_files"
      - "network_access"
dependencies:
  - "requests>=2.25.0"
  - "pandas>=1.3.0"
```

### Examples
```bash
# Skill system usage example
$ h-agent skill list
Built-in skills:
- office-skill (enabled)
- git-skill (enabled)  
- docker-skill (disabled)

$ h-agent skill install jira-skill
Installing jira-skill...
Configure Jira credentials: https://your-company.atlassian.net
Username: your-email@company.com
API Token: ********************************

$ h-agent chat
> Create Jira ticket, title "Fix login bug", high priority
[Jira skill automatically called, created ticket ABC-123]
```

### Further Reading
- [Skill Development Guide](features/skills.md)
- [Built-in Skills Reference](tools/built-in-skills.md)
- [Permission Model Description](security/permissions.md)

---

## Chapter 5: MCP Tools

### Scenario
You need h-agent to interact with web applications, such as automating login to internal systems, extracting web data, or configuring custom MCP tools to handle specific business workflows.

### Quick Start
```bash
# Enable Playwright web automation
h-agent mcp enable playwright

# Configure website token-free login
h-agent mcp auth add --site internal.company.com --token your-token

# Use in conversation
> Login to internal.company.com and extract sales data
```

### Detailed Steps

#### What is MCP
MCP (Multi-Channel Protocol) is h-agent's external tool protocol:
- **Standardized Interface**: Unified tool calling protocol
- **Multi-channel Support**: Web, API, desktop applications, etc.
- **Secure Sandbox**: Tools run in restricted environments
- **Auto Authentication**: Supports token extraction and token-free login

#### Using Playwright Web Automation
Playwright integration provides:
- **Browser Automation**: Automatic clicking, input, navigation
- **Screenshots and Recording**: Visual operation process
- **Network Interception**: Monitor and modify network requests
- **Multi-browser Support**: Chromium, Firefox, WebKit

Enable and use:
```bash
# Enable Playwright
h-agent mcp enable playwright

# Configure browser options
h-agent mcp config playwright --headless false --slow-mo 100

# Use in conversation
> Open https://example.com and take a screenshot
> Fill out login form and submit
```

#### Token Extraction and Token-Free Login
Automatic authentication handling:
```bash
# Add website authentication info
h-agent mcp auth add --site example.com --cookie "session=abc123"
h-agent mcp auth add --site api.example.com --header "Authorization: Bearer xyz789"

# Extract existing tokens from browser
h-agent mcp auth extract --site example.com

# View all authentication configurations
h-agent mcp auth list
```

#### How to Configure Custom MCP
Creating custom MCP tools:
1. Create MCP configuration file
2. Define tool interface
3. Implement business logic
4. Register with h-agent

MCP configuration file (`mcp-config.yaml`):
```yaml
name: "custom-business-tool"
version: "1.0"
protocol: "mcp-v1"
tools:
  - name: "get_sales_data"
    description: "Get sales data"
    input_schema:
      type: "object"
      properties:
        date_range:
          type: "string"
          description: "Date range, e.g., '2024-01-01 to 2024-01-31'"
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

#### MCP Configuration File Details
Key configuration items:
- **name**: Tool name
- **protocol**: MCP protocol version
- **tools**: Available tool list
- **input_schema**: Input parameter validation
- **output_schema**: Output format definition
- **auth**: Authentication method configuration
- **rate_limits**: Rate limit settings

### Examples
```bash
# MCP tool usage example
$ h-agent mcp enable playwright
Playwright MCP enabled

$ h-agent mcp auth add --site crm.internal.com --cookie-file ./cookies.json
CRM authentication configured

$ h-agent chat
> Login to crm.internal.com and export this month's customer list
[Agent automatically logs into CRM using Playwright]
[Extracted customer data and saved as customers.csv]

> Get sales statistics using custom business tool
[Called custom-business-tool/get_sales_data]
Return: {"total_sales": 125000, "transactions": 45}
```

### Further Reading
- [MCP Protocol Specification](protocols/mcp.md)
- [Playwright Integration Documentation](tools/playwright.md)
- [Authentication Management Guide](security/authentication.md)

---

## Chapter 6: Advanced Configuration

### Scenario
You need to optimize h-agent's performance, switch between different AI models, use custom agent templates, or deploy in an offline environment.

### Quick Start
```bash
# Switch to different model
h-agent config --model claude-3-sonnet

# Apply agent template
h-agent template apply coding-expert

# Offline deployment
h-agent deploy offline --models local-models/

# Performance tuning
h-agent config --max-tokens 4096 --temperature 0.7
```

### Detailed Steps

#### Multi-Model Switching
Supported model types:
- **OpenAI**: gpt-4o, gpt-4o-mini, gpt-4-turbo
- **Anthropic**: claude-3-opus, claude-3-sonnet, claude-3-haiku  
- **Open Source Models**: Llama 3, Mistral, Gemma (via Ollama/LM Studio)
- **Azure**: Azure OpenAI Service

Configuring multiple models:
```bash
# Set default model
h-agent config --model gpt-4o

# Set model for specific session
h-agent session create --name cheap --model gpt-4o-mini

# Model routing rules
h-agent config --model-routing '
  simple_tasks: gpt-4o-mini
  code_review: gpt-4o  
  creative_writing: claude-3-sonnet
'
```

#### Agent Templates
Pre-defined agent configuration templates:
```bash
# View available templates
h-agent template list

# Apply template
h-agent template apply coding-expert

# Create custom template
h-agent template create my-template --from current

# Templates include:
# - System prompt
# - Tool permissions
# - Model configuration
# - Memory strategy
```

Common templates:
- **coding-expert**: Focused on code generation and debugging
- **research-assistant**: Academic research and literature analysis
- **business-analyst**: Data analysis and business insights
- **creative-writer**: Content creation and copywriting

#### Plugin System
Extending h-agent functionality:
```bash
# Install plugin
h-agent plugin install advanced-rag

# Enable plugin
h-agent plugin enable advanced-rag

# Plugin configuration
h-agent plugin config advanced-rag --chunk-size 512

# View plugin status
h-agent plugin list
```

Plugin types:
- **RAG Plugins**: Enhanced retrieval capabilities
- **Memory Plugins**: Advanced memory management
- **Security Plugins**: Additional security checks
- **UI Plugins**: Web interface extensions

#### Offline Deployment
Fully offline operation configuration:
```bash
# Download models locally
h-agent models download --provider ollama --models llama3:8b,phi3

# Configure local API endpoint
h-agent config --base-url http://localhost:11434/v1 --api-key local

# Offline mode deployment
h-agent deploy offline --workspace /opt/h-agent-offline

# Verify offline functionality
h-agent run --offline "Test offline mode"
```

Offline deployment requirements:
- Locally running model service (Ollama, LM Studio, vLLM)
- Pre-downloaded embedding models (for RAG)
- Local tool dependencies

#### Performance Tuning
Key performance parameters:
```bash
# Context length optimization
h-agent config --max-context 32000 --context-strategy truncate

# Generation parameter tuning  
h-agent config --temperature 0.3 --top-p 0.9 --max-tokens 2048

# Concurrency control
h-agent config --max-concurrent-agents 3 --tool-timeout 30

# Cache optimization
h-agent config --enable-cache true --cache-size 1GB

# Memory management
h-agent config --memory-limit 4GB --swap-enabled false
```

Performance monitoring:
```bash
# View performance statistics
h-agent stats

# Real-time monitoring
h-agent monitor

# Generate performance report
h-agent report performance
```

### Examples
```bash
# Advanced configuration example
$ h-agent config --model gpt-4o --temperature 0.2 --max-tokens 4096
Configuration updated

$ h-agent template apply coding-expert
Applying coding-expert template:
- System prompt: "You are an experienced software engineer..."
- Tool permissions: All code-related tools
- Memory strategy: Code structure priority

$ h-agent deploy offline --models ./local-models --workspace /opt/h-agent-prod
Offline deployment complete!
Configuration file: /opt/h-agent-prod/config.yaml
Model path: /opt/h-agent-prod/models/
Service port: 8080

$ h-agent stats
=== Performance Statistics ===
Average response time: 2.3s
Token usage: 156MB/day  
Concurrent sessions: 3/5
Cache hit rate: 78%
```

### Further Reading
- [Configuration Reference Manual](config/reference.md)
- [Performance Optimization Guide](performance/optimization.md)
- [Offline Deployment Best Practices](deployment/offline.md)
- [Plugin Development Documentation](plugins/development.md)

---

## Chapter 7: Buddy Companion System

### Scenario
You want a fun virtual companion to add some entertainment to daily use.

### Quick Start
```bash
# Generate companion
/buddy roll

# View companion
/buddy show
```

### Detailed Steps

#### Companion Generation
The Buddy system generates unique virtual companions for each user:
- **Rarity**: Common(★), Rare(★★), Epic(★★★), Legendary(★★★★)
- **Species**: Fox, cat, dog, dragon, rabbit, and more
- **Appearance**: Different eyes, hats, color combinations
- **Stats**: Attack, Defense, Speed, Intelligence, etc.

```bash
/buddy roll           # Randomly generate companion
/buddy roll --seed    # Use fixed seed (reproducible)
```

#### Companion Naming
```bash
/buddy name "LittleFox"   # Name companion
/buddy personality        # Set personality
```

#### Companion Display
```bash
/buddy show           # Show full card
/buddy mini           # Show mini version
/buddy bubble         # Show bubble format
```

### Examples
```
$ /buddy roll
✨ New companion generated!

╔════════════════════════════════╗
║  ★★ Epic ★★                   ║
║                                ║
║    🐕 🎩 👀                    ║
║                                ║
║  Name: Unnamed                 ║
║  Species: Dog                  ║
║  Stats:                        ║
║    ATK: 78  DEF: 45            ║
║    SPD: 62  INT: 89            ║
╚════════════════════════════════╝

$ /buddy name "Buddy"
Companion named: Buddy

$ /buddy show
╔════════════════════════════════╗
║  ★★ Epic ★★                   ║
║                                ║
║    🐕 🎩 👀                    ║
║                                ║
║  Name: Buddy                   ║
║  Species: Dog                  ║
║  Personality: Brave, Loyal     ║
║  Stats:                        ║
║    ATK: 78  DEF: 45            ║
║    SPD: 62  INT: 89            ║
╚════════════════════════════════╝
```

---

## Chapter 8: Vim Mode

### Scenario
You're a Vim user and want familiar Vim keybindings in h-agent.

### Quick Start
```bash
/vim enable    # Enable Vim mode
/vim status    # View status
```

### Detailed Steps

#### Vim Mode States
h-agent supports three Vim states:
- **Normal mode**: Default state, execute Vim commands
- **Insert mode**: Input text
- **Command mode**: Execute slash commands

#### Keybindings
Normal mode common keys:
```
i      - Enter Insert mode
:      - Enter Command mode
h/j/k/l - Directional movement
w/b    - Word jumps
dd     - Delete line
yy     - Yank line
p      - Paste
u      - Undo
Esc    - Return to Normal mode
```

Insert mode:
```
Esc    - Return to Normal mode
Ctrl+C - Interrupt
```

Command mode:
```
Enter  - Execute command
Esc    - Cancel command
```

### Examples
```
$ /vim enable
Vim mode enabled
Current state: Normal

[Normal mode]
Press i to start input...

[Insert mode]
Type your question...

[Press Esc for Normal]
Press :help for help...
```

---

## Chapter 9: Voice Mode

### Scenario
You want to input questions via voice instead of typing.

### Quick Start
```bash
/voice start    # Start recording
/voice stop     # Stop and transcribe
```

### Detailed Steps

#### Recording Control
```bash
/voice start          # Start recording
/voice stop           # Stop and transcribe
/voice cancel         # Cancel recording
/voice status         # View recording status
```

#### Configuration
```bash
# Set speech recognition service
h-agent config --stt-provider openai  # OpenAI Whisper
h-agent config --stt-provider local   # Local model

# Set recording duration limit
h-agent config --voice-max-duration 60  # Max 60 seconds
```

### Examples
```
$ /voice start
🎤 Recording started...
[Recording: 3s]

$ /voice stop
🎤 Recording stopped, transcribing...
Transcript: "Help me write a Python function to calculate Fibonacci"

[AI Response]
Sure, let me help you write a Fibonacci function...
```

---

## Chapter 10: IDE Bridge

### Scenario
You want to use h-agent directly in your IDE (VS Code, JetBrains, etc.).

### Quick Start
```bash
/bridge start    # Start bridge service
```

Then configure connection in your IDE.

### Detailed Steps

#### Starting Bridge
```bash
/bridge start           # Start HTTP server (default port 8080)
/bridge start --port 9000  # Custom port
/bridge status          # View status
/bridge stop            # Stop service
```

#### API Endpoints
Bridge service provides these APIs:
```
POST /chat              # Send message
GET /status             # View status
GET /sessions           # List sessions
POST /session/create    # Create session
GET /history/<id>       # Get history
```

#### IDE Integration
VS Code extension configuration:
```json
{
  "h-agent.bridge.url": "http://localhost:8080",
  "h-agent.bridge.enabled": true
}
```

### Examples
```
$ /bridge start
Bridge service started
Port: 8080
Status: Running

$ curl http://localhost:8080/chat -d '{"message": "hello"}'
{"response": "Hello! How can I help you?"}

$ /bridge status
Service status: Running
Port: 8080
Active connections: 2
Messages: 156
```

---

## Chapter 11: Task Scheduling

### Scenario
You want to execute tasks periodically or maintain heartbeat monitoring.

### Quick Start
```bash
/cron add "*/5 * * * *" "echo 'hello'" "Test"
/heartbeat start
```

### Detailed Steps

#### Cron Tasks
```bash
/cron add <expression> <command> <name>   # Add task
/cron list                                # List tasks
/cron enable <id>                         # Enable task
/cron disable <id>                        # Disable task
/cron delete <id>                         # Delete task
/cron history <id>                        # View execution history
```

Cron expression format:
```
* * * * *
│ │ │ │ │
│ │ │ │ └── Day of week (0-6)
│ │ │ └──── Month (1-12)
│ │ └────── Day of month (1-31)
│ └──────── Hour (0-23)
└────────── Minute (0-59)
```

Example expressions:
```
*/5 * * * *    - Every 5 minutes
0 9 * * *      - Every day at 9:00
0 */2 * * *    - Every 2 hours
30 14 * * 1-5  - Weekdays at 14:30
```

#### Heartbeat
```bash
/heartbeat start     # Start heartbeat monitoring
/heartbeat stop      # Stop heartbeat
/heartbeat status    # View status
```

Heartbeat features:
- Periodic system status checks
- Execute tasks in HEARTBEAT.md
- Automatic update checks

### Examples
```
$ /cron add "*/10 * * * *" "h-agent run 'check email'" "Email Check"
Task added: cron-001
Expression: */10 * * * *
Next run: 10:10

$ /cron list
ID         Expression       Name        Status    Next Run
cron-001   */10 * * * *    Email Check active   10:10
cron-002   0 9 * * *       Daily Report active   09:00

$ /heartbeat start
Heartbeat started
Interval: 30 minutes
Status: Running

$ /heartbeat status
Heartbeat status: Running
PID: 12345
Started: 08:00
Executions: 5
Last execution: 09:30
```

---

## Chapter 12: Plugin System

### Scenario
You want to extend h-agent's functionality by installing or developing plugins.

### Quick Start
```bash
/plugin list           # List plugins
/plugin enable <name>  # Enable plugin
```

### Detailed Steps

#### Plugin Management
```bash
/plugin list              # List all plugins
/plugin enable <name>     # Enable plugin
/plugin disable <name>    # Disable plugin
/plugin info <name>       # View plugin info
/plugin install <path>    # Install local plugin
/plugin uninstall <name>  # Uninstall plugin
```

#### Plugin Directory
Plugins are stored in `~/.h-agent/plugins/`:
```
~/.h-agent/plugins/
├── my-plugin/
│   ├── manifest.yaml    # Plugin manifest
│   ├── main.py          # Plugin entry
│   └── tools.py         # Tool definitions
│   └── handlers.py      # Command handlers
```

#### Plugin Manifest Format
```yaml
name: my-plugin
version: 1.0.0
description: My custom plugin
author: your-name
tools:
  - my_custom_tool
commands:
  - /mycommand
dependencies:
  - requests
```

### Examples
```
$ /plugin list
Name           Version  Status    Description
web-ui         1.2.0    enabled   Web Interface
advanced-rag   2.0.1    enabled   Advanced RAG
code-review    0.9.0    disabled  Code Review
my-plugin      1.0.0    enabled   Custom Plugin

$ /plugin enable code-review
Plugin enabled: code-review
New tools: review_code, check_style
New commands: /review

$ /plugin info web-ui
Name: web-ui
Version: 1.2.0
Author: h-agent-team
Description: Web interface plugin
Tools: web_start, web_stop
Commands: /web
Dependencies: flask, websocket
```

---

## Appendix: Command Reference

### Basic Commands
| Command | Description |
|---------|-------------|
| `/help [command]` | Show help |
| `/exit` | Exit |
| `/sessions` | List sessions |
| `/resume [id]` | Resume session |
| `/status` | Session status |

### Agent Commands
| Command | Description |
|---------|-------------|
| `/model` | Show current model |
| `/cost` | Token usage and cost |
| `/usage` | Detailed usage stats |
| `/config [key]` | Show config |
| `/sessions` | List saved sessions |

### Memory Commands
| Command | Description |
|---------|-------------|
| `/memory list` | List all memories |
| `/memory add <text>` | Add new memory |
| `/memory search <query>` | Search memories |
| `/memory stats` | Memory stats |
| `/memory clear` | Clear memories |

### Team Commands
| Command | Description |
|---------|-------------|
| `/team start` | Start team mode |
| `/team status` | Team status |
| `/team assign <agent>` | Assign task |

### MCP Commands
| Command | Description |
|---------|-------------|
| `/mcp add <name>` | Add MCP server |
| `/mcp list` | List MCPs |
| `/mcp status` | MCP status |

### Buddy Commands
| Command | Description |
|---------|-------------|
| `/buddy roll` | Generate companion |
| `/buddy show` | Show companion |
| `/buddy name <name>` | Name companion |
| `/buddy personality` | Set personality |

### Vim Commands
| Command | Description |
|---------|-------------|
| `/vim enable` | Enable Vim mode |
| `/vim disable` | Disable Vim mode |
| `/vim status` | Vim status |

### Voice Commands
| Command | Description |
|---------|-------------|
| `/voice start` | Start recording |
| `/voice stop` | Stop and transcribe |
| `/voice cancel` | Cancel recording |
| `/voice status` | Recording status |

### Bridge Commands
| Command | Description |
|---------|-------------|
| `/bridge start` | Start bridge |
| `/bridge stop` | Stop bridge |
| `/bridge status` | Bridge status |

### Scheduling Commands
| Command | Description |
|---------|-------------|
| `/cron add` | Add cron task |
| `/cron list` | List tasks |
| `/cron enable/disable` | Enable/disable |
| `/heartbeat start` | Start heartbeat |
| `/heartbeat stop` | Stop heartbeat |
| `/heartbeat status` | Heartbeat status |

### Plugin Commands
| Command | Description |
|---------|-------------|
| `/plugin list` | List plugins |
| `/plugin enable/disable` | Enable/disable |
| `/plugin info` | Plugin info |
| `/plugin install` | Install plugin |

---

*"I would rather make mistakes than do nothing."*
