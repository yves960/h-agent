# CLI Complete Command Reference

*"I would rather die than nothing."* — Ekko

Complete reference for all h-agent CLI commands.

---

## Global Commands

### h-agent --version

Display version number and exit.

```bash
h-agent --version
# Output: h-agent 1.2.3
```

### h-agent init

First-time setup wizard.

```bash
h-agent init                    # Full interactive setup wizard
h-agent init --quick           # Quick setup (minimal prompts)
```

### h-agent (no arguments)

Default to the main CLI. For clarity, the docs prefer explicit forms such as `h-agent chat`, `h-agent run`, and `h-agent session ...`.

```bash
h-agent
# Equivalent to:
h-agent chat
```

---

## Daemon

### h-agent start

Start background daemon.

```bash
h-agent start
```

**Example output**:
```
Daemon started (PID: 12345, Port: 19527)
```

### h-agent stop

Stop daemon.

```bash
h-agent stop
```

### h-agent status

Check daemon running status.

```bash
h-agent status
```

**Example output**:
```
Daemon running (PID: 12345, Port: 19527)
  Current session: sess-abc123
  Total sessions: 3
```

### h-agent logs

View daemon logs.

```bash
h-agent logs                          # View all logs
h-agent logs --tail 50               # Last 50 lines
h-agent logs --lines 100             # Last 100 lines
```

### h-agent autostart install

Install auto-start on boot.

```bash
h-agent autostart install            # Install (auto-detect platform)
h-agent autostart uninstall         # Uninstall
h-agent autostart status            # View status
```

---

## Chat and Run

### h-agent chat

Interactive chat mode with the new full-screen CLI shell.

```bash
h-agent chat                          # Use default session
h-agent chat --session my-session    # Use specified session
```

**Primary interactions**:
- `Tab` — complete slash commands
- `Up` / `Down` — browse local input history
- `F1` — toggle the help overlay
- `Ctrl+C` or `/exit` — exit chat

**Recommended workflow**:
- use `h-agent session list/history/create` for session management
- use `h-agent chat --session <name>` to enter a specific session

### h-agent run

Single command mode, exits after execution.

```bash
h-agent run "Write a quicksort for me"
h-agent run --session my "Explain what this code does"
h-agent run "Check git status and commit"
```

---

## Session Management

### h-agent session list

List all sessions.

```bash
h-agent session list                     # List all
h-agent session list --tag bug          # Filter by tag
h-agent session list --group frontend   # Filter by group
```

### h-agent session create

Create new session.

```bash
h-agent session create                  # Create unnamed session
h-agent session create --name my-task  # Create named session
h-agent session create --name review --group code  # With group
```

### h-agent session history

View session history.

```bash
h-agent session history <session_id>    # By ID
h-agent session history my-task         # By name (auto match)
```

### h-agent session delete

Delete session.

```bash
h-agent session delete <session_id>
h-agent session delete old-session
```

### h-agent session search

Search session content.

```bash
h-agent session search "login feature"
h-agent session search "git commit" --days 30  # Last 30 days
```

### h-agent session rename

Rename session.

```bash
h-agent session rename <session_id> new-name
```

### h-agent session tag

Session tag management.

```bash
h-agent session tag list                        # List all tags
h-agent session tag add <session_id> bug        # Add tag
h-agent session tag remove <session_id> bug     # Remove tag
h-agent session tag get <session_id>            # View session tags
```

### h-agent session group

Session group management.

```bash
h-agent session group list                      # List all groups
h-agent session group set <session_id> frontend # Set group
h-agent session group set <session_id> ""      # Clear group
h-agent session group sessions frontend         # View sessions in group
```

---

## RAG (Codebase Search)

### h-agent rag index

Index codebase.

```bash
h-agent rag index                          # Index current directory
h-agent rag index --directory ./src       # Index specified directory
```

### h-agent rag search

Search codebase.

```bash
h-agent rag search "user authentication"              # Semantic search
h-agent rag search "email sending" --limit 10  # Limit results
```

### h-agent rag stats

View index statistics.

```bash
h-agent rag stats
h-agent rag stats --directory ./src
```

---

## Configuration Management

### h-agent config --show

Show current configuration.

```bash
h-agent config --show
```

### h-agent config --api-key

Set API Key.

```bash
h-agent config --api-key sk-xxxx        # Set directly
h-agent config --api-key __prompt__     # Interactive secure input
h-agent config --clear-key              # Clear API Key
```

### h-agent config --base-url

Set API Base URL.

```bash
h-agent config --base-url https://api.deepseek.com/v1
h-agent config --base-url http://localhost:11434/v1  # Ollama
```

### h-agent config --model

Set model.

```bash
h-agent config --model gpt-4o
h-agent config --model deepseek-chat
```

### h-agent config --profile

Profile management.

```bash
h-agent config --list-all                  # List all Profiles
h-agent config --profile work              # Switch to work Profile
h-agent config --profile-create new-profile # Create new Profile
h-agent config --profile-delete old-profile # Delete Profile
```

### h-agent config --wizard

Interactive setup wizard.

```bash
h-agent config --wizard
```

### h-agent config --export / --import

Configuration import/export.

```bash
h-agent config --export            # Export to JSON
h-agent config --import config.json  # Import from JSON
```

---

## Plugin Management

### h-agent plugin list

List all plugins.

```bash
h-agent plugin list
```

### h-agent plugin info

View plugin details.

```bash
h-agent plugin info <plugin_name>
```

### h-agent plugin enable

Enable plugin.

```bash
h-agent plugin enable <plugin_name>
```

### h-agent plugin disable

Disable plugin.

```bash
h-agent plugin disable <plugin_name>
```

### h-agent plugin install

Install plugin (from URL).

```bash
h-agent plugin install https://github.com/user/h-agent-myplugin
```

### h-agent plugin uninstall

Uninstall plugin.

```bash
h-agent plugin uninstall <plugin_name>
```

---

## Skill Management

### h-agent skill list

List all skills.

```bash
h-agent skill list              # Only available skills
h-agent skill list --all        # Include disabled skills
```

### h-agent skill info

View skill details.

```bash
h-agent skill info coding-agent
```

### h-agent skill enable

Enable skill.

```bash
h-agent skill enable github
```

### h-agent skill disable

Disable skill.

```bash
h-agent skill disable weather
```

### h-agent skill install

Install skill (via pip).

```bash
h-agent skill install tavily
h-agent skill install myskill --package h_agent_skill_myskill
```

### h-agent skill uninstall

Uninstall skill.

```bash
h-agent skill uninstall old-skill
```

### h-agent skill run

Run skill function.

```bash
h-agent skill run github issues owner/repo --limit 5
h-agent skill run weather "Beijing"
```

---

## Long-term Memory

### h-agent memory list

List memories.

```bash
h-agent memory list                        # All
h-agent memory list --type decision        # Filter by type
```

### h-agent memory add

Add memory.

```bash
h-agent memory add fact "python-version" "3.11"
h-agent memory add decision "db-choice" "PostgreSQL" --reason "Need transaction support"
h-agent memory add user "boss-name" "Zhang San" --tags personal,work
```

**Type options**: `user` | `project` | `decision` | `fact` | `error`

### h-agent memory get

Get memory.

```bash
h-agent memory get fact python-version
```

### h-agent memory delete

Delete memory.

```bash
h-agent memory delete decision db-choice
```

### h-agent memory search

Search memories.

```bash
h-agent memory search "Python"                  # Search keyword
h-agent memory search "deployment" --days 30         # Last 30 days
h-agent memory search "" --sessions            # Also search session history
```

### h-agent memory dump

Export memories as text.

```bash
h-agent memory dump                  # All
h-agent memory dump --type decision # By type
```

---

## Agent Team

### h-agent team

Team management.

```bash
h-agent team list          # List team members
h-agent team status       # View team status
h-agent team init         # Initialize team workspace
```

---

## Model Management

### h-agent model list

List available models.

```bash
h-agent model list
```

### h-agent model switch

Switch model.

```bash
h-agent model switch gpt-4o-mini
```

### h-agent model info

View model information.

```bash
h-agent model info gpt-4o
```

### h-agent model add

Add custom model.

```bash
h-agent model add
# Interactive add (name, base URL, etc.)
```

---

## Template Management

### h-agent template list

List all templates.

```bash
h-agent template list
```

### h-agent template show

View template details.

```bash
h-agent template show code-review
```

### h-agent template apply

Apply template.

```bash
h-agent template apply code-review
```

### h-agent template create

Create new template.

```bash
h-agent template create my-template
```

### h-agent template delete

Delete template.

```bash
h-agent template delete old-template
```

---

## Web UI

### h-agent web

Start Web UI server.

```bash
h-agent web                           # Default port 8080
h-agent web --port 9000              # Specify port
h-agent web --no-browser             # Don't auto-open browser
```

---

## Command Quick Reference

| Command | Description |
|------|------|
| `h-agent init` | First-time configuration |
| `h-agent chat` | Interactive chat |
| `h-agent run "..."` | Single command |
| `h-agent start/stop/status/logs` | Daemon management |
| `h-agent session list/create/history/delete/search/rename/tag/group` | Session management |
| `h-agent rag index/search/stats` | Codebase search |
| `h-agent config --show` | View configuration |
| `h-agent plugin list/info/enable/disable/install/uninstall` | Plugin management |
| `h-agent skill list/info/enable/disable/install/uninstall/run` | Skill management |
| `h-agent memory list/add/get/delete/search/dump` | Long-term memory |
| `h-agent team list/status/init` | Team management |
| `h-agent model list/switch/info/add` | Model management |
| `h-agent template list/show/apply/create/delete` | Template management |
| `h-agent web [--port]` | Web UI |
| `h-agent --version` | Version info |

---

## Notes

- **Session name matching**: All commands accepting `session_id` support name auto-matching
- **Tab completion**: Supports bash/zsh tab completion (auto-configured after first run of `h-agent init`)
- **Progress bar**: Large file operations and indexing tasks automatically show progress bar
- **Ctrl+C**: Most commands support `Ctrl+C` interruption, won't create zombie processes
- **Exit code**: Returns `0` on success, `1` on failure
