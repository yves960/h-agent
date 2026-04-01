from .base import Tool, ToolResult


class AskUserQuestionTool(Tool):
    name = "ask_user"
    description = "Ask user a question and wait for response"
    input_schema = {
        "type": "object",
        "properties": {
            "question": {"type": "string"},
            "options": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["question"]
    }
    
    async def execute(self, args: dict, progress_callback=None) -> ToolResult:
        question = args["question"]
        options = args.get("options", [])
        
        # 在实际 REPL 中，这会等待用户输入
        # 目前返回占位结果
        
        output = f"Question: {question}"
        if options:
            output += f"\nOptions: {', '.join(options)}"
        
        return ToolResult(success=True, output=output)
