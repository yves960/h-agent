#!/usr/bin/env python3
"""
s11_autonomous_agents.py - Autonomous Agents (OpenAI Version)

Agents that find work themselves when idle.

Lifecycle:
1. WORK: Execute tasks using tools
2. IDLE: Poll for new work (inbox messages, unclaimed tasks)
3. SHUTDOWN: After timeout or explicit shutdown

Key insight: "The agent finds work itself."
"""

import os
import json
import time
import uuid
import threading
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

load_dotenv(override=True)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "sk-dummy"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
)
MODEL = os.getenv("MODEL_ID", "gpt-4o")

WORK_DIR = Path.cwd()
TEAM_DIR = WORK_DIR / ".team"
TEAM_DIR.mkdir(exist_ok=True)

INBOX_DIR = TEAM_DIR / "inbox"
INBOX_DIR.mkdir(exist_ok=True)

TASKS_DIR = WORK_DIR / ".tasks"
TASKS_DIR.mkdir(exist_ok=True)

POLL_INTERVAL = 5  # seconds
IDLE_TIMEOUT = 60  # seconds


# ============================================================
# Agent Identity
# ============================================================

@dataclass
class AgentIdentity:
    agent_id: str
    name: str
    role: str
    team: str
    skills: List[str] = None
    
    def __post_init__(self):
        if self.skills is None:
            self.skills = []
    
    def to_prompt(self) -> str:
        return f"""You are '{self.name}', role: {self.role}, team: {self.team}.
Agent ID: {self.agent_id}
Skills: {', '.join(self.skills) if self.skills else 'general'}

When idle, look for work in:
1. Your inbox (.team/inbox/{self.agent_id}.jsonl)
2. Unclaimed tasks (.tasks/*.json)

Claim tasks that match your skills. Complete them efficiently."""


# ============================================================
# Task Board
# ============================================================

class TaskStatus(str, Enum):
    OPEN = "open"
    CLAIMED = "claimed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    id: str
    title: str
    description: str
    status: TaskStatus
    claimed_by: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    result: str = ""
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d
    
    @classmethod
    def from_dict(cls, d: dict) -> "Task":
        d["status"] = TaskStatus(d.get("status", "open"))
        return cls(**d)


class TaskBoard:
    """File-based task board for autonomous agents."""
    
    def __init__(self, tasks_dir: Path = TASKS_DIR):
        self.tasks_dir = tasks_dir
    
    def create_task(self, title: str, description: str = "") -> Task:
        """Create a new task."""
        task = Task(
            id=f"task-{uuid.uuid4().hex[:8]}",
            title=title,
            description=description,
            status=TaskStatus.OPEN,
            created_at=datetime.now().isoformat(),
        )
        self._save_task(task)
        return task
    
    def _save_task(self, task: Task):
        """Save task to file."""
        task_file = self.tasks_dir / f"{task.id}.json"
        task_file.write_text(json.dumps(task.to_dict(), indent=2))
    
    def _load_task(self, task_id: str) -> Optional[Task]:
        """Load task from file."""
        task_file = self.tasks_dir / f"{task_id}.json"
        if not task_file.exists():
            return None
        return Task.from_dict(json.loads(task_file.read_text()))
    
    def list_open_tasks(self) -> List[Task]:
        """List all open (unclaimed) tasks."""
        tasks = []
        for task_file in self.tasks_dir.glob("task-*.json"):
            try:
                task = Task.from_dict(json.loads(task_file.read_text()))
                if task.status == TaskStatus.OPEN:
                    tasks.append(task)
            except:
                pass
        return tasks
    
    def claim_task(self, task_id: str, agent_id: str) -> Optional[Task]:
        """Claim an open task."""
        task = self._load_task(task_id)
        if not task or task.status != TaskStatus.OPEN:
            return None
        
        task.status = TaskStatus.CLAIMED
        task.claimed_by = agent_id
        task.updated_at = datetime.now().isoformat()
        self._save_task(task)
        return task
    
    def start_task(self, task_id: str) -> Optional[Task]:
        """Mark task as in progress."""
        task = self._load_task(task_id)
        if not task:
            return None
        
        task.status = TaskStatus.IN_PROGRESS
        task.updated_at = datetime.now().isoformat()
        self._save_task(task)
        return task
    
    def complete_task(self, task_id: str, result: str = "") -> Optional[Task]:
        """Mark task as completed."""
        task = self._load_task(task_id)
        if not task:
            return None
        
        task.status = TaskStatus.COMPLETED
        task.result = result
        task.updated_at = datetime.now().isoformat()
        self._save_task(task)
        return task


# Global task board
task_board = TaskBoard()


# ============================================================
# Message Bus
# ============================================================

def send_message(to_agent: str, message: dict):
    """Send a message to an agent's inbox."""
    inbox_file = INBOX_DIR / f"{to_agent}.jsonl"
    with open(inbox_file, "a") as f:
        f.write(json.dumps(message) + "\n")


def read_messages(agent_id: str) -> List[dict]:
    """Read and clear messages from inbox."""
    inbox_file = INBOX_DIR / f"{agent_id}.jsonl"
    if not inbox_file.exists():
        return []
    
    messages = []
    with open(inbox_file, "r") as f:
        for line in f:
            if line.strip():
                messages.append(json.loads(line))
    
    # Clear inbox
    inbox_file.write_text("")
    return messages


# ============================================================
# Autonomous Agent
# ============================================================

class AutonomousAgent:
    """An agent that finds work itself."""
    
    def __init__(self, identity: AgentIdentity):
        self.identity = identity
        self.messages: List[dict] = []
        self.running = True
        self.idle_time = 0
    
    def get_system_prompt(self) -> str:
        """Get system prompt with identity."""
        return self.identity.to_prompt()
    
    def inject_identity(self):
        """Re-inject identity after context compression."""
        if not self.messages or self.messages[0].get("role") != "system":
            self.messages.insert(0, {"role": "system", "content": self.get_system_prompt()})
    
    def check_for_work(self) -> Optional[str]:
        """Check for work in inbox or task board."""
        # Check inbox
        messages = read_messages(self.identity.agent_id)
        if messages:
            # Process first message
            msg = messages[0]
            if msg.get("type") == "task":
                return f"New task from inbox: {msg.get('content', '')}"
            elif msg.get("type") == "shutdown":
                self.running = False
                return "Shutdown requested"
        
        # Check for unclaimed tasks
        open_tasks = task_board.list_open_tasks()
        if open_tasks:
            # Auto-claim first matching task
            task = open_tasks[0]
            claimed = task_board.claim_task(task.id, self.identity.agent_id)
            if claimed:
                return f"Auto-claimed task: {task.title}\nDescription: {task.description}"
        
        return None
    
    def work_cycle(self, user_input: str = None):
        """One work cycle: process input, execute tools, return when idle."""
        if user_input:
            self.messages.append({"role": "user", "content": user_input})
        
        while True:
            self.inject_identity()
            
            response = client.chat.completions.create(
                model=MODEL,
                messages=self.messages,
                tools=self._get_tools(),
                tool_choice="auto",
                max_tokens=4000,
            )
            
            message = response.choices[0].message
            self.messages.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": message.tool_calls,
            })
            
            # No tool calls = idle
            if not message.tool_calls:
                return "idle"
            
            # Execute tools
            for tool_call in message.tool_calls:
                result = self._execute_tool(tool_call)
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })
    
    def _get_tools(self):
        """Get available tools."""
        return [
            {"type": "function", "function": {
                "name": "bash",
                "description": "Run a shell command",
                "parameters": {
                    "type": "object",
                    "properties": {"command": {"type": "string"}},
                    "required": ["command"],
                }
            }},
            {"type": "function", "function": {
                "name": "list_tasks",
                "description": "List open tasks",
                "parameters": {"type": "object", "properties": {}},
            }},
            {"type": "function", "function": {
                "name": "claim_task",
                "description": "Claim an open task",
                "parameters": {
                    "type": "object",
                    "properties": {"task_id": {"type": "string"}},
                    "required": ["task_id"],
                }
            }},
            {"type": "function", "function": {
                "name": "complete_task",
                "description": "Mark a task as completed",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string"},
                        "result": {"type": "string"},
                    },
                    "required": ["task_id"],
                }
            }},
            {"type": "function", "function": {
                "name": "check_inbox",
                "description": "Check inbox for messages",
                "parameters": {"type": "object", "properties": {}},
            }},
        ]
    
    def _execute_tool(self, tool_call) -> str:
        """Execute a tool call."""
        import subprocess
        
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        
        if name == "bash":
            try:
                r = subprocess.run(args["command"], shell=True, cwd=WORK_DIR, 
                                  capture_output=True, text=True, timeout=60)
                return (r.stdout + r.stderr)[:10000] or "(no output)"
            except Exception as e:
                return f"Error: {e}"
        
        elif name == "list_tasks":
            tasks = [t.to_dict() for t in task_board.list_open_tasks()]
            return json.dumps({"open_tasks": tasks})
        
        elif name == "claim_task":
            task = task_board.claim_task(args["task_id"], self.identity.agent_id)
            if task:
                task_board.start_task(args["task_id"])
                return json.dumps({"claimed": task.to_dict()})
            return json.dumps({"error": "Cannot claim task"})
        
        elif name == "complete_task":
            task = task_board.complete_task(args["task_id"], args.get("result", ""))
            if task:
                return json.dumps({"completed": task.to_dict()})
            return json.dumps({"error": "Task not found"})
        
        elif name == "check_inbox":
            messages = read_messages(self.identity.agent_id)
            return json.dumps({"messages": messages})
        
        return f"Unknown tool: {name}"
    
    def run(self):
        """Main autonomous loop."""
        print(f"\033[36m🤖 {self.identity.name} started\033[0m")
        print(f"   Role: {self.identity.role}")
        print(f"   Team: {self.identity.team}")
        
        while self.running:
            # Work cycle
            result = self.work_cycle("What should I do?")
            
            if result == "idle":
                # Check for work periodically
                self.idle_time = 0
                while self.idle_time < IDLE_TIMEOUT:
                    work = self.check_for_work()
                    if work:
                        print(f"\033[32m📋 Found work: {work[:50]}...\033[0m")
                        self.work_cycle(work)
                        self.idle_time = 0
                        break
                    
                    time.sleep(POLL_INTERVAL)
                    self.idle_time += POLL_INTERVAL
                
                if self.idle_time >= IDLE_TIMEOUT:
                    print(f"\033[33m⏰ Idle timeout reached, shutting down\033[0m")
                    break
        
        print(f"\033[36m👋 {self.identity.name} stopped\033[0m")


def main():
    print(f"\033[36mOpenAI Agent Harness - s11 (Autonomous Agents)\033[0m")
    print(f"Model: {MODEL}")
    print(f"Tasks dir: {TASKS_DIR}")
    print("\nAgents find work themselves when idle.")
    print("Create tasks in .tasks/ or send messages to inbox.\n")
    
    # Create a sample autonomous agent
    identity = AgentIdentity(
        agent_id="worker-1",
        name="Worker Alpha",
        role="backend developer",
        team="engineering",
        skills=["python", "api", "testing"],
    )
    
    agent = AutonomousAgent(identity)
    agent.run()


if __name__ == "__main__":
    main()