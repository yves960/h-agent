"""
h_agent/tools/__init__.py - Tool System

Modern tool system inspired by Claude Code's Tool architecture.
"""

from h_agent.tools.base import Tool, ToolResult
from h_agent.tools.registry import ToolRegistry, get_registry

# Convenience imports for built-in tools
from h_agent.tools.bash import BashTool
from h_agent.tools.file_read import FileReadTool
from h_agent.tools.file_write import FileWriteTool
from h_agent.tools.file_edit import FileEditTool

# New tools: glob, grep, web_fetch, web_search
from h_agent.tools.glob import GlobTool
from h_agent.tools.grep import GrepTool
from h_agent.tools.web_fetch import WebFetchTool
from h_agent.tools.web_search import WebSearchTool
from h_agent.tools.lsp import LSPTool
from h_agent.tools.notebook import NotebookEditTool
from h_agent.tools.plan import EnterPlanModeTool, ExitPlanModeTool
from h_agent.tools.worktree import EnterWorktreeTool, ExitWorktreeTool
from h_agent.tools.todo import TodoWriteTool
from h_agent.tools.ask import AskUserQuestionTool
from h_agent.tools.sleep import SleepTool
from h_agent.tools.schedule import ScheduleCronTool

__all__ = [
    "Tool",
    "ToolResult",
    "ToolRegistry",
    "get_registry",
    "BashTool",
    "FileReadTool",
    "FileWriteTool",
    "FileEditTool",
    "GlobTool",
    "GrepTool",
    "WebFetchTool",
    "WebSearchTool",
    "LSPTool",
    "NotebookEditTool",
    "EnterPlanModeTool",
    "ExitPlanModeTool",
    "EnterWorktreeTool",
    "ExitWorktreeTool",
    "TodoWriteTool",
    "AskUserQuestionTool",
    "SleepTool",
    "ScheduleCronTool",
]
