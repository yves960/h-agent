#!/usr/bin/env python3
"""
h_agent/features/tasks.py - Task Management System

Persistent task storage in ~/.h-agent/tasks/
"""

import json
import uuid
import time
from pathlib import Path
from typing import Optional, Dict, List, Any


class TaskManager:
    """Manages persistent tasks stored as JSON files."""

    def __init__(self, tasks_dir: Path = None):
        if tasks_dir is None:
            tasks_dir = Path.home() / ".h-agent" / "tasks"
        self.tasks_dir = tasks_dir
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

    def _task_path(self, task_id: str) -> Path:
        return self.tasks_dir / f"{task_id}.json"

    def create(self, title: str, description: str = "", priority: str = "medium") -> str:
        """Create a new task, return task_id."""
        task_id = uuid.uuid4().hex[:8]
        task = {
            "id": task_id,
            "title": title,
            "description": description,
            "priority": priority,
            "status": "pending",
            "owner": None,
            "created_at": time.time(),
            "updated_at": time.time(),
        }
        self._task_path(task_id).write_text(
            json.dumps(task, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return task_id

    def get(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task details by ID, or None if not found."""
        path = self._task_path(task_id)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def update(self, task_id: str, status: str = None, owner: str = None) -> bool:
        """Update task status or owner. Returns True if task exists and was updated."""
        task = self.get(task_id)
        if task is None:
            return False
        if status is not None:
            task["status"] = status
        if owner is not None:
            task["owner"] = owner
        task["updated_at"] = time.time()
        self._task_path(task_id).write_text(
            json.dumps(task, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return True

    def list_all(self) -> List[Dict[str, Any]]:
        """List all tasks."""
        tasks = []
        for path in self.tasks_dir.glob("*.json"):
            try:
                task = json.loads(path.read_text(encoding="utf-8"))
                tasks.append(task)
            except (json.JSONDecodeError, OSError):
                continue
        return sorted(tasks, key=lambda t: t.get("created_at", 0), reverse=True)

    def delete(self, task_id: str) -> bool:
        """Delete a task by ID. Returns True if deleted."""
        path = self._task_path(task_id)
        if not path.exists():
            return False
        path.unlink()
        return True


# ============================================================
# Background Task Runner
# ============================================================

import subprocess
import threading
from dataclasses import dataclass, field
from typing import Callable, Optional, Dict, Any
from enum import Enum


class BackgroundStatus(Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BackgroundTask:
    task_id: str
    command: str
    status: BackgroundStatus = BackgroundStatus.RUNNING
    output: str = ""
    return_code: Optional[int] = None
    started_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None


class BackgroundRunner:
    """Runs commands in background threads."""

    def __init__(self):
        self._tasks: Dict[str, BackgroundTask] = {}
        self._lock = threading.Lock()

    def run(self, command: str) -> str:
        """Run command in daemon thread, return task_id."""
        task_id = uuid.uuid4().hex[:8]
        task = BackgroundTask(task_id=task_id, command=command)
        with self._lock:
            self._tasks[task_id] = task

        thread = threading.Thread(target=self._execute, args=(task_id, command), daemon=True)
        thread.start()
        return task_id

    def _execute(self, task_id: str, command: str):
        """Execute command and store result."""
        task = self._tasks.get(task_id)
        if task is None:
            return

        try:
            r = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 min timeout
            )
            task.output = (r.stdout + r.stderr).strip()
            task.return_code = r.returncode
            task.status = BackgroundStatus.COMPLETED if r.returncode == 0 else BackgroundStatus.FAILED
        except subprocess.TimeoutExpired:
            task.output = "Error: Command timed out after 300 seconds"
            task.status = BackgroundStatus.FAILED
            task.return_code = -1
        except Exception as e:
            task.output = f"Error: {e}"
            task.status = BackgroundStatus.FAILED
            task.return_code = -1
        finally:
            task.finished_at = time.time()

    def check(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Check task status. Returns dict with status/output or None if not found."""
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            return {
                "task_id": task.task_id,
                "command": task.command,
                "status": task.status.value,
                "output": task.output,
                "return_code": task.return_code,
                "running": task.status == BackgroundStatus.RUNNING,
            }


# Singleton instances
task_manager = TaskManager()
background_runner = BackgroundRunner()
