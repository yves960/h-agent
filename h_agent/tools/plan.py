from .base import Tool, ToolResult


class EnterPlanModeTool(Tool):
    name = "enter_plan_mode"
    description = "Enter planning mode for complex tasks"
    input_schema = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    async def execute(self, args: dict, progress_callback=None) -> ToolResult:
        # 切换到规划模式
        # 在规划模式下，agent 先制定计划，再执行
        return ToolResult(success=True, output="Entered plan mode")


class ExitPlanModeTool(Tool):
    name = "exit_plan_mode"
    description = "Exit planning mode"
    input_schema = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    async def execute(self, args: dict, progress_callback=None) -> ToolResult:
        return ToolResult(success=True, output="Exited plan mode")
