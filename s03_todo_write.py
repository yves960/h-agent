#!/usr/bin/env python3
"""
s03_todo_write.py - Task Planning with TodoWrite

An agent without a plan drifts.
List the steps first, then execute; completion doubles.

This adds a TodoWrite tool that allows the agent to manage a task list.
The agent can:
- Create todos
- Update their status
- Track progress

The todos are injected into the system prompt as a reminder.
"""

import os
import json
import glob as glob_module
import subprocess
from openai import OpenAI
from dotenv import load_dotenv
from typing import Callable, Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum

load_dotenv(override=True)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "sk-dummy"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
)
MODEL = os.getenv("MODEL_ID", "gpt-4o")


# ============================================================
# Todo System
# ============================================================

class TodoStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass
class Todo:
    id: str
    content: str
    status: TodoStatus = TodoStatus.PENDING
    priority: int = 1  # 1-5, 5 highest
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "status": self.status.value,
            "priority": self.priority,
        }


class TodoManager:
    """Manages the agent's task list."""
    
    def __init__(self):
        self.todos: Dict[str, Todo] = {}
        self._counter = 0
    
    def _next_id(self) -> str:
        self._counter += 1
        return f"todo-{self._counter}"
    
    def add(self, content: str, priority: int = 1) -> Todo:
        """Add a new todo item."""
        todo = Todo(
            id=self._next_id(),
            content=content,
            priority=priority,
        )
        self.todos[todo.id] = todo
        return todo
    
    def update(self, todo_id: str, status: Optional[str] = None, 
               content: Optional[str] = None) -> Optional[Todo]:
        """Update a todo item."""
        if todo_id not in self.todos:
            return None
        
        todo = self.todos[todo_id]
        if status:
            todo.status = TodoStatus(status)
        if content:
            todo.content = content
        return todo
    
    def list(self) -> List[Todo]:
        """List all todos, sorted by priority and status."""
        return sorted(
            self.todos.values(),
            key=lambda t: (-t.priority, list(TodoStatus).index(t.status))
        )
    
    def clear_completed(self) -> int:
        """Remove completed todos."""
        completed = [t for t in self.todos.values() if t.status == TodoStatus.COMPLETED]
        for t in completed:
            del self.todos[t.id]
        return len(completed)
    
    def format_for_prompt(self) -> str:
        """Format todos for inclusion in system prompt."""
        if not self.todos:
            return "No active tasks."
        
        lines = ["Current Tasks:"]
        for todo in self.list():
            status_icon = {
                TodoStatus.PENDING: "⏳",
                TodoStatus.IN_PROGRESS: "🔄",
                TodoStatus.COMPLETED: "✅",
            }.get(todo.status, "❓")
            lines.append(f"  {status_icon} [{todo.id}] {todo.content}")
        return "\n".join(lines)


# Global todo manager instance
todo_manager = TodoManager()


# ============================================================
# Tool Definitions
# ============================================================

TOOLS = [
    # bash, read, write, edit, glob 同 s02
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a shell command.",
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
            "description": "Read file contents.",
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
    },
    {
        "type": "function",
        "function": {
            "name": "write",
            "description": "Write content to a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file"},
                    "content": {"type": "string", "description": "Content to write"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit",
            "description": "Make a precise edit to a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file"},
                    "old_text": {"type": "string", "description": "Exact text to replace"},
                    "new_text": {"type": "string", "description": "New text"}
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
                    "pattern": {"type": "string", "description": "Glob pattern"},
                    "path": {"type": "string", "description": "Base directory", "default": "."}
                },
                "required": ["pattern"]
            }
        }
    },
    # 新增: TodoWrite 工具
    {
        "type": "function",
        "function": {
            "name": "TodoWrite",
            "description": "Manage your task list. Use this to plan and track your work. Always list tasks before starting work.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["add", "update", "list", "clear_completed"],
                        "description": "Action to perform"
                    },
                    "todos": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string", "description": "Todo ID (for update)"},
                                "content": {"type": "string", "description": "Task description"},
                                "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]},
                                "priority": {"type": "integer", "description": "Priority 1-5"}
                            }
                        },
                        "description": "List of todo items (for add/update)"
                    }
                },
                "required": ["action"]
            }
        }
    }
]


# ============================================================
# Tool Handlers
# ============================================================

def tool_bash(command: str) -> str:
    dangerous = ["rm -rf /", "sudo rm", "mkfs", "dd if="]
    if any(d in command for d in dangerous):
        return "Error: Dangerous command blocked"
    try:
        result = subprocess.run(command, shell=True, cwd=os.getcwd(),
                               capture_output=True, text=True, timeout=120)
        output = (result.stdout + result.stderr).strip()
        return output[:50000] if output else "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Timeout"
    except Exception as e:
        return f"Error: {e}"


def tool_read(path: str, offset: int = 1, limit: int = 2000) -> str:
    try:
        if not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)
        if not os.path.exists(path):
            return f"Error: File not found: {path}"
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        start = max(0, offset - 1)
        end = start + limit if limit > 0 else len(lines)
        return ''.join(lines[start:end]) or "(empty file)"
    except UnicodeDecodeError:
        return "Error: Binary file"
    except Exception as e:
        return f"Error: {e}"


def tool_write(path: str, content: str) -> str:
    try:
        if not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Wrote {len(content)} chars to {path}"
    except Exception as e:
        return f"Error: {e}"


def tool_edit(path: str, old_text: str, new_text: str) -> str:
    try:
        if not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)
        if not os.path.exists(path):
            return f"Error: File not found: {path}"
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        if old_text not in content:
            return "Error: Text not found"
        count = content.count(old_text)
        if count > 1:
            return f"Error: Found {count} occurrences, must be unique"
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content.replace(old_text, new_text))
        return f"Edited {path}"
    except Exception as e:
        return f"Error: {e}"


def tool_glob(pattern: str, path: str = ".") -> str:
    try:
        if not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)
        matches = glob_module.glob(os.path.join(path, pattern), recursive=True)
        rel_matches = [os.path.relpath(m, path) for m in matches]
        return '\n'.join(sorted(rel_matches)) if rel_matches else "No files found"
    except Exception as e:
        return f"Error: {e}"


def tool_todo_write(action: str, todos: List[dict] = None) -> str:
    """Handle TodoWrite tool calls."""
    if action == "add" and todos:
        added = []
        for t in todos:
            todo = todo_manager.add(
                content=t.get("content", ""),
                priority=t.get("priority", 1)
            )
            added.append(todo.to_dict())
        return json.dumps({"added": added, "message": f"Added {len(added)} tasks"})
    
    elif action == "update" and todos:
        updated = []
        for t in todos:
            todo = todo_manager.update(
                todo_id=t.get("id"),
                status=t.get("status"),
                content=t.get("content")
            )
            if todo:
                updated.append(todo.to_dict())
        return json.dumps({"updated": updated})
    
    elif action == "list":
        todos = [t.to_dict() for t in todo_manager.list()]
        return json.dumps({"todos": todos})
    
    elif action == "clear_completed":
        count = todo_manager.clear_completed()
        return json.dumps({"cleared": count})
    
    return json.dumps({"error": "Unknown action"})


TOOL_HANDLERS: Dict[str, Callable] = {
    "bash": tool_bash,
    "read": tool_read,
    "write": tool_write,
    "edit": tool_edit,
    "glob": tool_glob,
    "TodoWrite": tool_todo_write,
}


# ============================================================
# Agent Loop with Dynamic System Prompt
# ============================================================

def get_system_prompt() -> str:
    """Generate system prompt with current todo state."""
    todos_prompt = todo_manager.format_for_prompt()
    return f"""You are a coding agent at {os.getcwd()}.

Use the available tools to solve tasks efficiently.
IMPORTANT: Before starting complex tasks, use TodoWrite to list the steps.
Track your progress by updating task status.

{todos_prompt}

Act, don't explain too much."""


def execute_tool_call(tool_call) -> str:
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    handler = TOOL_HANDLERS.get(function_name)
    if not handler:
        return f"Error: Unknown tool '{function_name}'"
    return handler(**arguments)


def agent_loop(messages: list):
    """Agent loop with dynamic system prompt."""
    while True:
        # 每次调用时更新系统提示（包含最新 todo 状态）
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": get_system_prompt()}] + messages,
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
            if tool_call.function.name == "TodoWrite":
                print(f"\033[32m📋 TodoWrite: {args.get('action')}\033[0m")
            else:
                cmd = args.get('command', '') or args.get('path', '') or str(list(args.keys())[0] if args else '')
                print(f"\033[33m$ {tool_call.function.name}({cmd[:50]}...)\033[0m")
            
            result = execute_tool_call(tool_call)
            print(result[:200] + ("..." if len(result) > 200 else ""))
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })


def main():
    print(f"\033[36mOpenAI Agent Harness - s03 (TodoWrite)\033[0m")
    print(f"Model: {MODEL}")
    print(f"Tools: {', '.join(TOOL_HANDLERS.keys())}")
    print(f"Working directory: {os.getcwd()}")
    print("Type 'q' to quit, 'todos' to list tasks\n")
    
    history = []
    
    while True:
        try:
            query = input("\033[36m>> \033[0m")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        
        if query.strip().lower() == "q":
            break
        if query.strip().lower() == "todos":
            print(todo_manager.format_for_prompt())
            continue
        
        history.append({"role": "user", "content": query})
        agent_loop(history)
        
        last = history[-1]
        if last["role"] == "assistant" and last.get("content"):
            print(f"\n{last['content']}\n")


if __name__ == "__main__":
    main()