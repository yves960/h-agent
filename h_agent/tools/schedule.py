from .base import Tool, ToolResult


class ScheduleCronTool(Tool):
    name = "schedule_cron"
    description = "Schedule a task to run at intervals"
    input_schema = {
        "type": "object",
        "properties": {
            "cron": {"type": "string", "description": "Cron expression"},
            "task": {"type": "string", "description": "Task to execute"}
        },
        "required": ["cron", "task"]
    }
    
    async def execute(self, args: dict, progress_callback=None) -> ToolResult:
        cron = args["cron"]
        task = args["task"]
        
        # 注册 cron 任务
        # 返回任务 ID
        
        return ToolResult(
            success=True,
            output=f"Scheduled: {task} with cron '{cron}'"
        )
