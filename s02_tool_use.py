#!/usr/bin/env python3
"""
s02_tool_use.py - Multiple Tools with Dispatch Map

Adding a tool means adding one handler.
The loop stays the same; tools register into a dispatch map.

Tools implemented:
- bash: Execute shell commands
- read: Read file contents
- write: Write content to file
- edit: Make precise edits to files
- glob: Find files by pattern
"""

import os
import json
import glob as glob_module
import subprocess
from openai import OpenAI
from dotenv import load_dotenv
from typing import Callable, Dict, Any

load_dotenv(override=True)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "sk-dummy"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
)
MODEL = os.getenv("MODEL_ID", "gpt-4o")

SYSTEM = f"""You are a coding agent at {os.getcwd()}.
Use the available tools to solve tasks efficiently.
Act, don't explain too much."""

# ============================================================
# Tool Definitions (OpenAI format)
# ============================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a shell command. Use for file operations, git, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command"}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read",
            "description": "Read the contents of a file. Returns the text content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file to read"},
                    "offset": {"type": "integer", "description": "Line number to start reading from (1-indexed)", "default": 1},
                    "limit": {"type": "integer", "description": "Maximum number of lines to read", "default": 2000}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write",
            "description": "Write content to a file. Creates the file if it doesn't exist, overwrites if it does.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file to write"},
                    "content": {"type": "string", "description": "Content to write to the file"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit",
            "description": "Make a precise edit to a file by replacing exact text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file to edit"},
                    "old_text": {"type": "string", "description": "Exact text to find and replace"},
                    "new_text": {"type": "string", "description": "Text to replace with"}
                },
                "required": ["path", "old_text", "new_text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "glob",
            "description": "Find files matching a pattern.",
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
]


# ============================================================
# Tool Handlers
# ============================================================

def tool_bash(command: str) -> str:
    """Execute a shell command."""
    dangerous = ["rm -rf /", "sudo rm", "mkfs", "dd if=", "> /dev/sd"]
    if any(d in command for d in dangerous):
        return "Error: Dangerous command blocked"
    try:
        result = subprocess.run(
            command, shell=True, cwd=os.getcwd(),
            capture_output=True, text=True, timeout=120
        )
        output = (result.stdout + result.stderr).strip()
        return output[:50000] if output else "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Timeout (120s)"
    except Exception as e:
        return f"Error: {e}"


def tool_read(path: str, offset: int = 1, limit: int = 2000) -> str:
    """Read file contents."""
    try:
        # 支持相对路径和绝对路径
        if not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)
        
        if not os.path.exists(path):
            return f"Error: File not found: {path}"
        
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 处理 offset 和 limit
        start = max(0, offset - 1)
        end = start + limit if limit > 0 else len(lines)
        selected = lines[start:end]
        
        result = ''.join(selected)
        return result if result else "(empty file)"
    except UnicodeDecodeError:
        return "Error: Binary file, cannot read as text"
    except Exception as e:
        return f"Error: {e}"


def tool_write(path: str, content: str) -> str:
    """Write content to a file."""
    try:
        if not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)
        
        # 创建父目录
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"Successfully wrote {len(content)} characters to {path}"
    except Exception as e:
        return f"Error: {e}"


def tool_edit(path: str, old_text: str, new_text: str) -> str:
    """Make a precise edit to a file."""
    try:
        if not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)
        
        if not os.path.exists(path):
            return f"Error: File not found: {path}"
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if old_text not in content:
            return f"Error: Text not found in file. The old_text must match exactly."
        
        # 统计出现次数
        count = content.count(old_text)
        if count > 1:
            return f"Error: Found {count} occurrences of old_text. It must be unique."
        
        new_content = content.replace(old_text, new_text)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return f"Successfully edited {path}"
    except Exception as e:
        return f"Error: {e}"


def tool_glob(pattern: str, path: str = ".") -> str:
    """Find files matching a pattern."""
    try:
        if not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)
        
        matches = glob_module.glob(os.path.join(path, pattern), recursive=True)
        
        # 转换为相对路径
        rel_matches = [os.path.relpath(m, path) for m in matches]
        
        if not rel_matches:
            return "No files found"
        
        return '\n'.join(sorted(rel_matches))
    except Exception as e:
        return f"Error: {e}"


# ============================================================
# Tool Dispatch Map
# ============================================================

TOOL_HANDLERS: Dict[str, Callable] = {
    "bash": tool_bash,
    "read": tool_read,
    "write": tool_write,
    "edit": tool_edit,
    "glob": tool_glob,
}


def execute_tool_call(tool_call) -> str:
    """Execute a tool call using the dispatch map."""
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    
    handler = TOOL_HANDLERS.get(function_name)
    if not handler:
        return f"Error: Unknown tool '{function_name}'"
    
    return handler(**arguments)


# ============================================================
# Agent Loop (same as s01, but with dispatch map)
# ============================================================

def agent_loop(messages: list):
    """The core agent loop with multi-tool support."""
    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=8000,
        )
        
        message = response.choices[0].message
        
        messages.append({
            "role": "assistant",
            "content": message.content,
            "tool_calls": message.tool_calls,
        })
        
        if not message.tool_calls:
            return
        
        for tool_call in message.tool_calls:
            args = json.loads(tool_call.function.arguments)
            # 打印工具调用
            if tool_call.function.name == "bash":
                print(f"\033[33m$ {args.get('command', '')}\033[0m")
            else:
                print(f"\033[33m{tool_call.function.name}({list(args.keys())[0]}=...)\033[0m")
            
            result = execute_tool_call(tool_call)
            print(result[:200] + ("..." if len(result) > 200 else ""))
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })


def main():
    """Interactive REPL."""
    print(f"\033[36mOpenAI Agent Harness - s02 (Multi-Tool)\033[0m")
    print(f"Model: {MODEL}")
    print(f"Tools: {', '.join(TOOL_HANDLERS.keys())}")
    print(f"Working directory: {os.getcwd()}")
    print("Type 'q' or 'exit' to quit\n")
    
    history = []
    
    while True:
        try:
            query = input("\033[36m>> \033[0m")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        
        if query.strip().lower() in ("q", "exit", ""):
            print("Goodbye!")
            break
        
        history.append({"role": "user", "content": query})
        agent_loop(history)
        
        last = history[-1]
        if last["role"] == "assistant" and last.get("content"):
            print(f"\n{last['content']}\n")


if __name__ == "__main__":
    main()