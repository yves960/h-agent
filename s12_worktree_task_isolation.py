#!/usr/bin/env python3
"""
s12_worktree_task_isolation.py - Worktree + Task Isolation (OpenAI Version)

Directory-level isolation for parallel task execution.
Tasks are the control plane and worktrees are the execution plane.

Key insight: "Isolate by directory, coordinate by task ID."

Structure:
    .tasks/task_001.json      # Task metadata
    .worktrees/index.json     # Worktree registry
    .worktrees/auth-refactor/ # Isolated working directory
"""

import os
import json
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from enum import Enum

load_dotenv(override=True)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "sk-dummy"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
)
MODEL = os.getenv("MODEL_ID", "gpt-4o")

WORK_DIR = Path.cwd()
TASKS_DIR = WORK_DIR / ".tasks"
WORKTREES_DIR = WORK_DIR / ".worktrees"

TASKS_DIR.mkdir(exist_ok=True)
WORKTREES_DIR.mkdir(exist_ok=True)


# ============================================================
# Task System
# ============================================================

class TaskStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    id: str
    subject: str
    description: str = ""
    status: TaskStatus = TaskStatus.OPEN
    worktree: Optional[str] = None  # Worktree name if allocated
    priority: int = 1
    created_at: str = ""
    updated_at: str = ""
    result: str = ""
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d
    
    @classmethod
    def from_dict(cls, d: dict) -> "Task":
        d = d.copy()
        d["status"] = TaskStatus(d.get("status", "open"))
        return cls(**d)


# ============================================================
# Worktree Management
# ============================================================

@dataclass
class Worktree:
    name: str
    path: str
    branch: Optional[str] = None
    task_id: Optional[str] = None
    status: str = "active"
    created_at: str = ""
    
    def to_dict(self) -> dict:
        return asdict(self)


class WorktreeManager:
    """Manages isolated working directories for tasks."""
    
    def __init__(self, worktrees_dir: Path = WORKTREES_DIR):
        self.worktrees_dir = worktrees_dir
        self.index_file = worktrees_dir / "index.json"
        self.worktrees: Dict[str, Worktree] = {}
        self._load_index()
    
    def _load_index(self):
        """Load worktree index."""
        if self.index_file.exists():
            data = json.loads(self.index_file.read_text())
            for wt in data.get("worktrees", []):
                self.worktrees[wt["name"]] = Worktree(**wt)
    
    def _save_index(self):
        """Save worktree index."""
        data = {
            "worktrees": [wt.to_dict() for wt in self.worktrees.values()],
            "updated_at": datetime.now().isoformat(),
        }
        self.index_file.write_text(json.dumps(data, indent=2))
    
    def create(self, name: str, task_id: str = None) -> Worktree:
        """Create a new worktree (isolated directory)."""
        worktree_path = self.worktrees_dir / name
        
        # Create directory
        worktree_path.mkdir(parents=True, exist_ok=True)
        
        # Try to create git worktree if in a repo
        branch = None
        try:
            # Check if we're in a git repo
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=WORK_DIR,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                # Create a new branch and worktree
                branch = f"wt/{name}"
                subprocess.run(
                    ["git", "worktree", "add", "-b", branch, str(worktree_path)],
                    cwd=WORK_DIR,
                    capture_output=True,
                    timeout=30,
                )
        except:
            pass  # Not a git repo or git not available
        
        worktree = Worktree(
            name=name,
            path=str(worktree_path),
            branch=branch,
            task_id=task_id,
            created_at=datetime.now().isoformat(),
        )
        
        self.worktrees[name] = worktree
        self._save_index()
        
        return worktree
    
    def get(self, name: str) -> Optional[Worktree]:
        """Get worktree by name."""
        return self.worktrees.get(name)
    
    def get_for_task(self, task_id: str) -> Optional[Worktree]:
        """Get worktree assigned to a task."""
        for wt in self.worktrees.values():
            if wt.task_id == task_id:
                return wt
        return None
    
    def list(self) -> List[Worktree]:
        """List all worktrees."""
        return list(self.worktrees.values())
    
    def remove(self, name: str, keep_branch: bool = False) -> bool:
        """Remove a worktree."""
        if name not in self.worktrees:
            return False
        
        worktree = self.worktrees[name]
        worktree_path = Path(worktree.path)
        
        # Try to remove git worktree
        if worktree.branch:
            try:
                subprocess.run(
                    ["git", "worktree", "remove", str(worktree_path), "--force"],
                    cwd=WORK_DIR,
                    capture_output=True,
                    timeout=30,
                )
                if not keep_branch:
                    subprocess.run(
                        ["git", "branch", "-D", worktree.branch],
                        cwd=WORK_DIR,
                        capture_output=True,
                        timeout=10,
                    )
            except:
                pass
        
        # Remove directory if still exists
        if worktree_path.exists():
            shutil.rmtree(worktree_path)
        
        del self.worktrees[name]
        self._save_index()
        
        return True


# Global managers
worktree_manager = WorktreeManager()


class TaskManager:
    """Manages tasks with worktree allocation."""
    
    def __init__(self, tasks_dir: Path = TASKS_DIR):
        self.tasks_dir = tasks_dir
        self._counter = 0
    
    def _next_id(self) -> str:
        self._counter += 1
        return f"task-{self._counter:03d}"
    
    def create(self, subject: str, description: str = "", priority: int = 1) -> Task:
        """Create a new task."""
        task = Task(
            id=self._next_id(),
            subject=subject,
            description=description,
            priority=priority,
            created_at=datetime.now().isoformat(),
        )
        self._save(task)
        return task
    
    def _save(self, task: Task):
        """Save task to file."""
        task_file = self.tasks_dir / f"{task.id}.json"
        task_file.write_text(json.dumps(task.to_dict(), indent=2))
    
    def _load(self, task_id: str) -> Optional[Task]:
        """Load task from file."""
        task_file = self.tasks_dir / f"{task_id}.json"
        if not task_file.exists():
            return None
        return Task.from_dict(json.loads(task_file.read_text()))
    
    def allocate_worktree(self, task_id: str) -> Optional[Worktree]:
        """Allocate a worktree for a task."""
        task = self._load(task_id)
        if not task:
            return None
        
        # Create worktree name from task
        wt_name = f"wt-{task_id}"
        
        worktree = worktree_manager.create(wt_name, task_id)
        
        # Update task
        task.worktree = wt_name
        task.status = TaskStatus.IN_PROGRESS
        task.updated_at = datetime.now().isoformat()
        self._save(task)
        
        return worktree
    
    def complete(self, task_id: str, result: str = "") -> Optional[Task]:
        """Mark task as completed."""
        task = self._load(task_id)
        if not task:
            return None
        
        task.status = TaskStatus.COMPLETED
        task.result = result
        task.updated_at = datetime.now().isoformat()
        self._save(task)
        
        return task
    
    def list(self, status: TaskStatus = None) -> List[Task]:
        """List tasks, optionally filtered by status."""
        tasks = []
        for task_file in self.tasks_dir.glob("task-*.json"):
            try:
                task = Task.from_dict(json.loads(task_file.read_text()))
                if status is None or task.status == status:
                    tasks.append(task)
            except:
                pass
        return sorted(tasks, key=lambda t: (-t.priority, t.id))


task_manager = TaskManager()


# ============================================================
# Tools
# ============================================================

def tool_bash(command: str, worktree: str = None) -> str:
    """Run a shell command, optionally in a worktree."""
    cwd = WORK_DIR
    if worktree:
        wt = worktree_manager.get(worktree)
        if wt:
            cwd = Path(wt.path)
    
    try:
        r = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True, timeout=120)
        return (r.stdout + r.stderr)[:20000] or "(no output)"
    except Exception as e:
        return f"Error: {e}"


def tool_task_create(subject: str, description: str = "", priority: int = 1) -> str:
    """Create a new task."""
    task = task_manager.create(subject, description, priority)
    return json.dumps({"created": task.to_dict()})


def tool_task_allocate(task_id: str) -> str:
    """Allocate a worktree for a task."""
    worktree = task_manager.allocate_worktree(task_id)
    if not worktree:
        return json.dumps({"error": "Failed to allocate worktree"})
    return json.dumps({
        "allocated": {
            "task_id": task_id,
            "worktree": worktree.name,
            "path": worktree.path,
        }
    })


def tool_task_complete(task_id: str, result: str = "") -> str:
    """Complete a task."""
    task = task_manager.complete(task_id, result)
    if not task:
        return json.dumps({"error": "Task not found"})
    return json.dumps({"completed": task.to_dict()})


def tool_task_list(status: str = None) -> str:
    """List tasks."""
    st = TaskStatus(status) if status else None
    tasks = [t.to_dict() for t in task_manager.list(st)]
    return json.dumps({"tasks": tasks})


def tool_worktree_create(name: str, task_id: str = None) -> str:
    """Create a new worktree."""
    worktree = worktree_manager.create(name, task_id)
    return json.dumps({"created": worktree.to_dict()})


def tool_worktree_remove(name: str, keep_branch: bool = False) -> str:
    """Remove a worktree."""
    success = worktree_manager.remove(name, keep_branch)
    return json.dumps({"removed": success})


def tool_worktree_list() -> str:
    """List worktrees."""
    worktrees = [wt.to_dict() for wt in worktree_manager.list()]
    return json.dumps({"worktrees": worktrees})


TOOLS = [
    {"type": "function", "function": {"name": "bash", "description": "Run a shell command",
        "parameters": {"type": "object", "properties": {
            "command": {"type": "string"},
            "worktree": {"type": "string", "description": "Worktree name to run in"},
        }, "required": ["command"]}}},
    {"type": "function", "function": {"name": "task_create", "description": "Create a new task",
        "parameters": {"type": "object", "properties": {
            "subject": {"type": "string"},
            "description": {"type": "string"},
            "priority": {"type": "integer"},
        }, "required": ["subject"]}}},
    {"type": "function", "function": {"name": "task_allocate", "description": "Allocate a worktree for a task",
        "parameters": {"type": "object", "properties": {
            "task_id": {"type": "string"},
        }, "required": ["task_id"]}}},
    {"type": "function", "function": {"name": "task_complete", "description": "Complete a task",
        "parameters": {"type": "object", "properties": {
            "task_id": {"type": "string"},
            "result": {"type": "string"},
        }, "required": ["task_id"]}}},
    {"type": "function", "function": {"name": "task_list", "description": "List tasks",
        "parameters": {"type": "object", "properties": {
            "status": {"type": "string", "enum": ["open", "in_progress", "completed", "failed", "cancelled"]},
        }}}},
    {"type": "function", "function": {"name": "worktree_create", "description": "Create a worktree",
        "parameters": {"type": "object", "properties": {
            "name": {"type": "string"},
            "task_id": {"type": "string"},
        }, "required": ["name"]}}},
    {"type": "function", "function": {"name": "worktree_remove", "description": "Remove a worktree",
        "parameters": {"type": "object", "properties": {
            "name": {"type": "string"},
            "keep_branch": {"type": "boolean"},
        }, "required": ["name"]}}},
    {"type": "function", "function": {"name": "worktree_list", "description": "List worktrees"}},
]

TOOL_HANDLERS = {
    "bash": lambda **kw: tool_bash(kw["command"], kw.get("worktree")),
    "task_create": tool_task_create,
    "task_allocate": tool_task_allocate,
    "task_complete": tool_task_complete,
    "task_list": lambda **kw: tool_task_list(kw.get("status")),
    "worktree_create": tool_worktree_create,
    "worktree_remove": tool_worktree_remove,
    "worktree_list": tool_worktree_list,
}


def execute_tool_call(tool_call) -> str:
    args = json.loads(tool_call.function.arguments)
    handler = TOOL_HANDLERS[tool_call.function.name]
    return handler(**args)


# ============================================================
# Agent Loop
# ============================================================

def get_system_prompt() -> str:
    return f"""You are a coding agent at {WORK_DIR}.

Use task + worktree tools for multi-task work:
- Create tasks for work items
- Allocate worktrees for isolation (each task gets its own directory)
- Run commands in specific worktrees
- Complete tasks when done

For parallel or risky changes:
1. Create a task
2. Allocate a worktree (creates isolated directory)
3. Run commands in that worktree
4. Complete task when done

Worktrees provide directory-level isolation - each task can work in its own space."""


def agent_loop(messages: list):
    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": get_system_prompt()}] + messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=4000,
        )
        
        message = response.choices[0].message
        messages.append({"role": "assistant", "content": message.content, "tool_calls": message.tool_calls})
        
        if not message.tool_calls:
            return
        
        for tool_call in message.tool_calls:
            args = json.loads(tool_call.function.arguments)
            name = tool_call.function.name
            
            if name.startswith("task_") or name.startswith("worktree_"):
                print(f"\033[34m📁 {name}: {args}\033[0m")
            else:
                wt = args.get("worktree", "")
                print(f"\033[33m$ bash ({wt or 'main'})\033[0m")
            
            result = execute_tool_call(tool_call)
            print(result[:150] + ("..." if len(result) > 150 else ""))
            
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})


def main():
    print(f"\033[36mOpenAI Agent Harness - s12 (Worktree Task Isolation)\033[0m")
    print(f"Model: {MODEL}")
    print(f"Tasks dir: {TASKS_DIR}")
    print(f"Worktrees dir: {WORKTREES_DIR}")
    print("\nFeatures:")
    print("  - Tasks: Create, allocate, complete")
    print("  - Worktrees: Isolated directories for parallel work")
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