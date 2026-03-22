# Agent Team Configuration Guide

This document describes how to configure and use a multi-agent team.

---

## 1. Quick Start

### 1.1 Initialize Team

If Web UI shows "Agent has no active handler", you need to reinitialize:

```bash
h-agent team init
```

### 1.2 View Team Status

```bash
# View all registered Agents
h-agent team list

# View team status (shows member count, pending task count, history count)
h-agent team status

# View Daemon status
h-agent status
```

**Pending tasks explanation:**
- Pending tasks are tasks that have been submitted but not yet completed
- View pending task details:
```bash
# Method 1: View task queue
h-agent team tasks

# Method 2: View logs directly
h-agent logs | grep "pending"
```

---

## 2. Launch Interface

### 2.1 Web UI

```bash
# Start Web interface
h-agent web

# Specify port
h-agent web --port 8080
```

Then open http://localhost:8080 in browser

### 2.2 Interactive CLI

```bash
h-agent chat
```

### 2.3 Single Command

```bash
h-agent team talk TeamLead "Help me develop a login feature"
```

---

## 3. Team Configuration

### 3.1 Config File Location

```
~/.h-agent/team/team_state.json
```

### 3.2 View and Edit Configuration

```bash
# View current configuration
cat ~/.h-agent/team/team_state.json

# Edit config file (manually edit JSON)
nano ~/.h-agent/team/team_state.json
```

### 3.3 Clean Up Duplicate Agents

If there are duplicate roles in `team_state.json` (e.g., multiple planners), manually edit the file to remove duplicates:

```json
{
  "members": [
    {"name": "planner", "role": "planner", ...},  // Keep only one
    {"name": "Architect", "role": "planner", ...},      // Delete this
    ...
  ]
}
```

After editing, reinitialize:
```bash
h-agent team init
```
```

### 3.3 Add New Agent

Add a new entry in the `members` array:

```json
{
  "name": "Your Agent Name",
  "role": "coordinator",  // Options: planner, coder, reviewer, devops, researcher
  "description": "Agent description",
  "system_prompt": "This Agent's responsibilities and behavior definition...",
  "enabled": true
}
```

---

## 4. Modify Existing Agent Prompts

Currently registered Agents (6 Chinese names):

| Agent Name | Role | Default Prompt |
|---------|------|----------|
| TeamLead | coordinator | empty |
| Product | researcher | empty |
| Architect | planner | empty |
| Developer | coder | empty |
| Tester | reviewer | empty |
| Operations | devops | empty |

### 4.1 Team Lead Agent Prompt Example

```json
{
  "system_prompt": "You are a technical team lead. Your team members include: Product (requirements research), Architect (solution design), Developer (code implementation), Tester (testing verification), Operations (deployment and operations).

Working methods:
1. After receiving user requirements, delegate product research via h-agent team talk Product \"requirements content\"
2. After product is complete, delegate architecture design
3. After architecture is complete, delegate development implementation
4. After development is complete, delegate testing verification
5. After tests pass, report completion to user

You can use h-agent team list to view team members."
}
```

### 4.2 Developer Agent Prompt Example

```json
{
  "system_prompt": "You are a senior software engineer.

Working methods:
1. Receive development tasks assigned by team lead
2. Write code to implement features
3. After completion, notify tester via h-agent team talk Tester \"Please test the following feature: ...\"
4. If test fails, fix issues and retest
5. After tests pass, report to team lead via h-agent team talk TeamLead \"Development complete\"

Available tools: bash to execute commands, read/write/edit for file operations."
}
```

### 4.3 Tester Agent Prompt Example

```json
{
  "system_prompt": "You are a senior test engineer.

Working methods:
1. Wait for test tasks from developer Agent
2. Write test cases
3. Execute tests
4. If test fails, notify developer via h-agent team talk Developer \"Test failed: reason\"
5. After tests pass, report to team lead via h-agent team talk TeamLead \"Tests passed\""
}
```

---

## 5. Restart to Take Effect

After modifying `team_state.json`, you need to restart the Daemon:

```bash
# Stop Daemon
h-agent stop

# Restart
h-agent start

# Or restart directly
h-agent restart
```

---

## 6. Complete Usage Workflow

### 6.1 Method 1: Web UI

```bash
# 1. Start Web UI
h-agent web

# 2. Open browser at http://localhost:8080

# 3. Send task to Team Lead Agent in the input box
# Example: "Help me develop a user login feature"
```

### 6.2 Method 2: Command Line

```bash
# 1. Start Daemon
h-agent start

# 2. Send task to team lead
h-agent team talk TeamLead "Help me develop a user login feature"

# 3. Query task status
h-agent team status

# 4. View logs
h-agent logs
```

### 6.3 Method 3: Interactive Mode

```bash
# Enter interactive mode
h-agent chat

# At the prompt, enter:
# /talk TeamLead Help me develop a login feature
```

---

## 7. Scheduled Tasks

### 7.1 View Scheduled Tasks

```bash
h-agent cron list
```

Example output:
```
ID         Name     Expression      Status    
------------------------------------------------------------
29fcd91f   Job      */1 * * * *     active    
```

- **ID**: Unique identifier for the task
- **Name**: Task name
- **Expression**: Cron expression (`* * * * *` = min hour day month weekday)
- **Status**: Task status (active=running)

### 7.2 View Scheduled Task Details

```bash
# View task execution logs
h-agent cron log <job_id>

# Manually execute a task
h-agent cron exec <job_id>
```

### 7.3 Add Scheduled Task

```bash
# Execute at 9 AM daily
h-agent cron add --name "morning" --cron "0 9 * * *" --command "python -m h_agent team talk TeamLead Good morning, please check today's tasks"
```

### 7.3 Add Evening Summary Task

```bash
# Execute at 6 PM daily
h-agent cron add --name "evening" --cron "0 18 * * *" --command "python -m h_agent team talk TeamLead Please summarize today's work"
```

---

## 8. Skill Extensions

### 8.1 View Available Skills

```bash
h-agent skill list
```

### 8.2 Enable Skill

```bash
h-agent skill enable outlook
```

### 8.3 Custom Skills

Place Skill files in:

```
~/.h-agent/skills/
```

Skill format:

```python
# ~/.h-agent/skills/my_skill.py

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "my_tool",
            "description": "Tool description",
            "parameters": {
                "type": "object",
                "properties": {
                    "arg1": {"type": "string"}
                }
            }
        }
    }
]

def my_tool(arg1: str) -> str:
    """Tool implementation"""
    return f"Result: {arg1}"
```

---

## 9. Agent Configuration (Recommended Method)

Using Agent Profile for Agent configuration is recommended to get complete session history, tool calls, and streaming output capabilities.

### 9.1 Directory Structure

Each Agent config file is located at:

```
~/.h-agent/agents/{agent_name}/
├── IDENTITY.md    # Identity definition: name, role, personality
├── SOUL.md        # Behavior guidelines: work principles, collaboration methods
├── USER.md        # User info: preferences, project context
└── config.json    # Agent configuration
```

### 9.2 Create Agent Profile

```
~/.h-agent/agents/{agent_name}/
├── IDENTITY.md    # Identity definition: name, role, personality
├── SOUL.md        # Behavior guidelines: work principles, collaboration methods
├── USER.md        # User info: preferences, project context
└── config.json    # Agent configuration
```

### 9.2 Create Agent Profile

```bash
# Create new Agent Profile
h-agent agent init MyAgent --role coordinator --description "My AI Assistant"

# List all Agent Profiles
h-agent agent list

# View Agent details
h-agent agent show MyAgent

# View Agent's sessions
h-agent agent sessions MyAgent
```

### 9.3 Edit Agent Files

```bash
# Edit IDENTITY.md
h-agent agent edit MyAgent identity

# Edit SOUL.md
h-agent agent edit MyAgent soul

# Edit USER.md
h-agent agent edit MyAgent user

# Edit config.json
h-agent agent edit MyAgent config
```

### 9.4 IDENTITY.md Example

```markdown
# MyAgent - IDENTITY

## Name
MyAgent

## Role
Technical Team Lead

## Personality Traits
Rigorous, professional, efficiency-focused

## Areas of Expertise
- Project management
- Technical architecture design
- Code review
```

### 9.5 SOUL.md Example

```markdown
# SOUL - Behavior Guidelines

## Work Principles
1. Prioritize code quality and stability
2. Pursue simple and effective solutions
3. Proactively identify and solve problems

## Collaboration Methods
1. Clearly communicate task goals and expectations
2. Provide timely feedback on progress and issues
3. Respect team members' professional opinions

## Quality Standards
- Code must pass tests
- Documentation must be updated
- Changes must go through review
```

### 9.6 Agent Capabilities

Agents configured with Profile have full capabilities:

| Capability | Description |
|------|------|
| **Session** | Each Agent has independent session history |
| **ContextGuard** | Automatic context overflow handling |
| **LongTermMemory** | Long-term memory storage and retrieval |
| **Tool Calling** | Full tool calling capabilities |
| **Skills** | Can load custom skills |

---

## 10. HTTP REST API

### 10.1 Endpoint Overview

New version Agents support streaming dialogue via HTTP API:

```
POST /api/agents/{agent_id}/message
```

### 10.2 Request Format

```bash
curl -X POST http://localhost:8080/api/agents/MyAgent/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "session_id": "optional session ID"}'
```

**Request body**:

| Field | Type | Required | Description |
|------|------|------|------|
| `message` | string | ✅ | Message to send |
| `session_id` | string | ❌ | Session ID, creates new session if not provided |

### 10.3 Response Format (SSE Stream)

Response is Server-Sent Events (SSE) stream:

```
event: token
data: {"token": "Hello"}

event: token
data: {"token": "!"}

event: tool_start
data: {"name": "bash", "args": "{"command": "ls"}"}

event: tool_end
data: {"name": "bash", "result": "README.md\nsrc/"}

event: end
data: {"done": true}
```

**Event types**:

| Event | Description |
|------|------|
| `token` | Content output character by character |
| `tool_start` | Tool execution started |
| `tool_end` | Tool execution completed |
| `error` | Error occurred |
| `end` | Dialogue ended |

### 10.4 JavaScript Call Example

```javascript
const response = await fetch('http://localhost:8080/api/agents/MyAgent/message', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({message: 'Hello', session_id: 'my-session'})
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const {done, value} = await reader.read();
  if (done) break;
  
  const text = decoder.decode(value);
  const lines = text.split('\n');
  
  for (const line of lines) {
    if (line.startsWith('event: ')) {
      currentEvent = line.slice(7);
    } else if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      if (currentEvent === 'token') {
        process.stdout.write(data.token);
      } else if (currentEvent === 'end') {
        console.log('\n[Done]');
      }
    }
  }
}
```

### 10.5 List All Agents

```bash
curl http://localhost:8080/api/agents
```

Response:

```json
{
  "success": true,
  "agents": [
    {"id": "__default__", "name": "Default Assistant", "role": "assistant"},
    {"id": "TeamLead", "name": "TeamLead", "role": "coordinator", "team": "dev-team"},
    {"id": "Developer", "name": "Developer", "role": "coder", "team": "dev-team"}
  ]
}
```

---

## 11. Team Configuration Template (legacy)

> **Note**: The following is the old configuration method based on `team_state.json`.
> **Recommended**: Use the Agent Profile method in Section 9 for Agent configuration.

Below is a complete 6-person team configuration. Copy to `~/.h-agent/team/team_state.json` to use:

```json
{
  "team_id": "dev-team",
  "members": [
    {
      "name": "TeamLead",
      "role": "coordinator",
      "description": "Technical team lead, responsible for coordinating work",
      "enabled": true,
      "system_prompt": "You are a technical team lead responsible for coordinating team work.\n\nTeam members:\n- Product (Researcher): Requirements research, output PRD\n- Architect (Planner): Technical solution design\n- Developer (Coder): Code implementation\n- Tester (Reviewer): Testing and verification\n- Operations (DevOps): Deployment and operations\n\nWorking methods:\n1. Receive user requirements\n2. Delegate product research via h-agent team talk Product \"requirements content\"\n3. After product is complete, delegate architecture design\n4. After architecture is complete, delegate development implementation\n5. After development is complete, delegate testing verification\n6. After tests pass, report completion to user\n\nYou use h-agent team talk to communicate with each Agent."
    },
    {
      "name": "Product",
      "role": "researcher",
      "description": "Product manager, responsible for requirements research",
      "enabled": true,
      "system_prompt": "You are a senior product manager responsible for requirements research and analysis.\n\nWorking methods:\n1. Receive requirements research tasks from team lead\n2. Analyze requirements, output product document (PRD format)\n3. Report results to team lead via h-agent team talk TeamLead \"PRD content\"\n\nOutput format requirements:\n## Requirements Background\n[Why this feature is needed]\n\n## Feature List\n1. [Feature 1]: Description\n2. [Feature 2]: Description\n\n## User Stories\n- As a [user], I want [feature], so that [benefit]\n\n## Priority\n- P0: Must have\n- P1: Important\n- P2: Optional"
    },
    {
      "name": "Architect",
      "role": "planner",
      "description": "Architect, responsible for technical solution design",
      "enabled": true,
      "system_prompt": "You are a senior architect responsible for technical solution design.\n\nWorking methods:\n1. Receive architecture design tasks from team lead\n2. Design technical solutions based on product PRD\n3. Report results to team lead via h-agent team talk TeamLead \"solution content\"\n\nOutput format requirements:\n## Technology Selection\n- Language/framework\n- Database\n- Middleware\n\n## System Design\n[Architecture description]\n\n## API Design\n[API list]\n\n## Data Model\n[Core data tables]"
    },
    {
      "name": "Developer",
      "role": "coder",
      "description": "Software engineer, responsible for code implementation",
      "enabled": true,
      "system_prompt": "You are a senior software engineer responsible for code implementation.\n\nWorking methods:\n1. Receive development tasks from team lead\n2. Write code referencing architecture solution\n3. After completion, notify tester via h-agent team talk Tester \"Please test: feature description\"\n4. If test fails, fix and retest\n5. After tests pass, report to team lead via h-agent team talk TeamLead \"Development complete\"\n\nAvailable tools:\n- bash: Execute commands\n- read/write/edit: File operations\n- glob: Find files"
    },
    {
      "name": "Tester",
      "role": "reviewer",
      "description": "Test engineer, responsible for testing verification",
      "enabled": true,
      "system_prompt": "You are a senior test engineer responsible for testing verification.\n\nWorking methods:\n1. Wait for test tasks from developer Agent\n2. Write test cases\n3. Execute tests\n4. If failed, notify developer via h-agent team talk Developer \"Test failed: reason\"\n5. If passed, report to team lead via h-agent team talk TeamLead \"Tests passed\"\n\nTesting principles:\n- Don't let any bug slip through\n- Test cases must cover edge cases\n- Provide clear failure reasons"
    },
    {
      "name": "Operations",
      "role": "devops",
      "description": "Operations engineer, responsible for deployment and operations",
      "enabled": true,
      "system_prompt": "You are a senior operations engineer responsible for deployment and operations.\n\nWorking methods:\n1. Receive operations tasks from team lead\n2. Output deployment solutions or operations suggestions\n3. Report to team lead via h-agent team talk TeamLead \"solution content\"\n\nFocus areas:\n- Stability\n- Security\n- Observability\n- Automation"
    }
  ]
}
```

### Usage

```bash
# 1. Backup existing configuration
cp ~/.h-agent/team/team_state.json ~/.h-agent/team/team_state.json.bak

# 2. Copy template to config file
# (Copy the JSON content above, save to ~/.h-agent/team/team_state.json)

# 3. Restart Daemon to take effect
h-agent restart

# 4. Verify
h-agent team list
```

### Customization

- **Modify workflow**: Edit each Agent's `system_prompt`
- **Add new Agent**: Add new entry in `members` array
- **Disable Agent**: Set `"enabled": false`
- **Modify Agent name**: Modify both `name` and references in prompt

---

## 12. FAQ

### Q: Web UI shows "Agent has no active handler"?
A: Run `h-agent team init` to reinitialize the team

### Q: How to delete an Agent?
A: 
- **Profile method**: Delete `~/.h-agent/agents/{agent_name}/` directory
- **team_state method**: Delete the corresponding member in `team_state.json`

### Q: How to pause an Agent?
A: Set `"enabled": false`

### Q: Configuration changes don't take effect?
A: 
- Profile method: Takes effect directly, no restart needed
- team_state method: Run `h-agent team init` to reinitialize

### Q: Forgot Agent name?
A: Run `h-agent team list` to view all Agents

### Q: How to make Agents collaborate automatically?
A: Describe the workflow in each Agent's prompt. Agents will automatically call `h-agent team talk` to collaborate based on their prompts

### Q: What does Pending tasks mean?
A: Tasks submitted but not yet completed. Use `h-agent logs | grep pending` to view details

### Q: team_state.json has duplicate roles?
A: Manually edit `~/.h-agent/team/team_state.json`, delete duplicate entries, then run `h-agent team init`

### Q: Do sessions expire and get cleaned up automatically?
A: Yes. Sessions not updated for 30 days are automatically cleaned up. Trigger timing:
- When running `h-agent start`
- When running `h-agent web`
- When manually running `h-agent session cleanup`

### Q: How to modify session expiration time?
A: Set environment variable `H_AGENT_SESSION_TTL_DAYS`, for example:
```bash
export H_AGENT_SESSION_TTL_DAYS=7  # 7 day expiration
h-agent start
```

---

## 13. Quick Command Reference

| Command | Description |
|------|------|
| `h-agent team init` | Initialize team (fix handler errors) |
| `h-agent team list` | List all Agents |
| `h-agent team status` | View team status |
| `h-agent team talk <agent> <msg>` | Send message to Agent |
| `h-agent agent list` | List all Agent Profiles |
| `h-agent agent init <name>` | Create new Agent Profile |
| `h-agent agent show <name>` | View Agent details |
| `h-agent agent edit <name> <file>` | Edit Agent files |
| `h-agent agent sessions <name>` | View Agent sessions |
| `h-agent session cleanup` | Clean up expired sessions (default 30 days) |
| `h-agent web` | Start Web UI |
| `h-agent chat` | Interactive CLI |
| `h-agent start` | Start Daemon (auto cleanup expired sessions) |
| `h-agent stop` | Stop Daemon |
| `h-agent status` | View Daemon status |
| `h-agent logs` | View logs |
| `h-agent skill list` | List Skills |
| `h-agent cron list` | List scheduled tasks |
| `h-agent cron log <job_id>` | View task logs |
| HTTP API | `POST /api/agents/{agent_id}/message` |
