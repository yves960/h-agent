#!/usr/bin/env python3
"""
s07_task_system.py - File-Based Task System

Break big goals into small tasks, order them, persist to disk.

Tasks are stored in a JSON file with:
- Dependencies between tasks
- Status tracking
- Priority ordering

This enables:
- Persistence across sessions
- Dependency resolution
- Progress tracking
"""

import os
import json
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

WORK_DIR = os.getcwd()
TASKS_FILE = Path(WORK_DIR) / ".agent_tasks.json"


# ============================================================
# Task System
# ============================================================

class TaskStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"  # dependencies met
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass
class Task:
    id: str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 1  # 1-5, 5 highest
    dependencies: List[str] = None  # task IDs
    assignee: str = ""  # agent ID
    created_at: str = ""
    updated_at: str = ""
    result: str = ""
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d
    
    @classmethod
    def from_dict(cls, d: dict) -> "Task":
        d["status"] = TaskStatus(d.get("status", "pending"))
        return cls(**d)


class TaskManager:
    """File-based task management with dependency resolution."""
    
    def __init__(self, tasks_file = TASKS_FILE):
        self.tasks_file = Path(tasks_file) if not isinstance(tasks_file, Path) else tasks_file
        self.tasks: Dict[str, Task] = {}
        self._counter = 0
        self._load()
    
    def _load(self):
        """Load tasks from file."""
        if self.tasks_file.exists():
            try:
                data = json.loads(self.tasks_file.read_text())
                for tid, tdata in data.get("tasks", {}).items():
                    self.tasks[tid] = Task.from_dict(tdata)
                self._counter = data.get("counter", 0)
            except (json.JSONDecodeError, KeyError):
                pass  # Start fresh if file is corrupted
    
    def _save(self):
        """Save tasks to file."""
        data = {
            "tasks": {tid: t.to_dict() for tid, t in self.tasks.items()},
            "counter": self._counter,
            "updated_at": datetime.now().isoformat(),
        }
        self.tasks_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    
    def _next_id(self) -> str:
        self._counter += 1
        return f"task-{self._counter:03d}"
    
    def create(self, title: str, description: str = "", 
               priority: int = 1, dependencies: List[str] = None) -> Task:
        """Create a new task."""
        task = Task(
            id=self._next_id(),
            title=title,
            description=description,
            priority=priority,
            dependencies=dependencies or [],
        )
        self.tasks[task.id] = task
        self._save()
        return task
    
    def get(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self.tasks.get(task_id)
    
    def update(self, task_id: str, **kwargs) -> Optional[Task]:
        """Update a task."""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        for key, value in kwargs.items():
            if hasattr(task, key):
                if key == "status" and isinstance(value, str):
                    value = TaskStatus(value)
                setattr(task, key, value)
        
        task.updated_at = datetime.now().isoformat()
        self._save()
        return task
    
    def delete(self, task_id: str) -> bool:
        """Delete a task."""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self._save()
            return True
        return False
    
    def list(self, status: TaskStatus = None) -> List[Task]:
        """List tasks, optionally filtered by status."""
        tasks = list(self.tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return sorted(tasks, key=lambda t: (-t.priority, t.id))
    
    def get_ready_tasks(self) -> List[Task]:
        """Get tasks that are ready to execute (dependencies met)."""
        ready = []
        for task in self.tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            
            # Check dependencies
            deps_met = all(
                self.tasks.get(dep_id, Task(id="", title="")).status == TaskStatus.COMPLETED
                for dep_id in task.dependencies
            )
            
            if deps_met:
                task.status = TaskStatus.READY
                ready.append(task)
        
        self._save()
        return sorted(ready, key=lambda t: -t.priority)
    
    def get_next_task(self) -> Optional[Task]:
        """Get the next task to work on."""
        ready = self.get_ready_tasks()
        return ready[0] if ready else None
    
    def start_task(self, task_id: str) -> Optional[Task]:
        """Mark a task as in progress."""
        return self.update(task_id, status=TaskStatus.IN_PROGRESS)
    
    def complete_task(self, task_id: str, result: str = "") -> Optional[Task]:
        """Mark a task as completed."""
        return self.update(task_id, status=TaskStatus.COMPLETED, result=result)
    
    def fail_task(self, task_id: str, error: str = "") -> Optional[Task]:
        """Mark a task as failed."""
        return self.update(task_id, status=TaskStatus.FAILED, result=error)
    
    def get_graph(self) -> Dict[str, Any]:
        """Get task dependency graph."""
        nodes = []
        edges = []
        
        for task in self.tasks.values():
            nodes.append({
                "id": task.id,
                "title": task.title,
                "status": task.status.value,
            })
            for dep in task.dependencies:
                edges.append({"from": dep, "to": task.id})
        
        return {"nodes": nodes, "edges": edges}


# Global task manager
task_manager = TaskManager()


# ============================================================
# Tools
# ============================================================

import subprocess
import glob as glob_module

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
        if not os.path.exists(path):
            return f"Error: Not found: {path}"
        return Path(path).read_text()[:10000]
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

def tool_task_create(title: str, description: str = "", priority: int = 1, dependencies: List[str] = None) -> str:
    task = task_manager.create(title, description, priority, dependencies)
    return json.dumps({"created": task.to_dict()})

def tool_task_list(status: str = None) -> str:
    st = TaskStatus(status) if status else None
    tasks = [t.to_dict() for t in task_manager.list(st)]
    return json.dumps({"tasks": tasks}, ensure_ascii=False, indent=2)

def tool_task_get(task_id: str) -> str:
    task = task_manager.get(task_id)
    if not task:
        return json.dumps({"error": "Task not found"})
    return json.dumps(task.to_dict(), ensure_ascii=False, indent=2)

def tool_task_update(task_id: str, status: str = None, result: str = None) -> str:
    kwargs = {}
    if status:
        kwargs["status"] = status
    if result:
        kwargs["result"] = result
    task = task_manager.update(task_id, **kwargs)
    if not task:
        return json.dumps({"error": "Task not found"})
    return json.dumps({"updated": task.to_dict()})

def tool_task_next() -> str:
    task = task_manager.get_next_task()
    if not task:
        return json.dumps({"message": "No ready tasks"})
    return json.dumps({"next_task": task.to_dict()})

def tool_task_graph() -> str:
    return json.dumps(task_manager.get_graph(), ensure_ascii=False, indent=2)


TOOLS = [
    {"type": "function", "function": {"name": "bash", "description": "Run shell command",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "read", "description": "Read file",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "write", "description": "Write file",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    # Task tools
    {"type": "function", "function": {"name": "task_create", "description": "Create a new task",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string"}, "description": {"type": "string"},
            "priority": {"type": "integer"}, "dependencies": {"type": "array", "items": {"type": "string"}}},
            "required": ["title"]}}},
    {"type": "function", "function": {"name": "task_list", "description": "List tasks",
        "parameters": {"type": "object", "properties": {"status": {"type": "string", "enum": ["pending", "ready", "in_progress", "completed", "blocked", "failed"]}}}}},
    {"type": "function", "function": {"name": "task_get", "description": "Get task details",
        "parameters": {"type": "object", "properties": {"task_id": {"type": "string"}}, "required": ["task_id"]}}},
    {"type": "function", "function": {"name": "task_update", "description": "Update task status",
        "parameters": {"type": "object", "properties": {
            "task_id": {"type": "string"}, "status": {"type": "string"}, "result": {"type": "string"}},
            "required": ["task_id"]}}},
    {"type": "function", "function": {"name": "task_next", "description": "Get next task to work on"}},
    {"type": "function", "function": {"name": "task_graph", "description": "Get task dependency graph"}},
]

TOOL_HANDLERS = {
    "bash": tool_bash, "read": tool_read, "write": tool_write,
    "task_create": tool_task_create, "task_list": tool_task_list, "task_get": tool_task_get,
    "task_update": tool_task_update, "task_next": tool_task_next, "task_graph": tool_task_graph,
}


def execute_tool_call(tool_call) -> str:
    args = json.loads(tool_call.function.arguments)
    return TOOL_HANDLERS[tool_call.function.name](**args)


# ============================================================
# Agent Loop
# ============================================================

def get_system_prompt() -> str:
    ready = len(task_manager.get_ready_tasks())
    pending = len([t for t in task_manager.tasks.values() if t.status == TaskStatus.PENDING])
    in_progress = len([t for t in task_manager.tasks.values() if t.status == TaskStatus.IN_PROGRESS])
    
    return f"""You are a task-driven agent at {WORK_DIR}.

Current Tasks:
  - Ready: {ready}
  - Pending: {pending}  
  - In Progress: {in_progress}

Use task tools to manage work. Use 'task_next' to get the next task to work on.
Complete tasks using 'task_update' with status='completed'.

Act efficiently."""


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
            
            if name.startswith("task_"):
                print(f"\033[32m📋 {name}: {args}\033[0m")
            else:
                print(f"\033[33m$ {name}\033[0m")
            
            result = execute_tool_call(tool_call)
            print(result[:150] + ("..." if len(result) > 150 else ""))
            
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})


def main():
    print(f"\033[36mOpenAI Agent Harness - s07 (Task System)\033[0m")
    print(f"Model: {MODEL}")
    print(f"Tasks file: {TASKS_FILE}")
    print(f"\nTask tools: create, list, get, update, next, graph")
    print("\nType 'q' to quit, 'tasks' to list tasks\n")
    
    history = []
    while True:
        try:
            query = input("\033[36m>> \033[0m")
        except (EOFError, KeyboardInterrupt):
            break
        
        if query.strip().lower() == "q":
            break
        if query.strip().lower() == "tasks":
            print(task_manager.list())
            continue
        
        history.append({"role": "user", "content": query})
        agent_loop(history)
        
        if history[-1].get("content"):
            print(f"\n{history[-1]['content']}\n")


if __name__ == "__main__":
    main()