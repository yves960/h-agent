"""
Tools - 完整的工具实现
"""

import os
import subprocess
import glob as glob_module
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ToolResult:
    """工具执行结果。"""
    success: bool
    output: str
    error: str = ""


class Tool:
    """工具基类。"""
    name: str = "tool"
    description: str = ""
    
    def get_schema(self) -> dict:
        raise NotImplementedError
    
    def execute(self, **kwargs) -> str:
        raise NotImplementedError


# ============================================================
# Bash Tool
# ============================================================

class BashTool(Tool):
    """Shell 命令工具。"""
    name = "bash"
    description = "Run a shell command"
    
    def __init__(self, workspace: str = None, timeout: int = 120):
        self.workspace = workspace or os.getcwd()
        self.timeout = timeout
    
    def get_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "The shell command to execute"}
                    },
                    "required": ["command"]
                }
            }
        }
    
    def execute(self, command: str) -> str:
        # 安全检查
        dangerous = ["rm -rf /", "sudo rm", "mkfs", "dd if=", "> /dev/sd"]
        if any(d in command for d in dangerous):
            return "Error: Dangerous command blocked for safety"
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.workspace,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            output = (result.stdout + result.stderr).strip()
            return output[:50000] if output else "(no output)"
        except subprocess.TimeoutExpired:
            return f"Error: Command timed out ({self.timeout}s)"
        except Exception as e:
            return f"Error: {e}"


# ============================================================
# Read Tool
# ============================================================

class ReadTool(Tool):
    """文件读取工具。"""
    name = "read"
    description = "Read file contents"
    
    def __init__(self, workspace: str = None):
        self.workspace = Path(workspace or os.getcwd())
    
    def get_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to the file"},
                        "offset": {"type": "integer", "description": "Start line (1-indexed)", "default": 1},
                        "limit": {"type": "integer", "description": "Max lines to read", "default": 2000}
                    },
                    "required": ["path"]
                }
            }
        }
    
    def execute(self, path: str, offset: int = 1, limit: int = 2000) -> str:
        try:
            path = Path(path)
            if not path.is_absolute():
                path = self.workspace / path
            
            if not path.exists():
                return f"Error: File not found: {path}"
            
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            start = max(0, offset - 1)
            end = start + limit if limit > 0 else len(lines)
            content = ''.join(lines[start:end])
            
            return content or "(empty file)"
        except UnicodeDecodeError:
            return "Error: Binary file, cannot read as text"
        except Exception as e:
            return f"Error: {e}"


# ============================================================
# Write Tool
# ============================================================

class WriteTool(Tool):
    """文件写入工具。"""
    name = "write"
    description = "Write content to a file"
    
    def __init__(self, workspace: str = None):
        self.workspace = Path(workspace or os.getcwd())
    
    def get_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to the file"},
                        "content": {"type": "string", "description": "Content to write"}
                    },
                    "required": ["path", "content"]
                }
            }
        }
    
    def execute(self, path: str, content: str) -> str:
        try:
            path = Path(path)
            if not path.is_absolute():
                path = self.workspace / path
            
            # 创建父目录
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return f"Successfully wrote {len(content)} characters to {path}"
        except Exception as e:
            return f"Error: {e}"


# ============================================================
# Edit Tool
# ============================================================

class EditTool(Tool):
    """精确编辑工具。"""
    name = "edit"
    description = "Make a precise edit to a file by replacing exact text"
    
    def __init__(self, workspace: str = None):
        self.workspace = Path(workspace or os.getcwd())
    
    def get_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to the file"},
                        "old_text": {"type": "string", "description": "Exact text to find and replace"},
                        "new_text": {"type": "string", "description": "Text to replace with"}
                    },
                    "required": ["path", "old_text", "new_text"]
                }
            }
        }
    
    def execute(self, path: str, old_text: str, new_text: str) -> str:
        try:
            path = Path(path)
            if not path.is_absolute():
                path = self.workspace / path
            
            if not path.exists():
                return f"Error: File not found: {path}"
            
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if old_text not in content:
                return "Error: Text not found in file. The old_text must match exactly."
            
            # 检查是否唯一
            count = content.count(old_text)
            if count > 1:
                return f"Error: Found {count} occurrences of old_text. It must be unique."
            
            # 替换
            new_content = content.replace(old_text, new_text)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return f"Successfully edited {path}"
        except Exception as e:
            return f"Error: {e}"


# ============================================================
# Glob Tool
# ============================================================

class GlobTool(Tool):
    """文件搜索工具。"""
    name = "glob"
    description = "Find files matching a pattern"
    
    def __init__(self, workspace: str = None):
        self.workspace = Path(workspace or os.getcwd())
    
    def get_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string", "description": "Glob pattern (e.g., '**/*.py')"},
                        "path": {"type": "string", "description": "Base directory to search from", "default": "."}
                    },
                    "required": ["pattern"]
                }
            }
        }
    
    def execute(self, pattern: str, path: str = ".") -> str:
        try:
            path = Path(path)
            if not path.is_absolute():
                path = self.workspace / path
            
            matches = glob_module.glob(str(path / pattern), recursive=True)
            
            # 转换为相对路径
            rel_matches = [os.path.relpath(m, path) for m in matches]
            
            if not rel_matches:
                return "No files found matching pattern"
            
            return '\n'.join(sorted(rel_matches))
        except Exception as e:
            return f"Error: {e}"


# ============================================================
# Tool Registry
# ============================================================

class ToolRegistry:
    """工具注册表。"""
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._handlers: Dict[str, callable] = {}
    
    def register(self, tool: Tool):
        """注册工具。"""
        self._tools[tool.name] = tool
        self._handlers[tool.name] = tool.execute
    
    def unregister(self, name: str) -> bool:
        """移除工具。"""
        if name in self._tools:
            del self._tools[name]
            del self._handlers[name]
            return True
        return False
    
    def get_schemas(self) -> list:
        """获取所有工具的 OpenAI schema。"""
        return [tool.get_schema() for tool in self._tools.values()]
    
    def execute(self, name: str, **kwargs) -> str:
        """执行工具。"""
        if name not in self._handlers:
            return f"Error: Unknown tool '{name}'"
        return self._handlers[name](**kwargs)
    
    def list_tools(self) -> List[str]:
        """列出所有工具名。"""
        return list(self._tools.keys())
    
    def has_tool(self, name: str) -> bool:
        """检查工具是否存在。"""
        return name in self._tools
    
    def register_defaults(self, workspace: str = None):
        """注册默认工具集。"""
        self.register(BashTool(workspace))
        self.register(ReadTool(workspace))
        self.register(WriteTool(workspace))
        self.register(EditTool(workspace))
        self.register(GlobTool(workspace))


# ============================================================
# 便捷函数
# ============================================================

def create_default_tools(workspace: str = None) -> ToolRegistry:
    """创建默认工具注册表。"""
    registry = ToolRegistry()
    registry.register_defaults(workspace)
    return registry