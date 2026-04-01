import subprocess
from pathlib import Path
from .base import Tool, ToolResult


class EnterWorktreeTool(Tool):
    name = "enter_worktree"
    description = "Create and enter a git worktree for isolated work"
    input_schema = {
        "type": "object",
        "properties": {
            "branch": {"type": "string", "description": "Branch name"},
            "path": {"type": "string", "description": "Worktree path"}
        },
        "required": ["branch"]
    }
    
    async def execute(self, args: dict, progress_callback=None) -> ToolResult:
        branch = args["branch"]
        path = args.get("path", f".worktrees/{branch}")
        
        result = subprocess.run(
            ["git", "worktree", "add", path, "-b", branch],
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            return ToolResult(success=False, error=result.stderr)
        
        return ToolResult(success=True, output=f"Created worktree at {path}")


class ExitWorktreeTool(Tool):
    name = "exit_worktree"
    description = "Exit and remove git worktree"
    input_schema = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    async def execute(self, args: dict, progress_callback=None) -> ToolResult:
        result = subprocess.run(
            ["git", "worktree", "remove", "."],
            capture_output=True, text=True
        )
        
        return ToolResult(
            success=result.returncode == 0,
            output=result.stdout or result.stderr
        )
