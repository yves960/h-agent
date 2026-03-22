#!/usr/bin/env python3
"""
h_agent/features/sessions.py - Sessions & Context Protection (OpenAI Version)

会话是 JSONL 文件。写入时追加，读取时重放。过大时进行摘要压缩。

核心组件:
  SessionStore -- JSONL 持久化
  ContextGuard -- 三阶段溢出重试

用户输入 -> load_session() -> guard_api_call() -> save_turn() -> 打印响应
"""

import os
import sys
import json
import uuid
import fcntl
import contextlib
from pathlib import Path
from datetime import datetime
from typing import Any, List, Dict, Optional
from dataclasses import dataclass, field, asdict
from h_agent.core.client import get_client
from h_agent.features.subagents import run_subagent

client = get_client()
MODEL = os.getenv("MODEL_ID", "gpt-4o")

WORKSPACE_DIR = Path.cwd() / ".agent_workspace"
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

CONTEXT_SAFE_LIMIT = 180000  # tokens
MAX_TOOL_OUTPUT = 50000
SESSION_TTL_DAYS = int(os.getenv("H_AGENT_SESSION_TTL_DAYS", "30"))  # Default 30 days

# Global references for tool handlers (set by SessionAwareAgent)
_global_agent_id = "default"
_global_context_guard = None
_global_session_store = None

# Platform detection for file locking
IS_WINDOWS = sys.platform == "win32"
_msvcrt = None
if IS_WINDOWS:
    try:
        import msvcrt
        _msvcrt = msvcrt
    except ImportError:
        pass


@contextlib.contextmanager
def _file_lock(path: Path, mode: str = "r"):
    """Platform-safe file locking context manager."""
    if IS_WINDOWS:
        flags = mode == "r" and 0x1 or 0x2
        fd = os.open(str(path), os.O_RDWR | os.O_CREAT, 0o644)
        _locking = getattr(_msvcrt, "locking", None)
        try:
            if _locking:
                _locking(fd, flags, 0)
            yield
        finally:
            if _locking:
                _locking(fd, 0x8, 0)
            os.close(fd)
    else:
        fd = os.open(str(path), os.O_RDWR | os.O_CREAT, 0o644)
        try:
            if mode == "r":
                fcntl.flock(fd, fcntl.LOCK_SH)
            else:
                fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)

# ============================================================
# Session Store - JSONL 持久化
# ============================================================

@dataclass
class SessionMeta:
    session_id: str
    agent_id: str
    created_at: str
    updated_at: str
    message_count: int = 0
    token_count: int = 0
    
    def to_dict(self) -> dict:
        return asdict(self)


class SessionStore:
    """管理 agent 会话的 JSONL 持久化存储。"""
    
    def __init__(self, agent_id: str = "default"):
        self.agent_id = agent_id
        self.base_dir = WORKSPACE_DIR / "sessions" / agent_id
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.base_dir / "index.json"
        self._index: Dict[str, dict] = self._load_index()
        self.current_session_id: Optional[str] = None
    
    def _load_index(self) -> Dict[str, dict]:
        if self.index_path.exists():
            try:
                return json.loads(self.index_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return {}
        return {}
    
    def _save_index(self) -> None:
        self.index_path.write_text(
            json.dumps(self._index, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
    
    def _session_path(self, session_id: str) -> Path:
        return self.base_dir / f"{session_id}.jsonl"
    
    def create_session(self) -> str:
        """创建新会话，返回 session_id。"""
        session_id = f"sess-{uuid.uuid4().hex[:8]}"
        now = datetime.now().isoformat()
        
        self._index[session_id] = SessionMeta(
            session_id=session_id,
            agent_id=self.agent_id,
            created_at=now,
            updated_at=now,
        ).to_dict()
        self._save_index()
        
        # 创建空的 JSONL 文件
        self._session_path(session_id).touch()
        
        self.current_session_id = session_id
        return session_id
    
    def load_session(self, session_id: str = None) -> List[dict]:
        """加载会话，返回 messages 列表。"""
        if session_id is None:
            session_id = self.current_session_id
        
        if not session_id or session_id not in self._index:
            return []
        
        messages = []
        session_file = self._session_path(session_id)
        
        if session_file.exists():
            with _file_lock(session_file, mode="r"):
                with open(session_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            try:
                                messages.append(json.loads(line))
                            except json.JSONDecodeError:
                                pass
        
        return messages
    
    def save_turn(self, role: str, content: Any, session_id: str = None) -> None:
        """保存一轮对话到 JSONL。"""
        if session_id is None:
            session_id = self.current_session_id
        
        if not session_id:
            session_id = self.create_session()
        
        turn = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        
        session_file = self._session_path(session_id)
        
        if session_id not in self._index:
            now = datetime.now().isoformat()
            self._index[session_id] = SessionMeta(
                session_id=session_id,
                agent_id=self.agent_id,
                created_at=now,
                updated_at=now,
            ).to_dict()
            session_file.touch()
        
        with _file_lock(session_file, mode="w"):
            with open(session_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(turn, ensure_ascii=False) + "\n")
        
        meta = self._index[session_id]
        meta["message_count"] = meta.get("message_count", 0) + 1
        meta["updated_at"] = datetime.now().isoformat()
        self._save_index()
    
    def get_recent_sessions(self, limit: int = 10) -> List[dict]:
        """获取最近的会话列表。"""
        sessions = sorted(
            self._index.values(),
            key=lambda x: x.get("updated_at", ""),
            reverse=True
        )
        return sessions[:limit]
    
    def cleanup_expired(self) -> int:
        """删除超过 TTL 的会话，返回删除数量。"""
        from datetime import timedelta
        expired_threshold = datetime.now() - timedelta(days=SESSION_TTL_DAYS)
        expired_ids = []
        
        for session_id, meta in self._index.items():
            updated_at = meta.get("updated_at", "")
            if updated_at:
                try:
                    dt = datetime.fromisoformat(updated_at)
                    if dt < expired_threshold:
                        expired_ids.append(session_id)
                except ValueError:
                    pass
        
        for session_id in expired_ids:
            self.delete_session(session_id)
        
        return len(expired_ids)
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话。"""
        if session_id not in self._index:
            return False
        
        session_file = self._session_path(session_id)
        if session_file.exists():
            session_file.unlink()
        
        del self._index[session_id]
        self._save_index()
        return True


# ============================================================
# Context Guard - 溢出保护
# ============================================================

class ContextGuard:
    """
    三阶段上下文溢出处理:
    1. 正常调用
    2. 截断工具结果
    3. 压缩历史 (50%)
    """
    
    def __init__(self, safe_limit: int = CONTEXT_SAFE_LIMIT):
        self.safe_limit = safe_limit
    
    def estimate_tokens(self, messages: List[dict]) -> int:
        """估算 token 数量（粗略：1 token ≈ 4 字符）。"""
        total = 0
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                total += len(content)
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        total += len(str(block))
                    else:
                        total += len(str(block))
        return total // 4
    
    def should_compact(self, messages: List[dict]) -> bool:
        """检查是否需要压缩。"""
        return self.estimate_tokens(messages) > self.safe_limit
    
    def truncate_tool_results(self, messages: List[dict], max_len: int = MAX_TOOL_OUTPUT) -> List[dict]:
        """截断工具结果（第一阶段压缩）。"""
        result = []
        for msg in messages:
            if msg.get("role") == "tool":
                content = msg.get("content", "")
                if len(content) > max_len:
                    half = max_len // 2
                    msg = {
                        **msg,
                        "content": content[:half] + f"\n... [truncated {len(content) - max_len} chars]\n" + content[-half:]
                    }
            result.append(msg)
        return result
    
    def compact_messages(self, messages: List[dict]) -> List[dict]:
        """压缩历史消息（第二阶段压缩）。"""
        if len(messages) <= 4:
            return messages
        
        # 保留系统消息和最近的消息
        system_msgs = [m for m in messages if m.get("role") == "system"]
        recent_msgs = messages[-4:]  # 保留最近的 4 条
        
        # 对中间的消息生成摘要
        middle_msgs = messages[:-4]
        if middle_msgs:
            summary = self._generate_summary(middle_msgs)
            if summary:
                summary_msg = {
                    "role": "system",
                    "content": f"[Previous context summary]\n{summary}"
                }
                return system_msgs + [summary_msg] + recent_msgs
        
        return system_msgs + recent_msgs
    
    def _generate_summary(self, messages: List[dict]) -> Optional[str]:
        """Generate LLM-powered summary of messages (replaces naive user-message extraction)."""
        try:
            from h_agent.memory.summarizer import SmartSummarizer
            summarizer = SmartSummarizer()
            return summarizer.summarize(messages)
        except Exception:
            # Fallback: extract user messages only
            user_msgs = [m.get("content", "") for m in messages if m.get("role") == "user"]
            if user_msgs:
                return "User asked: " + "; ".join(user_msgs[-3:])
            return None
    
    def guard_api_call(self, messages: List[dict]) -> tuple:
        """
        保护 API 调用，返回 (处理后的消息, 压缩级别)。
        
        压缩级别:
          0 - 无压缩
          1 - 截断工具结果
          2 - 压缩历史
        """
        if not self.should_compact(messages):
            return messages, 0
        
        # 第一阶段：截断工具结果
        messages = self.truncate_tool_results(messages)
        if not self.should_compact(messages):
            return messages, 1
        
        # 第二阶段：压缩历史
        messages = self.compact_messages(messages)
        return messages, 2


# ============================================================
# Tools
# ============================================================

import subprocess

def tool_bash(command: str) -> str:
    try:
        r = subprocess.run(command, shell=True, cwd=WORKSPACE_DIR, capture_output=True, text=True, timeout=60)
        output = (r.stdout + r.stderr).strip()
        return output[:MAX_TOOL_OUTPUT] if output else "(no output)"
    except Exception as e:
        return f"Error: {e}"

def tool_read(file_path: str) -> str:
    try:
        path = WORKSPACE_DIR / file_path
        if not path.exists():
            return f"Error: File not found"
        return path.read_text()[:MAX_TOOL_OUTPUT]
    except Exception as e:
        return f"Error: {e}"

def tool_write(file_path: str, content: str) -> str:
    try:
        path = WORKSPACE_DIR / file_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return f"Wrote {len(content)} chars"
    except Exception as e:
        return f"Error: {e}"

def tool_background_run(command: str) -> str:
    from h_agent.features.tasks import background_runner
    task_id = background_runner.run(command)
    return task_id

def tool_check_background(task_id: str) -> str:
    from h_agent.features.tasks import background_runner
    result = background_runner.check(task_id)
    if result is None:
        return f"Error: Task {task_id} not found"
    if result["running"]:
        return f"Task {task_id} is running"
    return f"Task {task_id} completed with return code {result['return_code']}\n{result['output']}"

def tool_task_create(title: str, description: str = "", priority: str = "medium") -> str:
    from h_agent.features.tasks import task_manager
    task_id = task_manager.create(title, description, priority)
    return task_id

def tool_task_get(task_id: str) -> str:
    from h_agent.features.tasks import task_manager
    task = task_manager.get(task_id)
    if task is None:
        return f"Error: Task {task_id} not found"
    import json
    return json.dumps(task, indent=2, ensure_ascii=False)

def tool_task_update(task_id: str, status: str = None, owner: str = None) -> str:
    from h_agent.features.tasks import task_manager
    success = task_manager.update(task_id, status, owner)
    if not success:
        return f"Error: Task {task_id} not found"
    return f"Task {task_id} updated"

def tool_task_list() -> str:
    from h_agent.features.tasks import task_manager
    tasks = task_manager.list_all()
    if not tasks:
        return "No tasks"
    import json
    return json.dumps(tasks, indent=2, ensure_ascii=False)

def tool_edit_file(file_path: str, old_text: str, new_text: str) -> str:
    try:
        path = WORKSPACE_DIR / file_path
        if not path.exists():
            return f"Error: File not found"
        content = path.read_text(encoding="utf-8")
        if old_text not in content:
            return f"Error: Text not found"
        if content.count(old_text) > 1:
            return f"Error: Multiple matches ({content.count(old_text)} found). Be more specific."
        path.write_text(content.replace(old_text, new_text, 1), encoding="utf-8")
        return f"Edited successfully"
    except Exception as e:
        return f"Error: {e}"

def tool_todo_write(todos: List[dict]) -> str:
    global _global_agent_id
    try:
        todo_dir = Path.home() / ".h-agent" / _global_agent_id
        todo_dir.mkdir(parents=True, exist_ok=True)
        todo_file = todo_dir / "todos.json"
        todo_file.write_text(json.dumps(todos, indent=2, ensure_ascii=False), encoding="utf-8")
        return f"Saved {len(todos)} todos"
    except Exception as e:
        return f"Error: {e}"

def tool_compress() -> str:
    global _global_context_guard, _global_session_store
    if _global_context_guard is None or _global_session_store is None:
        return "Error: No active session"
    try:
        messages = _global_session_store.load_session()
        before_count = len(messages)
        compacted = _global_context_guard.compact_messages(messages)
        after_count = len(compacted)
        removed = before_count - after_count
        return f"Compressed {before_count} messages to {after_count} ({removed} removed)"
    except Exception as e:
        return f"Error: {e}"


def tool_delegate(task: str, context: str = "") -> str:
    """
    Spawn a subagent with fresh context to handle a focused task.
    The subagent shares the filesystem but not conversation history.
    Only the result is returned to the parent - context stays clean.
    
    Args:
        task: The task for the subagent to complete
        context: Additional context (file paths, previous findings, etc.)
    """
    try:
        result = run_subagent(task=task, context=context)
        return json.dumps({
            "success": result.success,
            "result": result.content,
            "steps": result.steps,
            "error": result.error
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


TOOLS = [
    {"type": "function", "function": {"name": "bash", "description": "Run shell command",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "read", "description": "Read file",
        "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}}, "required": ["file_path"]}}},
    {"type": "function", "function": {"name": "write", "description": "Write file",
        "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}, "content": {"type": "string"}}, "required": ["file_path", "content"]}}},
    {"type": "function", "function": {"name": "background_run", "description": "Run command in background thread.",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "check_background", "description": "Check background task status.",
        "parameters": {"type": "object", "properties": {"task_id": {"type": "string"}}, "required": ["task_id"]}}},
    {"type": "function", "function": {"name": "task_create", "description": "Create a persistent file task.",
        "parameters": {"type": "object", "properties": {"title": {"type": "string"}, "description": {"type": "string"}, "priority": {"type": "string"}}, "required": ["title"]}}},
    {"type": "function", "function": {"name": "task_get", "description": "Get task details by ID.",
        "parameters": {"type": "object", "properties": {"task_id": {"type": "string"}}, "required": ["task_id"]}}},
    {"type": "function", "function": {"name": "task_update", "description": "Update task status or details.",
        "parameters": {"type": "object", "properties": {"task_id": {"type": "string"}, "status": {"type": "string"}, "owner": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "task_list", "description": "List all tasks.",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "edit_file", "description": "Replace exact text in file.",
        "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}, "old_text": {"type": "string"}, "new_text": {"type": "string"}}, "required": ["file_path", "old_text", "new_text"]}}},
    {"type": "function", "function": {"name": "TodoWrite", "description": "Update task tracking list.",
        "parameters": {"type": "object", "properties": {"todos": {"type": "array", "items": {"type": "object", "properties": {"content": {"type": "string"}, "status": {"type": "string", "enum": ["in_progress", "completed", "pending"]}, "priority": {"type": "string", "enum": ["high", "medium", "low"]}}}}}, "required": ["todos"]}}},
    {"type": "function", "function": {"name": "compress", "description": "Manually compress conversation context.",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "delegate", "description": "Spawn a subagent with fresh context. Use for complex analysis, file exploration, or parallel work. The subagent shares filesystem but not conversation history.",
        "parameters": {"type": "object", "properties": {"task": {"type": "string", "description": "The task for the subagent"}, "context": {"type": "string", "description": "Additional context (file paths, previous findings)"}}, "required": ["task"]}}},
]

TOOL_HANDLERS = {
    "bash": tool_bash,
    "read": tool_read,
    "write": tool_write,
    "background_run": tool_background_run,
    "check_background": tool_check_background,
    "task_create": tool_task_create,
    "task_get": tool_task_get,
    "task_update": tool_task_update,
    "task_list": tool_task_list,
    "edit_file": tool_edit_file,
    "TodoWrite": tool_todo_write,
    "compress": tool_compress,
    "delegate": tool_delegate,
}


def execute_tool_call(tool_call) -> str:
    args = json.loads(tool_call.function.arguments)
    return TOOL_HANDLERS[tool_call.function.name](**args)


# ============================================================
# Agent Loop with Sessions
# ============================================================

class SessionAwareAgent:
    """带会话持久化的 Agent。"""
    
    def __init__(self, agent_id: str = "default"):
        global _global_agent_id, _global_context_guard, _global_session_store
        self.agent_id = agent_id
        self.session_store = SessionStore(agent_id)
        self.context_guard = ContextGuard()
        _global_agent_id = agent_id
        _global_context_guard = self.context_guard
        _global_session_store = self.session_store
    
    def get_system_prompt(self) -> str:
        return f"You are a helpful AI assistant at {WORKSPACE_DIR}. Use tools to help the user."
    
    def run(self, user_input: str, session_id: str = None) -> str:
        """运行一轮对话。"""
        # 加载或创建会话
        if session_id:
            self.session_store.current_session_id = session_id
        elif not self.session_store.current_session_id:
            self.session_store.create_session()
        
        # 加载历史消息
        messages = self.session_store.load_session()
        
        # 添加用户消息
        messages.append({"role": "user", "content": user_input})
        
        # 保护上下文
        messages, compact_level = self.context_guard.guard_api_call(messages)
        if compact_level > 0:
            print(f"\033[33m[Context compacted: level {compact_level}]\033[0m")
        
        # 添加系统提示
        messages = [{"role": "system", "content": self.get_system_prompt()}] + messages
        
        # Agent 循环
        while True:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                max_tokens=4096,
            )
            
            message = response.choices[0].message
            messages.append({"role": "assistant", "content": message.content, "tool_calls": message.tool_calls})
            
            if not message.tool_calls:
                # 保存并返回
                self.session_store.save_turn("user", user_input)
                self.session_store.save_turn("assistant", message.content)
                return message.content or ""
            
            # 执行工具
            for tool_call in message.tool_calls:
                result = execute_tool_call(tool_call)
                messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
    
    def list_sessions(self) -> List[dict]:
        """列出会话。"""
        return self.session_store.get_recent_sessions()
    
    def switch_session(self, session_id: str) -> bool:
        """切换会话。"""
        if session_id in self.session_store._index:
            self.session_store.current_session_id = session_id
            return True
        return False
    
    def new_session(self) -> str:
        """创建新会话。"""
        return self.session_store.create_session()


def main():
    print(f"\033[36mOpenAI Agent Harness - c03 (Sessions)\033[0m")
    print(f"Model: {MODEL}")
    print(f"Workspace: {WORKSPACE_DIR}")
    print("\nCommands: 'sessions' to list, 'new' for new session, 'switch <id>' to switch")
    print("Type 'quit' to exit\n")
    
    agent = SessionAwareAgent()
    
    while True:
        try:
            user_input = input("\033[36m>> \033[0m").strip()
        except (EOFError, KeyboardInterrupt):
            break
        
        if not user_input:
            continue
        
        if user_input.lower() == "quit":
            break
        
        if user_input.lower() == "sessions":
            sessions = agent.list_sessions()
            for s in sessions:
                print(f"  {s['session_id']}: {s['message_count']} msgs, updated {s['updated_at'][:19]}")
            continue
        
        if user_input.lower() == "new":
            session_id = agent.new_session()
            print(f"Created session: {session_id}")
            continue
        
        if user_input.lower().startswith("switch "):
            session_id = user_input[7:].strip()
            if agent.switch_session(session_id):
                print(f"Switched to: {session_id}")
            else:
                print(f"Session not found: {session_id}")
            continue
        
        # 正常对话
        response = agent.run(user_input)
        print(f"\n{response}\n")


if __name__ == "__main__":
    main()
