"""Tests for memory module."""
import os
import sys
import pytest
import tempfile

os.environ["OPENAI_API_KEY"] = "test"
os.environ["OPENAI_BASE_URL"] = "http://localhost:8000"
os.environ["MODEL_ID"] = "test-model"

from pyagent.memory import SessionStore, MemoryStore, ContextGuard


class TestSessionStore:
    """SessionStore tests."""
    
    def test_create_session(self, tmp_path):
        store = SessionStore("test", base_dir=str(tmp_path))
        session_id = store.create_session()
        
        assert session_id.startswith("sess-")
        assert store.current_session_id == session_id
    
    def test_save_and_load(self, tmp_path):
        store = SessionStore("test", base_dir=str(tmp_path))
        session_id = store.create_session()
        
        store.save_turn("user", "hello")
        store.save_turn("assistant", "hi there")
        
        messages = store.load_session()
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "hello"
    
    def test_list_sessions(self, tmp_path):
        store = SessionStore("test", base_dir=str(tmp_path))
        store.create_session()
        
        sessions = store.list_sessions()
        assert len(sessions) == 1
    
    def test_delete_session(self, tmp_path):
        store = SessionStore("test", base_dir=str(tmp_path))
        session_id = store.create_session()
        
        result = store.delete_session(session_id)
        assert result is True
        
        sessions = store.list_sessions()
        assert len(sessions) == 0


class TestMemoryStore:
    """MemoryStore tests."""
    
    def test_set_and_get(self, tmp_path):
        store = MemoryStore("test", memory_dir=str(tmp_path))
        store.set("key1", "value1")
        
        result = store.get("key1")
        assert result == "value1"
    
    def test_search(self, tmp_path):
        store = MemoryStore("test", memory_dir=str(tmp_path))
        store.set("project", "agent harness")
        store.set("author", "developer")
        
        results = store.search("agent")
        assert len(results) == 1
        assert "project" in results[0]
    
    def test_delete(self, tmp_path):
        store = MemoryStore("test", memory_dir=str(tmp_path))
        store.set("key1", "value1")
        
        result = store.delete("key1")
        assert result is True
        assert store.get("key1") == ""


class TestContextGuard:
    """ContextGuard tests."""
    
    def test_estimate_tokens(self):
        guard = ContextGuard()
        messages = [{"role": "user", "content": "x" * 1000}]
        tokens = guard.estimate_tokens(messages)
        assert tokens == 250  # 1000 / 4
    
    def test_truncate_tool_results(self):
        guard = ContextGuard(max_tool_output=100)
        messages = [
            {"role": "tool", "content": "x" * 200, "tool_call_id": "1"}
        ]
        result = guard.truncate_tool_results(messages)
        assert len(result[0]["content"]) < 200
    
    def test_compact_messages(self):
        guard = ContextGuard(safe_limit=100)
        messages = [
            {"role": "user", "content": "x" * 1000}
        ]
        compacted, level = guard.compact_messages(messages)
        assert level >= 0