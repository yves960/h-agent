from dataclasses import dataclass
from typing import List
from .base import Tool, ToolResult


@dataclass
class TodoItem:
    content: str
    status: str = "pending"  # pending, in_progress, completed


class TodoWriteTool(Tool):
    name = "todo_write"
    description = "Manage todo list for tracking progress"
    input_schema = {
        "type": "object",
        "properties": {
            "todos": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string"},
                        "status": {"type": "string"}
                    }
                }
            }
        },
        "required": ["todos"]
    }
    
    _todos: List[TodoItem] = []
    
    async def execute(self, args: dict, progress_callback=None) -> ToolResult:
        todos_data = args["todos"]
        
        self._todos = [
            TodoItem(content=t["content"], status=t.get("status", "pending"))
            for t in todos_data
        ]
        
        # 格式化输出
        lines = ["Todo list:"]
        for i, todo in enumerate(self._todos, 1):
            status_icon = {"pending": "⏳", "in_progress": "🔄", "completed": "✅"}
            lines.append(f"{i}. {status_icon.get(todo.status, '❓')} {todo.content}")
        
        return ToolResult(success=True, output="\n".join(lines))
