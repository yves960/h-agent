#!/usr/bin/env python3
"""
s09_agent_teams.py - Multi-Agent Collaboration

When the task is too big for one, delegate to teammates.

Features:
- Multiple specialized agents
- Async mailbox communication
- Task claiming and coordination
- Protocol-based collaboration

Agent Team Architecture:
- Lead Agent: Coordinates work, assigns tasks
- Worker Agents: Execute tasks in parallel
- Shared Task Board: All agents can see and claim tasks
- Mailboxes: Agents communicate via JSONL files
"""

import os
import json
import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum
import threading
import queue

load_dotenv(override=True)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "sk-dummy"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
)
MODEL = os.getenv("MODEL_ID", "gpt-4o")

WORK_DIR = os.getcwd()
MAILBOX_DIR = Path(WORK_DIR) / ".agent_mailboxes"
MAILBOX_DIR.mkdir(exist_ok=True)


# ============================================================
# Agent Team System
# ============================================================

class AgentRole(str, Enum):
    LEAD = "lead"        # Coordinates, assigns tasks
    WORKER = "worker"    # Executes tasks
    SPECIALIST = "specialist"  # Domain-specific work


@dataclass
class AgentConfig:
    id: str
    name: str
    role: AgentRole
    specialization: str = ""  # e.g., "testing", "docs", "frontend"
    model: str = MODEL
    system_prompt: str = ""
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d["role"] = self.role.value
        return d


@dataclass 
class TeamMessage:
    id: str
    from_agent: str
    to_agent: str  # or "all" for broadcast
    type: str  # "task_assign", "task_complete", "request_help", "status_update"
    content: str
    task_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        return asdict(self)


class AgentMailbox:
    """File-based mailbox for inter-agent communication."""
    
    def __init__(self, agent_id: str, mailbox_dir: Path = MAILBOX_DIR):
        self.agent_id = agent_id
        self.mailbox_file = mailbox_dir / f"{agent_id}.jsonl"
        if not self.mailbox_file.exists():
            self.mailbox_file.touch()
    
    def send(self, message: TeamMessage):
        """Send message to this mailbox."""
        with open(self.mailbox_file, "a") as f:
            f.write(json.dumps(message.to_dict()) + "\n")
    
    def receive(self, mark_read: bool = True) -> List[TeamMessage]:
        """Receive unread messages."""
        messages = []
        lines = []
        
        with open(self.mailbox_file, "r") as f:
            for line in f:
                data = json.loads(line.strip())
                if not data.get("read"):
                    messages.append(TeamMessage(**data))
                else:
                    lines.append(line)
        
        if mark_read:
            # Mark as read
            with open(self.mailbox_file, "w") as f:
                for line in lines:
                    f.write(line)
                for msg in messages:
                    data = msg.to_dict()
                    data["read"] = True
                    f.write(json.dumps(data) + "\n")
        
        return messages
    
    def has_messages(self) -> bool:
        """Check for unread messages."""
        with open(self.mailbox_file, "r") as f:
            for line in f:
                data = json.loads(line.strip())
                if not data.get("read"):
                    return True
        return False


class AgentTeam:
    """Manages a team of collaborating agents."""
    
    def __init__(self):
        self.agents: Dict[str, AgentConfig] = {}
        self.mailboxes: Dict[str, AgentMailbox] = {}
        self.shared_tasks: Dict[str, dict] = {}  # Task board
        self.task_file = MAILBOX_DIR / "shared_tasks.json"
        self._load_tasks()
    
    def _load_tasks(self):
        if self.task_file.exists():
            self.shared_tasks = json.loads(self.task_file.read_text())
    
    def _save_tasks(self):
        self.task_file.write_text(json.dumps(self.shared_tasks, indent=2))
    
    def register_agent(self, config: AgentConfig):
        """Register an agent to the team."""
        self.agents[config.id] = config
        self.mailboxes[config.id] = AgentMailbox(config.id)
    
    def get_agent(self, agent_id: str) -> Optional[AgentConfig]:
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[AgentConfig]:
        return list(self.agents.values())
    
    def send_message(self, message: TeamMessage):
        """Send message to agent(s)."""
        if message.to_agent == "all":
            # Broadcast to all
            for agent_id in self.agents:
                if agent_id != message.from_agent:
                    self.mailboxes[agent_id].send(message)
        else:
            # Direct message
            if message.to_agent in self.mailboxes:
                self.mailboxes[message.to_agent].send(message)
    
    def get_messages(self, agent_id: str) -> List[TeamMessage]:
        """Get unread messages for an agent."""
        if agent_id in self.mailboxes:
            return self.mailboxes[agent_id].receive()
        return []
    
    def post_task(self, title: str, description: str = "", 
                  assigned_to: str = None, priority: int = 1) -> dict:
        """Post a task to the shared board."""
        task_id = f"team-task-{uuid.uuid4().hex[:8]}"
        task = {
            "id": task_id,
            "title": title,
            "description": description,
            "status": "open",
            "priority": priority,
            "assigned_to": assigned_to,
            "created_at": datetime.now().isoformat(),
            "claimed_by": None,
            "result": None,
        }
        self.shared_tasks[task_id] = task
        self._save_tasks()
        
        # Notify if assigned
        if assigned_to and assigned_to in self.mailboxes:
            self.send_message(TeamMessage(
                id=f"msg-{uuid.uuid4().hex[:8]}",
                from_agent="system",
                to_agent=assigned_to,
                type="task_assign",
                content=f"Task assigned: {title}",
                task_id=task_id,
            ))
        
        return task
    
    def claim_task(self, task_id: str, agent_id: str) -> Optional[dict]:
        """Agent claims an open task."""
        if task_id not in self.shared_tasks:
            return None
        
        task = self.shared_tasks[task_id]
        if task["status"] != "open":
            return None
        
        task["claimed_by"] = agent_id
        task["status"] = "in_progress"
        self._save_tasks()
        return task
    
    def complete_task(self, task_id: str, result: str) -> Optional[dict]:
        """Mark task as completed."""
        if task_id not in self.shared_tasks:
            return None
        
        task = self.shared_tasks[task_id]
        task["status"] = "completed"
        task["result"] = result
        task["completed_at"] = datetime.now().isoformat()
        self._save_tasks()
        return task
    
    def get_open_tasks(self) -> List[dict]:
        """Get all open/available tasks."""
        return [t for t in self.shared_tasks.values() if t["status"] == "open"]
    
    def get_my_tasks(self, agent_id: str) -> List[dict]:
        """Get tasks assigned to or claimed by an agent."""
        return [
            t for t in self.shared_tasks.values()
            if t.get("assigned_to") == agent_id or t.get("claimed_by") == agent_id
        ]


# Global team
team = AgentTeam()

# Register default agents
team.register_agent(AgentConfig(
    id="lead",
    name="Team Lead",
    role=AgentRole.LEAD,
    system_prompt="You are the team lead. Coordinate tasks, assign work, monitor progress.",
))
team.register_agent(AgentConfig(
    id="worker-1",
    name="Worker Alpha",
    role=AgentRole.WORKER,
    specialization="general",
))
team.register_agent(AgentConfig(
    id="worker-2",
    name="Worker Beta",
    role=AgentRole.WORKER,
    specialization="testing",
))


# ============================================================
# Tools
# ============================================================

import subprocess
from pathlib import Path

def tool_bash(command: str) -> str:
    if any(d in command for d in ["rm -rf /", "mkfs"]):
        return "Error: Blocked"
    try:
        r = subprocess.run(command, shell=True, cwd=WORK_DIR, capture_output=True, text=True, timeout=60)
        return (r.stdout + r.stderr).strip()[:20000] or "(no output)"
    except Exception as e:
        return f"Error: {e}"

def tool_read(path: str) -> str:
    try:
        if not os.path.isabs(path):
            path = os.path.join(WORK_DIR, path)
        return Path(path).read_text()[:10000] if Path(path).exists() else "Error: Not found"
    except Exception as e:
        return f"Error: {e}"

def tool_write(path: str, content: str) -> str:
    try:
        if not os.path.isabs(path):
            path = os.path.join(WORK_DIR, path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(content)
        return f"Wrote {len(content)} chars"
    except Exception as e:
        return f"Error: {e}"

def tool_team_list() -> str:
    """List team members."""
    agents = [a.to_dict() for a in team.list_agents()]
    return json.dumps({"team": agents}, indent=2)

def tool_team_post_task(title: str, description: str = "", assigned_to: str = None, priority: int = 1) -> str:
    """Post a task to the shared board."""
    task = team.post_task(title, description, assigned_to, priority)
    return json.dumps({"posted": task}, indent=2)

def tool_team_claim_task(task_id: str) -> str:
    """Claim an open task (as current agent)."""
    # In a real system, this would be the current agent's ID
    task = team.claim_task(task_id, "lead")  # Simplified
    if not task:
        return json.dumps({"error": "Cannot claim task"})
    return json.dumps({"claimed": task}, indent=2)

def tool_team_complete_task(task_id: str, result: str) -> str:
    """Mark task as completed."""
    task = team.complete_task(task_id, result)
    if not task:
        return json.dumps({"error": "Task not found"})
    return json.dumps({"completed": task}, indent=2)

def tool_team_get_tasks(status: str = None) -> str:
    """Get tasks from the board."""
    tasks = list(team.shared_tasks.values())
    if status:
        tasks = [t for t in tasks if t.get("status") == status]
    return json.dumps({"tasks": tasks}, indent=2)

def tool_team_send_message(to_agent: str, message_type: str, content: str, task_id: str = None) -> str:
    """Send message to another agent."""
    msg = TeamMessage(
        id=f"msg-{uuid.uuid4().hex[:8]}",
        from_agent="lead",  # Simplified
        to_agent=to_agent,
        type=message_type,
        content=content,
        task_id=task_id,
    )
    team.send_message(msg)
    return json.dumps({"sent": msg.to_dict()})

def tool_team_get_messages() -> str:
    """Get unread messages."""
    messages = team.get_messages("lead")  # Simplified
    return json.dumps({"messages": [m.to_dict() for m in messages]}, indent=2)


TOOLS = [
    {"type": "function", "function": {"name": "bash", "description": "Run command",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "read", "description": "Read file",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "write", "description": "Write file",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    # Team tools
    {"type": "function", "function": {"name": "team_list", "description": "List team members"}},
    {"type": "function", "function": {"name": "team_post_task", "description": "Post task to board",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string"}, "description": {"type": "string"},
            "assigned_to": {"type": "string"}, "priority": {"type": "integer"}},
            "required": ["title"]}}},
    {"type": "function", "function": {"name": "team_claim_task", "description": "Claim a task",
        "parameters": {"type": "object", "properties": {"task_id": {"type": "string"}}, "required": ["task_id"]}}},
    {"type": "function", "function": {"name": "team_complete_task", "description": "Complete a task",
        "parameters": {"type": "object", "properties": {"task_id": {"type": "string"}, "result": {"type": "string"}},
            "required": ["task_id", "result"]}}},
    {"type": "function", "function": {"name": "team_get_tasks", "description": "Get tasks from board",
        "parameters": {"type": "object", "properties": {"status": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "team_send_message", "description": "Send message to agent",
        "parameters": {"type": "object", "properties": {
            "to_agent": {"type": "string"}, "message_type": {"type": "string"},
            "content": {"type": "string"}, "task_id": {"type": "string"}},
            "required": ["to_agent", "message_type", "content"]}}},
    {"type": "function", "function": {"name": "team_get_messages", "description": "Get unread messages"}},
]

TOOL_HANDLERS = {
    "bash": tool_bash, "read": tool_read, "write": tool_write,
    "team_list": tool_team_list, "team_post_task": tool_team_post_task,
    "team_claim_task": tool_team_claim_task, "team_complete_task": tool_team_complete_task,
    "team_get_tasks": tool_team_get_tasks, "team_send_message": tool_team_send_message,
    "team_get_messages": tool_team_get_messages,
}


def execute_tool_call(tool_call) -> str:
    args = json.loads(tool_call.function.arguments)
    return TOOL_HANDLERS[tool_call.function.name](**args)


# ============================================================
# Agent Loop
# ============================================================

def get_system_prompt() -> str:
    open_tasks = len(team.get_open_tasks())
    messages_waiting = sum(1 for m in team.mailboxes.values() if m.has_messages())
    
    return f"""You are the lead agent in a multi-agent team at {WORK_DIR}.

Team Members: {len(team.agents)}
Open Tasks: {open_tasks}
Pending Messages: {messages_waiting}

Use team tools to:
- Post tasks to the shared board
- Assign tasks to workers
- Send messages to teammates
- Monitor progress

Coordinate effectively. Delegate when appropriate."""


def agent_loop(messages: list):
    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": get_system_prompt()}] + messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=8000,
        )
        
        message = response.choices[0].message
        messages.append({"role": "assistant", "content": message.content, "tool_calls": message.tool_calls})
        
        if not message.tool_calls:
            return
        
        for tool_call in message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            
            if name.startswith("team_"):
                print(f"\033[34m👥 {name}: {args}\033[0m")
            else:
                print(f"\033[33m$ {name}\033[0m")
            
            result = execute_tool_call(tool_call)
            print(result[:150] + ("..." if len(result) > 150 else ""))
            
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})


def main():
    print(f"\033[36mOpenAI Agent Harness - s09 (Agent Teams)\033[0m")
    print(f"Model: {MODEL}")
    print(f"Mailbox dir: {MAILBOX_DIR}")
    print(f"\nTeam members: {[a.name for a in team.list_agents()]}")
    print("\nTeam tools: team_list, team_post_task, team_claim_task, team_complete_task,")
    print("            team_get_tasks, team_send_message, team_get_messages")
    print("\nType 'q' to quit\n")
    
    history = []
    while True:
        try:
            query = input("\033[36m>> \033[0m")
        except (EOFError, KeyboardInterrupt):
            break
        
        if query.strip().lower() == "q":
            break
        
        history.append({"role": "user", "content": query})
        agent_loop(history)
        
        if history[-1].get("content"):
            print(f"\n{history[-1]['content']}\n")


if __name__ == "__main__":
    main()