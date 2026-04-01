import asyncio
from .base import Tool, ToolResult


class SleepTool(Tool):
    name = "sleep"
    description = "Wait for a specified duration"
    input_schema = {
        "type": "object",
        "properties": {
            "seconds": {"type": "number", "description": "Seconds to wait"}
        },
        "required": ["seconds"]
    }
    
    async def execute(self, args: dict, progress_callback=None) -> ToolResult:
        seconds = args["seconds"]
        
        if progress_callback:
            progress_callback(f"Sleeping for {seconds} seconds...")
        
        await asyncio.sleep(seconds)
        
        return ToolResult(success=True, output=f"Slept for {seconds} seconds")
