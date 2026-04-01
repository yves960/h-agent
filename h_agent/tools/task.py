"""
h_agent/tools/task.py - Task Management Tools

Provides tools for creating, managing, and monitoring async tasks.
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable, Any

from h_agent.tools.base import Tool, ToolResult


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Represents an async task."""
    id: str
    prompt: str
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    agent_id: Optional[str] = None
    created_at: float = field(default_factory=lambda: __import__('time').time())
    completed_at: Optional[float] = None


class TaskManager:
    """Central task manager for tracking async tasks."""
    
    def __init__(self):
        self._tasks: Dict[str, Task] = {}
        self._lock = asyncio.Lock()
        self._running_tasks: Dict[str, asyncio.Task] = {}
    
    async def create_task(
        self,
        prompt: str,
        agent_id: Optional[str] = None,
        coro: Optional[Callable] = None,
    ) -> Task:
        """Create a new task."""
        async with self._lock:
            task_id = str(uuid.uuid4())[:8]
            task = Task(
                id=task_id,
                prompt=prompt,
                agent_id=agent_id,
            )
            self._tasks[task_id] = task
            
            if coro:
                async_task = asyncio.create_task(self._run_task(task_id, coro))
                self._running_tasks[task_id] = async_task
            
            return task
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self._tasks.get(task_id)
    
    async def list_tasks(self, status: Optional[TaskStatus] = None) -> List[Task]:
        """List all tasks, optionally filtered by status."""
        async with self._lock:
            tasks = list(self._tasks.values())
            if status:
                tasks = [t for t in tasks if t.status == status]
            return sorted(tasks, key=lambda t: t.created_at, reverse=True)
    
    async def update_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        """Update task status."""
        async with self._lock:
            if task_id in self._tasks:
                task = self._tasks[task_id]
                task.status = status
                if result is not None:
                    task.result = result
                if error is not None:
                    task.error = error
                if status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                    task.completed_at = __import__('time').time()
                    self._running_tasks.pop(task_id, None)
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        async with self._lock:
            if task_id in self._running_tasks:
                self._running_tasks[task_id].cancel()
                await self.update_status(task_id, TaskStatus.CANCELLED)
                return True
            return False
    
    async def _run_task(self, task_id: str, coro: Callable) -> None:
        """Internal runner for a task coroutine."""
        await self.update_status(task_id, TaskStatus.RUNNING)
        try:
            result = await coro()
            await self.update_status(task_id, TaskStatus.COMPLETED, result=str(result))
        except asyncio.CancelledError:
            await self.update_status(task_id, TaskStatus.CANCELLED)
        except Exception as e:
            await self.update_status(task_id, TaskStatus.FAILED, error=str(e))


# Global task manager instance
_task_manager: Optional[TaskManager] = None


def get_task_manager() -> TaskManager:
    """Get the global task manager."""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager


def generate_id() -> str:
    """Generate a short unique ID."""
    return str(uuid.uuid4())[:8]


class TaskCreateTool(Tool):
    """Create a new async task."""
    
    name = "task_create"
    description = "Create a new async task"
    
    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Task prompt"},
                "agent_id": {"type": "string", "description": "Optional agent ID to use"},
            },
            "required": ["prompt"],
        }
    
    async def execute(
        self,
        args: dict,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> ToolResult:
        manager = get_task_manager()
        task = await manager.create_task(
            prompt=args["prompt"],
            agent_id=args.get("agent_id"),
        )
        return ToolResult.ok(f"Task created: {task.id}")


class TaskGetTool(Tool):
    """Get task status and result."""
    
    name = "task_get"
    description = "Get task status and result by ID"
    
    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID to query"},
            },
            "required": ["task_id"],
        }
    
    async def execute(
        self,
        args: dict,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> ToolResult:
        manager = get_task_manager()
        task = await manager.get_task(args["task_id"])
        
        if not task:
            return ToolResult.err(f"Task not found: {args['task_id']}")
        
        output_lines = [
            f"Task ID: {task.id}",
            f"Status: {task.status.value}",
            f"Prompt: {task.prompt}",
        ]
        
        if task.result:
            output_lines.append(f"Result: {task.result}")
        if task.error:
            output_lines.append(f"Error: {task.error}")
        if task.completed_at:
            output_lines.append(f"Completed at: {task.completed_at}")
        
        return ToolResult.ok("\n".join(output_lines))


class TaskListTool(Tool):
    """List all tasks."""
    
    name = "task_list"
    description = "List all tasks, optionally filtered by status"
    
    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["pending", "running", "completed", "failed", "cancelled"],
                    "description": "Optional status filter",
                },
                "limit": {"type": "integer", "description": "Maximum number of tasks to return", "default": 20},
            },
        }
    
    async def execute(
        self,
        args: dict,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> ToolResult:
        manager = get_task_manager()
        status = TaskStatus(args["status"]) if args.get("status") else None
        tasks = await manager.list_tasks(status)
        
        limit = args.get("limit", 20)
        tasks = tasks[:limit]
        
        if not tasks:
            return ToolResult.ok("No tasks found")
        
        lines = ["Tasks:"]
        for task in tasks:
            lines.append(f"  [{task.status.value}] {task.id} - {task.prompt[:50]}...")
        
        return ToolResult.ok("\n".join(lines))


class TaskStopTool(Tool):
    """Stop a running task."""
    
    name = "task_stop"
    description = "Stop a running task"
    
    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID to stop"},
            },
            "required": ["task_id"],
        }
    
    async def execute(
        self,
        args: dict,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> ToolResult:
        manager = get_task_manager()
        cancelled = await manager.cancel_task(args["task_id"])
        
        if cancelled:
            return ToolResult.ok(f"Task cancelled: {args['task_id']}")
        return ToolResult.err(f"Task not running or not found: {args['task_id']}")
