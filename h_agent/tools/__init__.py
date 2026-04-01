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

__all__ = [
    "Tool",
    "ToolResult",
    "ToolRegistry",
    "get_registry",
    "BashTool",
    "FileReadTool",
    "FileWriteTool",
    "FileEditTool",
]
