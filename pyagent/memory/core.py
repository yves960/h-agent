"""
Memory - 记忆和会话管理
"""

import os
import json
import uuid
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum


# ============================================================
# Session Store
# ============================================================

class SessionStore:
    """JSONL 持久化会话存储。"""
    
    def __init__(self, agent_id: str = "default", base_dir: str = None):
        self.agent_id = agent_id
        self.base_dir = Path(base_dir or ".agent_workspace/sessions") / agent_id
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self.base_dir / "index.json"
        self._index: Dict[str, dict] = self._load_index()
        self.current_session_id: Optional[str] = None
    
    def _load_index(self) -> Dict[str, dict]:
        if self._index_path.exists():
            try:
                return json.loads(self._index_path.read_text(encoding="utf-8"))
            except:
                return {}
        return {}
    
    def _save_index(self):
        self._index_path.parent.mkdir(parents=True, exist_ok=True)
        self._index_path.write_text(
            json.dumps(self._index, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
    
    def _session_path(self, session_id: str) -> Path:
        return self.base_dir / f"{session_id}.jsonl"
    
    def create_session(self) -> str:
        """创建新会话。"""
        session_id = f"sess-{uuid.uuid4().hex[:8]}"
        now = datetime.now().isoformat()
        
        self._index[session_id] = {
            "session_id": session_id,
            "agent_id": self.agent_id,
            "created_at": now,
            "updated_at": now,
            "message_count": 0,
        }
        self._save_index()
        
        # 创建空的 JSONL 文件
        self._session_path(session_id).touch()
        self.current_session_id = session_id
        
        return session_id
    
    def load_session(self, session_id: str = None) -> List[dict]:
        """加载会话历史。"""
        if session_id is None:
            session_id = self.current_session_id
        
        if not session_id or session_id not in self._index:
            return []
        
        messages = []
        session_file = self._session_path(session_id)
        
        if session_file.exists():
            with open(session_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            messages.append(json.loads(line))
                        except:
                            pass
        
        return messages
    
    def save_turn(self, role: str, content: Any, session_id: str = None):
        """保存一轮对话。"""
        if session_id is None:
            session_id = self.current_session_id
        
        if not session_id:
            session_id = self.create_session()
        
        turn = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        
        # 追加到 JSONL
        session_file = self._session_path(session_id)
        with open(session_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(turn, ensure_ascii=False) + "\n")
        
        # 更新索引
        if session_id in self._index:
            self._index[session_id]["message_count"] += 1
            self._index[session_id]["updated_at"] = datetime.now().isoformat()
            self._save_index()
    
    def list_sessions(self, limit: int = 10) -> List[dict]:
        """列出最近会话。"""
        sessions = sorted(
            self._index.values(),
            key=lambda x: x.get("updated_at", ""),
            reverse=True
        )
        return sessions[:limit]
    
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
# Memory Store
# ============================================================

class MemoryStore:
    """键值记忆存储。"""
    
    def __init__(self, agent_id: str = "default", memory_dir: str = None):
        self.agent_id = agent_id
        self.memory_dir = Path(memory_dir or ".agent_workspace/memory") / agent_id
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self._memory: Dict[str, str] = {}
        self._load()
    
    def _load(self):
        """加载记忆文件。"""
        for mem_file in self.memory_dir.glob("*.md"):
            key = mem_file.stem
            self._memory[key] = mem_file.read_text(encoding="utf-8")
    
    def set(self, key: str, value: str):
        """设置记忆。"""
        self._memory[key] = value
        mem_file = self.memory_dir / f"{key}.md"
        mem_file.write_text(value, encoding="utf-8")
    
    def get(self, key: str) -> str:
        """获取记忆。"""
        return self._memory.get(key, "")
    
    def delete(self, key: str) -> bool:
        """删除记忆。"""
        if key in self._memory:
            del self._memory[key]
            mem_file = self.memory_dir / f"{key}.md"
            if mem_file.exists():
                mem_file.unlink()
            return True
        return False
    
    def search(self, query: str) -> List[str]:
        """搜索记忆。"""
        results = []
        query_lower = query.lower()
        
        for key, content in self._memory.items():
            if query_lower in key.lower() or query_lower in content.lower():
                results.append(f"[{key}]\n{content[:500]}")
        
        return results
    
    def list_keys(self) -> List[str]:
        """列出所有键。"""
        return list(self._memory.keys())
    
    def format_for_prompt(self) -> str:
        """格式化为提示词。"""
        if not self._memory:
            return ""
        
        lines = ["# Memory\n"]
        for key, content in self._memory.items():
            lines.append(f"## {key}\n{content}\n")
        
        return "\n".join(lines)


# ============================================================
# Context Guard
# ============================================================

class ContextGuard:
    """上下文溢出保护。"""
    
    def __init__(self, safe_limit: int = 180000, max_tool_output: int = 50000):
        self.safe_limit = safe_limit
        self.max_tool_output = max_tool_output
    
    def estimate_tokens(self, messages: List[dict]) -> int:
        """估算 token 数量。"""
        total = 0
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                total += len(content)
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        total += len(str(block))
        return total // 4  # 粗略估算
    
    def should_compact(self, messages: List[dict]) -> bool:
        """检查是否需要压缩。"""
        return self.estimate_tokens(messages) > self.safe_limit
    
    def truncate_tool_results(self, messages: List[dict]) -> List[dict]:
        """截断工具结果。"""
        result = []
        for msg in messages:
            if msg.get("role") == "tool":
                content = msg.get("content", "")
                if len(content) > self.max_tool_output:
                    half = self.max_tool_output // 2
                    msg = {
                        **msg,
                        "content": content[:half] + f"\n... [truncated]\n" + content[-half:]
                    }
            result.append(msg)
        return result
    
    def compact_messages(self, messages: List[dict]) -> tuple:
        """压缩消息，返回 (处理后的消息, 压缩级别)。"""
        if not self.should_compact(messages):
            return messages, 0
        
        # 第一阶段：截断工具结果
        messages = self.truncate_tool_results(messages)
        if not self.should_compact(messages):
            return messages, 1
        
        # 第二阶段：压缩历史
        if len(messages) > 10:
            # 保留系统消息和最近消息
            system_msgs = [m for m in messages if m.get("role") == "system"]
            recent_msgs = messages[-8:]
            
            # 生成摘要
            middle = messages[:-8]
            if middle:
                summary = self._generate_summary(middle)
                if summary:
                    summary_msg = {
                        "role": "system",
                        "content": f"[Previous context summary]\n{summary}"
                    }
                    return system_msgs + [summary_msg] + recent_msgs, 2
        
        return messages, 2
    
    def _generate_summary(self, messages: List[dict]) -> str:
        """生成摘要。"""
        user_msgs = [m.get("content", "") for m in messages if m.get("role") == "user"]
        if user_msgs:
            return "User asked: " + "; ".join(str(m)[:100] for m in user_msgs[-5:])
        return ""