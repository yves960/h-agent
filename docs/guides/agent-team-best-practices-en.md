# Agent Team Configuration Best Practices

This document teaches you how to configure a complete multi-agent team from scratch.

---

## 1. Project Structure

Recommended structure for organizing your configuration:

```
h-agent-config/
├── __init__.py
├── agents/                 # Agent definitions
│   ├── __init__.py
│   ├── prompts.py         # System Prompts for all Agents
│   └── roles.py           # Agent role configurations
├── team.py                # Team initialization
├── workflows/             # Workflow configurations
│   ├── __init__.py
│   ├── morning.py         # Morning routine
│   └── evening.py        # Evening routine
├── skills/               # Custom Skills (optional)
│   ├── __init__.py
│   └── email_check.py
└── main.py               # Entry point
```

---

## 2. Defining Agent Roles

### 2.1 Role Enumeration

```python
# agents/roles.py
from h_agent.team.team import AgentRole

# Extended role enumeration (optional, if you need more roles)
class MyAgentRole(AgentRole):
    PRODUCT = "product"
    ARCHITECT = "architect"
    OPERATIONS = "operations"
```

### 2.2 Predefined Role Mapping

| Your Required Role | h-agent Predefined Role | Description |
|------------|------------------|------|
| Team Lead | COORDINATOR | Coordinate work |
| Product | RESEARCHER | Research and analysis |
| Architect | PLANNER | Task planning |
| Developer | CODER | Code implementation |
| Tester | REVIEWER | Review and verification |
| Operations | DEVOPS | Deployment and operations |

---

## 3. Writing System Prompts

This is the **most critical** configuration. Each Agent's capabilities and personality are determined by it.

### 3.1 Prompt Structure

```python
# agents/prompts.py

# ============ Team Lead Agent ============
LEADER_PROMPT = """You are a technical team lead responsible for coordinating team work.

Team members:
- Product (Researcher): Requirements research, output PRD
- Architect (Planner): Technical solution design
- Developer (Coder): Code implementation
- Tester (Reviewer): Testing and verification
- Operations (DevOps): Deployment and operations

Your responsibilities:
1. Understand user requirements
2. Decompose tasks and delegate to appropriate Agents
3. Track progress and coordinate issues
4. Report results to users

【Key Rules】
- Delegate tasks via team.delegate("Agent name", "task type", "task content")
- Query status via team.query("Agent name", "question")
- Chat with Agent via team.talk_to("Agent name", "message")
- Automatically delegate testing after development is complete, don't wait

【Morning Routine】
At the start of each workday, you should:
1. Check each Agent's yesterday work summary
2. Check for urgent tasks
3. Brief users on today's plan

【Evening Routine】
At the end of each day, you should:
1. Collect work summaries from each Agent
2. Compile into daily report
3. Compress memory
"""

# ============ Product Agent ============
PRODUCT_PROMPT = """You are a senior product manager.

Responsibility: Receive requirements research tasks, output Product Requirements Document (PRD)

Output format:
## Requirements Background
[Why this feature is needed]

## Feature List
1. [Feature 1]: Description
2. [Feature 2]: Description

## User Stories
- As a [user], I want [feature], so that [benefit]

## Priority
- P0: [Must have]
- P1: [Important]
- P2: [Optional]

【Workflow】
1. Receive delegation from team lead
2. Analyze requirements
3. Output PRD
4. Report to team lead via team.delegate("Team Lead", "complete", PRD content)
"""

# ============ Architect Agent ============
ARCHITECT_PROMPT = """You are a senior architect.

Responsibility: Design technical solutions based on requirements and PRD

Output format:
## Technology Selection
- Language/framework
- Database
- Middleware

## System Design
[Architecture diagram or text description]

## API Design
[API interface list]

## Data Model
[Core data table structure]

【Workflow】
1. Receive delegation from team lead
2. Reference product PRD
3. Output technical solution
4. Report to team lead via team.delegate("Team Lead", "complete", solution content)
"""

# ============ Developer Agent ============
DEVELOPER_PROMPT = """You are a senior software engineer.

Responsibility: Implement code based on requirements and architecture

【Key Rules】
1. Must automatically notify tester after completion:
   team.delegate("Tester", "test", "test content")
2. If test fails, fix and retest
3. Report to team lead after tests pass

【Available Tools】
- bash: Execute commands
- read/write/edit: File operations
- glob: Find files

【Workflow】
1. Receive delegation from team lead
2. Reference architecture solution
3. Write code
4. Execute test verification
5. Notify tester Agent
6. Fix issues upon test feedback (if any)
7. Report to team lead after tests pass
"""

# ============ Tester Agent ============
TESTER_PROMPT = """You are a senior test engineer.

Responsibility: Test code submitted by developers

Output format:
## Test Results
- Pass: ✓
- Fail: ✗ (with reason)

## Test Cases
1. [Test case 1]: Pass/Fail
2. [Test case 2]: Pass/Fail

【Workflow】
1. Wait for test requests from developer Agent
2. Write test cases
3. Execute tests
4. Report results to developer Agent:
   team.talk_to("Developer", "Test failed: reason")
5. Or report to team lead:
   team.delegate("Team Lead", "complete", "Tests passed")
"""

# ============ Operations Agent ============
OPS_PROMPT = """You are a senior operations engineer.

Responsibility: Deployment solutions, operations documentation

【Workflow】
1. Receive delegation from team lead
2. Output deployment solution
3. Report to team lead
"""

# ============ Summary ============
PROMPTS = {
    "Team Lead": LEADER_PROMPT,
    "Product": PRODUCT_PROMPT,
    "Architect": ARCHITECT_PROMPT,
    "Developer": DEVELOPER_PROMPT,
    "Tester": TESTER_PROMPT,
    "Operations": OPS_PROMPT,
}
```

---

## 4. Initializing the Team

```python
# team.py
from h_agent.team.team import AgentTeam, AgentRole
from h_agent.core.client import get_client
from h_agent.core.config import MODEL
from agents.prompts import PROMPTS

def create_llm_handler(name: str, prompt: str):
    """Create LLM Handler for Agent"""
    client = get_client()
    
    def handler(msg) -> dict:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Task type: {msg.type}\nTask content: {msg.content}"}
            ],
            max_tokens=4096,
        )
        return {
            "agent_name": name,
            "role": "coordinator",
            "success": True,
            "content": response.choices[0].message.content,
        }
    return handler

def init_team(team_id: str = "my-team") -> AgentTeam:
    """Initialize team"""
    team = AgentTeam(team_id=team_id)
    
    role_map = {
        "Team Lead": AgentRole.COORDINATOR,
        "Product": AgentRole.RESEARCHER,
        "Architect": AgentRole.PLANNER,
        "Developer": AgentRole.CODER,
        "Tester": AgentRole.REVIEWER,
        "Operations": AgentRole.DEVOPS,
    }
    
    for name, role in role_map.items():
        team.register(
            name=name,
            role=role,
            handler=create_llm_handler(name, PROMPTS[name]),
            description=f"{name}Agent",
        )
        print(f"✓ Registered {name}Agent")
    
    return team

# Convenience function
def get_team() -> AgentTeam:
    """Get initialized team (singleton)"""
    if not hasattr(get_team, "_team"):
        get_team._team = init_team()
    return get_team._team
```

---

## 5. Basic Usage

```python
# main.py
from team import get_team

def main():
    team = get_team()
    
    # Assign task to team lead
    result = team.delegate("Team Lead", "task", "Help me develop a user login feature")
    print(result.content)

if __name__ == "__main__":
    main()
```

Run with:
```bash
python main.py
```

---

## 6. Morning/Evening Routines

### 6.1 Morning Routine

```python
# workflows/morning.py
from team import get_team

def morning_brief():
    """Morning brief"""
    team = get_team()
    
    print("="*50)
    print("🌅 Morning Brief")
    print("="*50)
    
    # Query each Agent's yesterday work summary
    for agent in ["Product", "Developer", "Tester", "Operations"]:
        result = team.query(agent, "Please briefly describe what you completed yesterday")
        print(f"\n【{agent}】:\n{result.content[:300]}...")
    
    # Get today's plan from team lead
    plan = team.query("Team Lead", "Based on yesterday's situation, list today's work plan")
    print(f"\n【Today's Plan】:\n{plan.content}")

    return plan.content
```

### 6.2 Evening Routine

```python
# workflows/evening.py
from team import get_team

def evening_summary():
    """Evening summary"""
    team = get_team()
    
    print("="*50)
    print("🌙 Evening Summary")
    print("="*50)
    
    # Collect work summaries from each Agent
    summaries = {}
    for agent in ["Product", "Developer", "Tester", "Operations"]:
        result = team.query(agent, "Please summarize what you completed today")
        summaries[agent] = result.content
        print(f"\n【{agent}】:\n{result.content[:200]}...")
    
    # Team lead compiles
    summary_prompt = "Compile the following work summaries into a daily report:\n" + "\n".join([
        f"{k}: {v}" for k, v in summaries.items()
    ])
    report = team.query("Team Lead", summary_prompt)
    print(f"\n【Daily Report】:\n{report.content}")
    
    return report.content
```

---

## 7. Scheduled Tasks Configuration

### 7.1 Using Heartbeat

```python
# scheduler.py
from h_agent.scheduler.heartbeat import HeartbeatMonitor
from workflows.morning import morning_brief
from workflows.evening import evening_summary

def start_scheduler():
    """Start scheduled tasks"""
    scheduler = HeartbeatMonitor()
    
    # Execute morning brief at 9 AM daily
    scheduler.add_job(
        name="morning_brief",
        cron="@daily",
        command="python -c 'from workflows.morning import morning_brief; morning_brief()'",
        enabled=True,
    )
    
    # Execute evening summary at 6 PM daily
    scheduler.add_job(
        name="evening_summary", 
        cron="0 18 * * *",  # Every day at 18:00
        command="python -c 'from workflows.evening import evening_summary; evening_summary()'",
        enabled=True,
    )
    
    # Start (daemon mode)
    scheduler.start(daemon=True)
```

### 7.2 Using System Cron

```bash
# Add to crontab
crontab -e

# Every day at 9 AM
0 9 * * * cd /path/to/project && python main.py --morning

# Every day at 6 PM
0 18 * * * cd /path/to/project && python main.py --evening
```

Corresponding `main.py`:
```python
import sys

def main():
    if "--morning" in sys.argv:
        from workflows.morning import morning_brief
        morning_brief()
    elif "--evening" in sys.argv:
        from workflows.evening import evening_summary
        evening_summary()
    else:
        # Interactive mode
        team = get_team()
        team.talk_to("Team Lead", input("Please enter task: "))
```

---

## 8. Custom Skills

If you need to extend capabilities (e.g., checking emails), you can create a Skill:

```python
# skills/email_check.py
"""Email Check Skill"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "check_emails",
            "description": "Check unread emails in mailbox",
            "parameters": {
                "type": "object",
                "properties": {
                    "account": {"type": "string", "description": "Email account"},
                    "limit": {"type": "integer", "description": "Maximum number to check", "default": 10},
                },
                "required": ["account"],
            },
        },
    }
]

def check_emails(account: str, limit: int = 10) -> str:
    """Check emails (actual implementation requires email API integration)"""
    # TODO: Implement email check logic
    return f"Unread emails: 3\n1. [Subject 1]\n2. [Subject 2]\n3. [Subject 3]"

HANDLERS = {
    "check_emails": check_emails,
}
```

Register with team:
```python
def init_team_with_skills() -> AgentTeam:
    from skills.email_check import TOOLS, HANDLERS
    
    team = init_team()
    
    # Add email Skill to team lead
    team.members["Team Lead"].tools.extend(TOOLS)
    
    return team
```

---

## 9. Complete Project Template

Create a quick-start template project:

```bash
mkdir my-agent-team && cd my-agent-team
```

Create the following files:

### 9.1 agents/prompts.py
```python
# See Section 3.1 above
```

### 9.2 team.py
```python
# See Section 4 above
```

### 9.3 main.py
```python
#!/usr/bin/env python3
import sys
from team import get_team

def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "--morning":
            from workflows.morning import morning_brief
            morning_brief()
            return
        elif cmd == "--evening":
            from workflows.evening import evening_summary
            evening_summary()
            return
    
    # Default: Send task to team lead
    team = get_team()
    task = input("\nPlease describe your request (enter q to quit): ")
    if task.lower() == 'q':
        return
    
    result = team.delegate("Team Lead", "task", task)
    print("\n" + "="*50)
    print("【Team Lead Response】")
    print("="*50)
    print(result.content)

if __name__ == "__main__":
    main()
```

### 9.4 workflows/__init__.py
```python
# workflows package
```

### 9.5 workflows/morning.py
```python
# See Section 6.1 above
```

### 9.6 workflows/evening.py
```python
# See Section 6.2 above
```

---

## 10. Running

```bash
# Interactive mode
python main.py

# Morning brief
python main.py --morning

# Evening summary
python main.py --evening

# Configure scheduled tasks (add to crontab)
echo "0 9 * * * cd $(pwd) && python main.py --morning" >> ~/.crontab
echo "0 18 * * * cd $(pwd) && python main.py --evening" >> ~/.crontab
```

---

## 11. Debugging Tips

### 11.1 View Team Status
```python
team = get_team()
print(team.list_members())  # List all Agents
print(team.pending_tasks)   # View pending tasks
print(team.history)         # View history
```

### 11.2 Test Individual Agent
```python
team = get_team()
result = team.query("Developer", "Hello, please introduce yourself")
print(result.content)
```

### 11.3 View Agent System Prompt
```python
team = get_team()
print(team.members["Developer"].system_prompt)
```

---

## 12. FAQ

### Q: What if an Agent doesn't work as expected?
A: Adjust the System Prompt, the more specific the better. Prompt is the only control method.

### Q: How to make an Agent remember context?
A: Each Agent call is independent. If you need memory, include context in the prompt.

### Q: What if task delegation fails?
A: Check if the Agent name is correct: `team.list_members()`

### Q: How to add a new Agent role?
A: Simply add to `role_map`, use `AgentRole.COORDINATOR` or extend the enumeration.

---

## Summary

Core of configuring Agent Team:
1. **Write good System Prompts** — Determines Agent behavior and capabilities
2. **Correct delegation calls** — `delegate()`, `query()`, `talk_to()`
3. **Reasonable scheduled tasks** — Automate morning/evening Routines

Now start configuring your team!
