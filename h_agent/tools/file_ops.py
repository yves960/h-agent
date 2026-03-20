#!/usr/bin/env python3
"""
h_agent/tools/file_ops.py - File operation tools

Tools:
- file_read: Read file contents with offset/limit
- file_write: Write content to file
- file_edit: Make precise edits to file
- file_glob: Find files by pattern
- file_exists: Check if file exists
- file_info: Get file metadata
"""

import os
import glob as glob_module
import json
import hashlib
from pathlib import Path
from typing import Callable, Dict, List, Any

# ============================================================
# Tool Definitions
# ============================================================

TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "file_read",
            "description": "Read the contents of a file. Supports relative and absolute paths.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file to read"},
                    "offset": {
                        "type": "integer",
                        "description": "Line number to start reading from (1-indexed)",
                        "default": 1
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of lines to read (0 = all)",
                        "default": 0
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "file_write",
            "description": "Write content to a file. Creates parent directories if needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file to write"},
                    "content": {"type": "string", "description": "Content to write to the file"},
                    "append": {
                        "type": "boolean",
                        "description": "Append to existing file instead of overwriting",
                        "default": False
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "file_edit",
            "description": "Make a precise edit to a file by replacing exact text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file to edit"},
                    "old_text": {"type": "string", "description": "Exact text to find and replace (must match exactly including whitespace)"},
                    "new_text": {"type": "string", "description": "Text to replace with"}
                },
                "required": ["path", "old_text", "new_text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "file_glob",
            "description": "Find files matching a glob pattern.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Glob pattern (e.g., '**/*.py', 'src/**/*.js')"},
                    "path": {"type": "string", "description": "Base directory to search from", "default": "."},
                    "recursive": {"type": "boolean", "description": "Search recursively", "default": True}
                },
                "required": ["pattern"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "file_exists",
            "description": "Check if a file or directory exists.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to check"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "file_info",
            "description": "Get detailed file metadata (size, mtime, permissions, checksum).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file"},
                    "checksum": {
                        "type": "boolean",
                        "description": "Include MD5 checksum",
                        "default": False
                    }
                },
                "required": ["path"]
            }
        }
    }
]


# ============================================================
# Tool Handlers
# ============================================================

def _resolve_path(path: str) -> str:
    """Resolve relative paths to absolute."""
    if not os.path.isabs(path):
        path = os.path.join(os.getcwd(), path)
    return os.path.normpath(path)


def tool_file_read(path: str, offset: int = 1, limit: int = 0) -> str:
    """Read file contents."""
    path = _resolve_path(path)
    
    if not os.path.exists(path):
        return f"Error: File not found: {path}"
    
    if os.path.isdir(path):
        return f"Error: Path is a directory: {path}"
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        start = max(0, offset - 1)
        end = start + limit if limit > 0 else len(lines)
        selected = lines[start:end]
        
        result = ''.join(selected)
        
        if not result:
            return "(empty file)"
        
        # Add context header for large files
        if limit > 0 and len(lines) > limit:
            total = len(lines)
            result = f"# Lines {offset}-{end} of {total}\n" + result
        
        return result
    except UnicodeDecodeError:
        return "Error: Binary file, cannot read as text"
    except Exception as e:
        return f"Error: {e}"


def tool_file_write(path: str, content: str, append: bool = False) -> str:
    """Write content to a file."""
    path = _resolve_path(path)
    
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        mode = 'a' if append else 'w'
        with open(path, mode, encoding='utf-8') as f:
            f.write(content)
        
        action = "Appended" if append else "Wrote"
        return f"{action} {len(content)} characters to {path}"
    except Exception as e:
        return f"Error: {e}"


def tool_file_edit(path: str, old_text: str, new_text: str) -> str:
    """Make a precise edit to a file."""
    path = _resolve_path(path)
    
    if not os.path.exists(path):
        return f"Error: File not found: {path}"
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if old_text not in content:
            # Show what we have around the expected area for debugging
            return "Error: Text not found in file. The old_text must match exactly (including whitespace)."
        
        count = content.count(old_text)
        if count > 1:
            return f"Error: Found {count} occurrences of old_text. old_text must be unique."
        
        new_content = content.replace(old_text, new_text, 1)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return f"Successfully edited {path}"
    except Exception as e:
        return f"Error: {e}"


def tool_file_glob(pattern: str, path: str = ".", recursive: bool = True) -> str:
    """Find files matching a pattern."""
    path = _resolve_path(path)
    
    try:
        if recursive:
            full_pattern = os.path.join(path, "**", pattern)
            matches = glob_module.glob(full_pattern, recursive=True)
        else:
            full_pattern = os.path.join(path, pattern)
            matches = glob_module.glob(full_pattern)
        
        if not matches:
            return f"No files found matching '{pattern}' in {path}"
        
        # Format results
        results = []
        for m in sorted(matches):
            if os.path.isfile(m):
                rel = os.path.relpath(m, path)
                size = os.path.getsize(m)
                results.append(f"{rel} ({size} bytes)")
        
        if not results:
            return f"No files found matching '{pattern}' in {path}"
        
        return '\n'.join(results)
    except Exception as e:
        return f"Error: {e}"


def tool_file_exists(path: str) -> str:
    """Check if file exists."""
    path = _resolve_path(path)
    
    if os.path.exists(path):
        if os.path.isdir(path):
            return f"True: {path} is a directory"
        elif os.path.isfile(path):
            return f"True: {path} is a file"
        else:
            return f"True: {path} exists"
    else:
        return f"False: {path} does not exist"


def tool_file_info(path: str, checksum: bool = False) -> str:
    """Get file metadata."""
    path = _resolve_path(path)
    
    if not os.path.exists(path):
        return f"Error: File not found: {path}"
    
    if not os.path.isfile(path):
        return f"Error: Path is not a file: {path}"
    
    try:
        stat = os.stat(path)
        info = {
            "path": path,
            "size": f"{stat.st_size} bytes",
            "modified": stat.st_mtime,
            "permissions": oct(stat.st_mode)[-3:],
            "is_file": os.path.isfile(path),
            "is_dir": os.path.isdir(path),
        }
        
        if checksum:
            with open(path, 'rb') as f:
                md5 = hashlib.md5(f.read()).hexdigest()
            info["md5"] = md5
        
        return json.dumps(info, indent=2)
    except Exception as e:
        return f"Error: {e}"


# ============================================================
# Handler Dispatch Map
# ============================================================

TOOL_HANDLERS: Dict[str, Callable] = {
    "file_read": tool_file_read,
    "file_write": tool_file_write,
    "file_edit": tool_file_edit,
    "file_glob": tool_file_glob,
    "file_exists": tool_file_exists,
    "file_info": tool_file_info,
}
