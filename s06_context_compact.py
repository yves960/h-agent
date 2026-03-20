#!/usr/bin/env python3
"""
s06_context_compact.py - Context Compression

Context will fill up; you need a way to make room.

Three-layer compression strategy:
1. Truncate old tool_results (keep summaries)
2. Generate conversation summary periodically
3. Persist tasks to disk, remove from context

This enables infinite-length sessions.
"""

import os
import json
import hashlib
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from pathlib import Path

load_dotenv(override=True)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "sk-dummy"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
)
MODEL = os.getenv("MODEL_ID", "gpt-4o")

WORK_DIR = os.getcwd()
COMPACT_DIR = Path(WORK_DIR) / ".agent_context"
COMPACT_DIR.mkdir(exist_ok=True)


# ============================================================
# Context Compression System
# ============================================================

class ContextManager:
    """Manages context compression and persistence."""
    
    def __init__(self, max_messages: int = 50, max_tool_result_chars: int = 5000):
        self.max_messages = max_messages
        self.max_tool_result_chars = max_tool_result_chars
        self.summaries: List[str] = []
    
    def count_tokens_estimate(self, messages: List[dict]) -> int:
        """Estimate token count (rough: 1 token ≈ 4 chars)."""
        total = 0
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                total += len(content)
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        total += len(str(block))
        return total // 4
    
    def should_compact(self, messages: List[dict]) -> bool:
        """Check if context needs compression."""
        return len(messages) > self.max_messages
    
    def truncate_tool_results(self, messages: List[dict]) -> List[dict]:
        """Truncate long tool results, keeping beginning and end."""
        result = []
        for msg in messages:
            if msg.get("role") == "tool":
                content = msg.get("content", "")
                if len(content) > self.max_tool_result_chars:
                    half = self.max_tool_result_chars // 2
                    truncated = (
                        content[:half] + 
                        f"\n\n... [truncated {len(content) - self.max_tool_result_chars} chars] ...\n\n" +
                        content[-half:]
                    )
                    msg = {**msg, "content": truncated}
            result.append(msg)
        return result
    
    def generate_summary(self, messages: List[dict]) -> str:
        """Generate a summary of the conversation."""
        # 收集关键信息
        user_msgs = [m for m in messages if m.get("role") == "user"]
        assistant_msgs = [m for m in messages if m.get("role") == "assistant"]
        
        summary_parts = []
        summary_parts.append(f"Conversation: {len(user_msgs)} user messages, {len(assistant_msgs)} responses")
        
        # 提取用户的主要请求
        for msg in user_msgs[-5:]:  # 最近5条
            content = msg.get("content", "")
            if isinstance(content, str) and content:
                summary_parts.append(f"User: {content[:100]}...")
        
        return "\n".join(summary_parts)
    
    def compact(self, messages: List[dict]) -> List[dict]:
        """Apply compression to context."""
        if not self.should_compact(messages):
            return messages
        
        print(f"\033[36m🗜️ Compressing context ({len(messages)} messages)\033[0m")
        
        # 1. Truncate tool results
        messages = self.truncate_tool_results(messages)
        
        # 2. Generate summary for old messages
        if len(messages) > 20:
            old_messages = messages[:-10]
            recent_messages = messages[-10:]
            
            summary = self.generate_summary(old_messages)
            self.summaries.append(summary)
            
            # Save summary to file
            summary_file = COMPACT_DIR / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            summary_file.write_text(summary)
            
            # Keep only recent messages + summary as context
            messages = [
                {"role": "system", "content": f"[Previous context summarized]\n{summary}"}
            ] + recent_messages
        
        print(f"\033[36m✅ Compressed to {len(messages)} messages\033[0m")
        return messages
    
    def save_checkpoint(self, messages: List[dict], thread_id: str):
        """Save current context to disk."""
        checkpoint = {
            "thread_id": thread_id,
            "timestamp": datetime.now().isoformat(),
            "messages": messages,
            "summaries": self.summaries,
        }
        checkpoint_file = COMPACT_DIR / f"checkpoint_{thread_id}.json"
        checkpoint_file.write_text(json.dumps(checkpoint, indent=2, ensure_ascii=False))
    
    def load_checkpoint(self, thread_id: str) -> Optional[List[dict]]:
        """Load context from disk."""
        checkpoint_file = COMPACT_DIR / f"checkpoint_{thread_id}.json"
        if not checkpoint_file.exists():
            return None
        
        checkpoint = json.loads(checkpoint_file.read_text())
        self.summaries = checkpoint.get("summaries", [])
        return checkpoint.get("messages", [])


# Global context manager
context_manager = ContextManager()


# ============================================================
# Simplified Tools
# ============================================================

import subprocess
import glob as glob_module

def tool_bash(command: str) -> str:
    if any(d in command for d in ["rm -rf /", "mkfs"]):
        return "Error: Blocked"
    try:
        r = subprocess.run(command, shell=True, cwd=WORK_DIR, capture_output=True, text=True, timeout=60)
        return (r.stdout + r.stderr).strip()[:20000] or "(no output)"
    except Exception as e:
        return f"Error: {e}"

def tool_read(path: str) -> str:
    try:
        if not os.path.isabs(path):
            path = os.path.join(WORK_DIR, path)
        if not os.path.exists(path):
            return f"Error: Not found: {path}"
        return Path(path).read_text()[:10000]
    except Exception as e:
        return f"Error: {e}"

def tool_write(path: str, content: str) -> str:
    try:
        if not os.path.isabs(path):
            path = os.path.join(WORK_DIR, path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(content)
        return f"Wrote {len(content)} chars"
    except Exception as e:
        return f"Error: {e}"

def tool_edit(path: str, old_text: str, new_text: str) -> str:
    try:
        if not os.path.isabs(path):
            path = os.path.join(WORK_DIR, path)
        if not os.path.exists(path):
            return "Error: Not found"
        content = Path(path).read_text()
        if old_text not in content:
            return "Error: Not found in file"
        Path(path).write_text(content.replace(old_text, new_text))
        return "Edited"
    except Exception as e:
        return f"Error: {e}"

def tool_glob(pattern: str) -> str:
    matches = list(glob_module.glob(os.path.join(WORK_DIR, pattern), recursive=True))
    return '\n'.join(os.path.relpath(m, WORK_DIR) for m in matches) or "No files"

def tool_compact() -> str:
    """Force context compression."""
    return "Context will be compressed on next message."

def tool_save_context(thread_id: str) -> str:
    """Save current context to disk."""
    return f"Context saved for thread {thread_id}"


TOOLS = [
    {"type": "function", "function": {"name": "bash", "description": "Run shell command",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "read", "description": "Read file",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "write", "description": "Write file",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "edit", "description": "Edit file",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "old_text": {"type": "string"}, "new_text": {"type": "string"}}, "required": ["path", "old_text", "new_text"]}}},
    {"type": "function", "function": {"name": "glob", "description": "Find files",
        "parameters": {"type": "object", "properties": {"pattern": {"type": "string"}}, "required": ["pattern"]}}},
    {"type": "function", "function": {"name": "compact", "description": "Force context compression",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "save_context", "description": "Save context to disk",
        "parameters": {"type": "object", "properties": {"thread_id": {"type": "string"}}, "required": ["thread_id"]}}},
]

TOOL_HANDLERS = {
    "bash": tool_bash, "read": tool_read, "write": tool_write,
    "edit": tool_edit, "glob": tool_glob, "compact": tool_compact, "save_context": tool_save_context,
}


def execute_tool_call(tool_call) -> str:
    args = json.loads(tool_call.function.arguments)
    return TOOL_HANDLERS[tool_call.function.name](**args)


# ============================================================
# Agent Loop with Context Management
# ============================================================

def get_system_prompt() -> str:
    return f"""You are a coding agent at {WORK_DIR}.

Context is managed automatically. For long conversations, use:
- 'compact' to force compression
- 'save_context' to checkpoint progress

Act efficiently."""


def agent_loop(messages: List[dict], thread_id: str = "default"):
    """Agent loop with automatic context compression."""
    while True:
        # Check if we need to compact
        messages = context_manager.compact(messages)
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": get_system_prompt()}] + messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=8000,
        )
        
        message = response.choices[0].message
        messages.append({"role": "assistant", "content": message.content, "tool_calls": message.tool_calls})
        
        if not message.tool_calls:
            return messages
        
        for tool_call in message.tool_calls:
            print(f"\033[33m$ {tool_call.function.name}\033[0m")
            result = execute_tool_call(tool_call)
            
            if tool_call.function.name == "save_context":
                context_manager.save_checkpoint(messages, thread_id)
            
            print(result[:100] + ("..." if len(result) > 100 else ""))
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
    
    return messages


def main():
    print(f"\033[36mOpenAI Agent Harness - s06 (Context Compact)\033[0m")
    print(f"Model: {MODEL}")
    print(f"Max messages before compact: {context_manager.max_messages}")
    print(f"Context dir: {COMPACT_DIR}")
    print("\nType 'q' to quit, 'stats' for context stats\n")
    
    history = []
    thread_id = f"thread_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    while True:
        try:
            query = input("\033[36m>> \033[0m")
        except (EOFError, KeyboardInterrupt):
            break
        
        if query.strip().lower() == "q":
            break
        if query.strip().lower() == "stats":
            tokens = context_manager.count_tokens_estimate(history)
            print(f"Messages: {len(history)}, Est. tokens: {tokens}")
            continue
        
        history.append({"role": "user", "content": query})
        history = agent_loop(history, thread_id)
        
        if history[-1].get("content"):
            print(f"\n{history[-1]['content']}\n")


if __name__ == "__main__":
    main()