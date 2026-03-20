"""
Agent Core - 整合所有功能的完整 Agent
"""

import os
import json
import time
import threading
import subprocess
import glob as glob_module
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# 配置
# ============================================================

@dataclass
class AgentConfig:
    """Agent 配置。"""
    agent_id: str = "default"
    model: str = ""
    max_tokens: int = 4096
    max_context: int = 150000
    workspace: str = ""
    
    def __post_init__(self):
        if not self.model:
            self.model = os.getenv("MODEL_ID", "gpt-4o")
        if not self.workspace:
            self.workspace = os.getcwd()


# ============================================================
# 工具系统
# ============================================================

class Tool:
    """工具基类。"""
    name: str = "tool"
    description: str = ""
    
    def get_schema(self) -> dict:
        """返回 OpenAI 工具 schema。"""
        raise NotImplementedError
    
    def execute(self, **kwargs) -> str:
        """执行工具。"""
        raise NotImplementedError


class BashTool(Tool):
    """Shell 命令工具。"""
    name = "bash"
    description = "Run a shell command"
    
    def __init__(self, workspace: str = None):
        self.workspace = workspace or os.getcwd()
    
    def get_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "The shell command"}
                    },
                    "required": ["command"]
                }
            }
        }
    
    def execute(self, command: str) -> str:
        # 安全检查
        dangerous = ["rm -rf /", "sudo rm", "mkfs", "dd if="]
        if any(d in command for d in dangerous):
            return "Error: Dangerous command blocked"
        
        try:
            result = subprocess.run(
                command, shell=True, cwd=self.workspace,
                capture_output=True, text=True, timeout=120
            )
            output = (result.stdout + result.stderr).strip()
            return output[:50000] if output else "(no output)"
        except subprocess.TimeoutExpired:
            return "Error: Timeout (120s)"
        except Exception as e:
            return f"Error: {e}"


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
                        "path": {"type": "string"},
                        "offset": {"type": "integer", "default": 1},
                        "limit": {"type": "integer", "default": 2000}
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
            return ''.join(lines[start:start+limit]) or "(empty)"
        except Exception as e:
            return f"Error: {e}"


class WriteTool(Tool):
    """文件写入工具。"""
    name = "write"
    description = "Write content to file"
    
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
                        "path": {"type": "string"},
                        "content": {"type": "string"}
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
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')
            return f"Wrote {len(content)} chars"
        except Exception as e:
            return f"Error: {e}"


class EditTool(Tool):
    """精确编辑工具。"""
    name = "edit"
    description = "Make precise edit to file"
    
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
                        "path": {"type": "string"},
                        "old_text": {"type": "string"},
                        "new_text": {"type": "string"}
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
                return "Error: File not found"
            content = path.read_text(encoding='utf-8')
            if old_text not in content:
                return "Error: Text not found"
            if content.count(old_text) > 1:
                return "Error: Multiple matches"
            path.write_text(content.replace(old_text, new_text), encoding='utf-8')
            return "Edited successfully"
        except Exception as e:
            return f"Error: {e}"


class GlobTool(Tool):
    """文件搜索工具。"""
    name = "glob"
    description = "Find files by pattern"
    
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
                        "pattern": {"type": "string"},
                        "path": {"type": "string", "default": "."}
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
            return '\n'.join(os.path.relpath(m, path) for m in matches) or "No files"
        except Exception as e:
            return f"Error: {e}"


class ToolRegistry:
    """工具注册表。"""
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
    
    def register(self, tool: Tool):
        self._tools[tool.name] = tool
    
    def get_schemas(self) -> list:
        return [t.get_schema() for t in self._tools.values()]
    
    def execute(self, name: str, **kwargs) -> str:
        if name not in self._tools:
            return f"Error: Unknown tool '{name}'"
        return self._tools[name].execute(**kwargs)
    
    def register_defaults(self, workspace: str = None):
        """注册默认工具。"""
        self.register(BashTool(workspace))
        self.register(ReadTool(workspace))
        self.register(WriteTool(workspace))
        self.register(EditTool(workspace))
        self.register(GlobTool(workspace))


# ============================================================
# 记忆系统
# ============================================================

class MemoryStore:
    """记忆存储。"""
    
    def __init__(self, agent_id: str = "default"):
        self.agent_id = agent_id
        self._memory: Dict[str, str] = {}
    
    def set(self, key: str, value: str):
        self._memory[key] = value
    
    def get(self, key: str) -> str:
        return self._memory.get(key, "")
    
    def search(self, query: str) -> List[str]:
        results = []
        query_lower = query.lower()
        for key, value in self._memory.items():
            if query_lower in key.lower() or query_lower in value.lower():
                results.append(f"[{key}]\n{value}")
        return results


class SessionStore:
    """会话存储。"""
    
    def __init__(self, agent_id: str = "default"):
        self.agent_id = agent_id
        self._sessions: Dict[str, List[dict]] = {}
    
    def get_or_create(self, session_key: str) -> List[dict]:
        if session_key not in self._sessions:
            self._sessions[session_key] = []
        return self._sessions[session_key]
    
    def add_message(self, session_key: str, role: str, content: str):
        session = self.get_or_create(session_key)
        session.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })


# ============================================================
# Agent 核心类
# ============================================================

class Agent:
    """完整的 Agent 类。"""
    
    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig()
        
        # 初始化客户端
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "sk-dummy"),
            base_url=os.getenv("OPENAI_BASE_URL"),
        )
        
        # 初始化组件
        self.tools = ToolRegistry()
        self.tools.register_defaults(self.config.workspace)
        
        self.memory = MemoryStore(self.config.agent_id)
        self.sessions = SessionStore(self.config.agent_id)
        
        # 状态
        self._session_key = "default"
        self._running = False
    
    def get_system_prompt(self) -> str:
        """构建系统提示。"""
        memory_context = "\n".join(self.memory.search(""))[:5000]
        
        return f"""You are a helpful AI agent.

Agent ID: {self.config.agent_id}
Workspace: {self.config.workspace}

{memory_context}

Use tools to help the user. Be efficient and helpful."""
    
    def chat(self, message: str, session_key: str = None) -> str:
        """对话。"""
        if session_key:
            self._session_key = session_key
        
        # 获取会话历史
        messages = self.sessions.get_or_create(self._session_key)
        messages.append({"role": "user", "content": message})
        
        # Agent 循环
        while True:
            # 构建完整消息
            full_messages = [
                {"role": "system", "content": self.get_system_prompt()}
            ] + messages[-20:]
            
            # 调用 LLM
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=full_messages,
                tools=self.tools.get_schemas(),
                tool_choice="auto",
                max_tokens=self.config.max_tokens,
            )
            
            msg = response.choices[0].message
            messages.append({
                "role": "assistant",
                "content": msg.content,
                "tool_calls": msg.tool_calls,
            })
            
            # 没有工具调用则结束
            if not msg.tool_calls:
                return msg.content or ""
            
            # 执行工具
            for tool_call in msg.tool_calls:
                args = json.loads(tool_call.function.arguments)
                result = self.tools.execute(tool_call.function.name, **args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })
    
    def run_interactive(self):
        """交互模式运行。"""
        print(f"\033[36mOpenAI Agent Harness\033[0m")
        print(f"Model: {self.config.model}")
        print(f"Workspace: {self.config.workspace}")
        print("Type 'quit' to exit\n")
        
        self._running = True
        
        while self._running:
            try:
                user_input = input("\033[36mYou> \033[0m")
            except (EOFError, KeyboardInterrupt):
                break
            
            if user_input.strip().lower() in ("quit", "exit", "q"):
                break
            
            if not user_input.strip():
                continue
            
            response = self.chat(user_input)
            print(f"\n{response}\n")
        
        print("Goodbye!")


def run_agent():
    """运行 Agent（命令行入口）。"""
    agent = Agent()
    agent.run_interactive()


if __name__ == "__main__":
    run_agent()