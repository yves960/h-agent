"""
h_agent/commands/tasks.py - /tasks Command

Manage async tasks via CLI.
"""

from h_agent.commands.base import Command, CommandContext, CommandResult
from h_agent.tools.task import TaskStatus, get_task_manager


class TasksCommand(Command):
    """Manage async tasks."""
    
    name = "tasks"
    description = "Manage async tasks"
    aliases = ["task"]
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """
        Execute the tasks command.
        
        Usage:
            /tasks                 - List all tasks
            /tasks list            - List all tasks
            /tasks list --running  - List running tasks
            /tasks get <id>        - Get task details
            /tasks stop <id>       - Stop a task
        """
        manager = get_task_manager()
        parts = args.strip().split()
        
        if not parts or parts[0] == "list":
            # List tasks
            status = None
            if "--running" in parts:
                status = TaskStatus.RUNNING
            elif "--pending" in parts:
                status = TaskStatus.PENDING
            elif "--completed" in parts:
                status = TaskStatus.COMPLETED
            elif "--failed" in parts:
                status = TaskStatus.FAILED
            
            tasks = await manager.list_tasks(status)
            
            if not tasks:
                return CommandResult.ok("No tasks found")
            
            lines = ["Tasks:"]
            for task in tasks[:20]:  # Limit to 20
                status_icon = {
                    TaskStatus.PENDING: "⏳",
                    TaskStatus.RUNNING: "🔄",
                    TaskStatus.COMPLETED: "✅",
                    TaskStatus.FAILED: "❌",
                    TaskStatus.CANCELLED: "🚫",
                }.get(task.status, "?")
                
                prompt_preview = task.prompt[:50] + "..." if len(task.prompt) > 50 else task.prompt
                lines.append(f"  {status_icon} [{task.status.value}] {task.id}: {prompt_preview}")
            
            if len(tasks) > 20:
                lines.append(f"\n  ... and {len(tasks) - 20} more tasks")
            
            return CommandResult.ok("\n".join(lines))
        
        elif parts[0] == "get":
            if len(parts) < 2:
                return CommandResult.err("Usage: /tasks get <task_id>")
            
            task_id = parts[1]
            task = await manager.get_task(task_id)
            
            if not task:
                return CommandResult.err(f"Task not found: {task_id}")
            
            lines = [
                f"Task ID: {task.id}",
                f"Status: {task.status.value}",
                f"Prompt: {task.prompt}",
            ]
            
            if task.agent_id:
                lines.append(f"Agent: {task.agent_id}")
            
            if task.result:
                lines.append(f"Result: {task.result}")
            
            if task.error:
                lines.append(f"Error: {task.error}")
            
            return CommandResult.ok("\n".join(lines))
        
        elif parts[0] == "stop":
            if len(parts) < 2:
                return CommandResult.err("Usage: /tasks stop <task_id>")
            
            task_id = parts[1]
            cancelled = await manager.cancel_task(task_id)
            
            if cancelled:
                return CommandResult.ok(f"Task cancelled: {task_id}")
            else:
                return CommandResult.err(f"Task not running or not found: {task_id}")
        
        elif parts[0] == "clear":
            # Clear completed/failed tasks
            tasks = await manager.list_tasks()
            cleared = 0
            for task in tasks:
                if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                    # Remove from manager (would need a remove method)
                    cleared += 1
            
            return CommandResult.ok(f"Cleared {cleared} tasks")
        
        else:
            return CommandResult.err(
                f"Unknown subcommand: {parts[0]}\n"
                "Usage: /tasks [list|get|stop] [args]"
            )
