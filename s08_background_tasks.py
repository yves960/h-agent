#!/usr/bin/env python3
"""
s08_background_tasks.py - Background Task Execution

Run slow operations in the background; the agent keeps thinking.

Features:
- Spawn background tasks (long-running commands)
- Continue working while tasks run
- Get notified when tasks complete
- Check task status

Uses threading for background execution.
"""

import os
import json
import subprocess
import threading
import queue
import uuid
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

load_dotenv(override=True)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "sk-dummy"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
)
MODEL = os.getenv("MODEL_ID", "gpt-4o")

WORK_DIR = os.getcwd()


# ============================================================
# Background Task System
# ============================================================

class BGTaskStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BackgroundTask:
    id: str
    command: str
    status: BGTaskStatus = BGTaskStatus.RUNNING
    started_at: str = ""
    completed_at: str = ""
    output: str = ""
    error: str = ""
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d


class BackgroundTaskManager:
    """Manages background task execution."""
    
    def __init__(self):
        self.tasks: Dict[str, BackgroundTask] = {}
        self.notification_queue: queue.Queue = queue.Queue()
        self._lock = threading.Lock()
    
    def spawn(self, command: str, task_id: str = None) -> BackgroundTask:
        """Spawn a background task."""
        task_id = task_id or f"bg-{uuid.uuid4().hex[:8]}"
        
        task = BackgroundTask(
            id=task_id,
            command=command,
            status=BGTaskStatus.RUNNING,
            started_at=datetime.now().isoformat(),
        )
        
        with self._lock:
            self.tasks[task_id] = task
        
        # Start background thread
        thread = threading.Thread(
            target=self._run_task,
            args=(task_id, command),
            daemon=True,
        )
        thread.start()
        
        return task
    
    def _run_task(self, task_id: str, command: str):
        """Execute task in background thread."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=WORK_DIR,
                capture_output=True,
                text=True,
                timeout=300,  # 5 min timeout
            )
            
            with self._lock:
                task = self.tasks.get(task_id)
                if task:
                    task.status = BGTaskStatus.COMPLETED
                    task.completed_at = datetime.now().isoformat()
                    task.output = result.stdout[:50000]
                    task.error = result.stderr[:10000]
            
            # Queue notification
            self.notification_queue.put({
                "type": "task_completed",
                "task_id": task_id,
                "success": result.returncode == 0,
            })
            
        except subprocess.TimeoutExpired:
            with self._lock:
                task = self.tasks.get(task_id)
                if task:
                    task.status = BGTaskStatus.FAILED
                    task.error = "Timeout (300s)"
            
            self.notification_queue.put({
                "type": "task_failed",
                "task_id": task_id,
                "error": "timeout",
            })
            
        except Exception as e:
            with self._lock:
                task = self.tasks.get(task_id)
                if task:
                    task.status = BGTaskStatus.FAILED
                    task.error = str(e)
            
            self.notification_queue.put({
                "type": "task_failed",
                "task_id": task_id,
                "error": str(e),
            })
    
    def get(self, task_id: str) -> Optional[BackgroundTask]:
        """Get task status."""
        with self._lock:
            return self.tasks.get(task_id)
    
    def list(self) -> list:
        """List all background tasks."""
        with self._lock:
            return [t.to_dict() for t in self.tasks.values()]
    
    def get_notifications(self) -> list:
        """Get pending notifications (non-blocking)."""
        notifications = []
        try:
            while True:
                notifications.append(self.notification_queue.get_nowait())
        except queue.Empty:
            pass
        return notifications
    
    def has_notifications(self) -> bool:
        """Check if there are pending notifications."""
        return not self.notification_queue.empty()


# Global manager
bg_manager = BackgroundTaskManager()


# ============================================================
# Tools
# ============================================================

def tool_bash(command: str) -> str:
    """Synchronous bash (for quick commands)."""
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
            return f"Error: Not found"
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

def tool_bg_spawn(command: str, task_id: str = None) -> str:
    """Spawn a background task."""
    task = bg_manager.spawn(command, task_id)
    return json.dumps({
        "spawned": task.id,
        "status": task.status.value,
        "message": f"Background task {task.id} started. Use bg_status to check progress."
    })

def tool_bg_status(task_id: str) -> str:
    """Get background task status."""
    task = bg_manager.get(task_id)
    if not task:
        return json.dumps({"error": "Task not found"})
    return json.dumps(task.to_dict(), indent=2)

def tool_bg_list() -> str:
    """List all background tasks."""
    return json.dumps({"tasks": bg_manager.list()}, indent=2)

def tool_bg_notifications() -> str:
    """Get pending notifications from completed background tasks."""
    notifications = bg_manager.get_notifications()
    if not notifications:
        return json.dumps({"notifications": []})
    return json.dumps({"notifications": notifications}, indent=2)


TOOLS = [
    {"type": "function", "function": {"name": "bash", "description": "Run quick shell command (<60s)",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "read", "description": "Read file",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "write", "description": "Write file",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    # Background task tools
    {"type": "function", "function": {"name": "bg_spawn", "description": "Spawn a background task for long-running commands",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}, "task_id": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "bg_status", "description": "Check background task status",
        "parameters": {"type": "object", "properties": {"task_id": {"type": "string"}}, "required": ["task_id"]}}},
    {"type": "function", "function": {"name": "bg_list", "description": "List all background tasks",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "bg_notifications", "description": "Get notifications from completed background tasks",
        "parameters": {"type": "object", "properties": {}}}},
]

TOOL_HANDLERS = {
    "bash": tool_bash, "read": tool_read, "write": tool_write,
    "bg_spawn": tool_bg_spawn, "bg_status": tool_bg_status, "bg_list": tool_bg_list, "bg_notifications": tool_bg_notifications,
}


def execute_tool_call(tool_call) -> str:
    args = json.loads(tool_call.function.arguments)
    return TOOL_HANDLERS[tool_call.function.name](**args)


# ============================================================
# Agent Loop
# ============================================================

def get_system_prompt() -> str:
    running = len([t for t in bg_manager.tasks.values() if t.status == BGTaskStatus.RUNNING])
    
    prompt = f"""You are an agent at {WORK_DIR}.

Background tasks: {running} running

Use bg_spawn for long-running commands (tests, builds, etc.).
Use bg_notifications to check for completed tasks.
Continue working while background tasks run.

Act efficiently."""
    
    # Check for pending notifications
    if bg_manager.has_notifications():
        notifications = bg_manager.get_notifications()
        prompt += f"\n\n🔔 Pending Notifications:\n{json.dumps(notifications, indent=2)}"
    
    return prompt


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
            
            if name.startswith("bg_"):
                print(f"\033[35m⏱️ {name}: {args}\033[0m")
            else:
                print(f"\033[33m$ {name}\033[0m")
            
            result = execute_tool_call(tool_call)
            print(result[:150] + ("..." if len(result) > 150 else ""))
            
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})


def main():
    print(f"\033[36mOpenAI Agent Harness - s08 (Background Tasks)\033[0m")
    print(f"Model: {MODEL}")
    print(f"\nBackground tools: bg_spawn, bg_status, bg_list, bg_notifications")
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