#!/usr/bin/env python3
"""
h_agent/tests/test_tools_s02_s06.py - Tests for s02-s06 tools

Tests cover:
- edit_file: text replacement in files
- TodoWrite: task tracking list persistence
- compress: manual context compression
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import h_agent.features.sessions as sessions


class TestToolEditFile:
    """Tests for edit_file tool."""

    def test_edit_file_success(self, tmp_path):
        sessions.WORKSPACE_DIR = tmp_path
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world", encoding="utf-8")

        result = sessions.tool_edit_file("test.txt", "hello", "goodbye")

        assert result == "Edited successfully"
        assert test_file.read_text(encoding="utf-8") == "goodbye world"

    def test_edit_file_not_found(self, tmp_path):
        sessions.WORKSPACE_DIR = tmp_path

        result = sessions.tool_edit_file("nonexistent.txt", "old", "new")

        assert "Error" in result
        assert "not found" in result.lower()

    def test_edit_file_text_not_found(self, tmp_path):
        sessions.WORKSPACE_DIR = tmp_path
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world", encoding="utf-8")

        result = sessions.tool_edit_file("test.txt", "goodbye", "new")

        assert "Error" in result
        assert "not found" in result.lower()

    def test_edit_file_multiple_matches_error(self, tmp_path):
        sessions.WORKSPACE_DIR = tmp_path
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello hello hello", encoding="utf-8")

        result = sessions.tool_edit_file("test.txt", "hello", "hi")

        assert "Error" in result
        assert "Multiple matches" in result

    def test_edit_file_single_match_replacement(self, tmp_path):
        sessions.WORKSPACE_DIR = tmp_path
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello hello hello", encoding="utf-8")

        result = sessions.tool_edit_file("test.txt", "hello", "hi")

        assert "Multiple matches" in result


class TestToolTodoWrite:
    """Tests for TodoWrite tool."""

    def test_todo_write_creates_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sessions, "_global_agent_id", "test_agent")
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        todos = [
            {"content": "Test task", "status": "pending", "priority": "high"}
        ]

        result = sessions.tool_todo_write(todos)

        assert "Saved 1 todos" in result
        todo_file = tmp_path / ".h-agent" / "test_agent" / "todos.json"
        assert todo_file.exists()
        saved = json.loads(todo_file.read_text(encoding="utf-8"))
        assert len(saved) == 1
        assert saved[0]["content"] == "Test task"

    def test_todo_write_multiple_todos(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sessions, "_global_agent_id", "test_agent")
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        todos = [
            {"content": "Task 1", "status": "in_progress", "priority": "high"},
            {"content": "Task 2", "status": "pending", "priority": "medium"},
            {"content": "Task 3", "status": "completed", "priority": "low"},
        ]

        result = sessions.tool_todo_write(todos)

        assert "Saved 3 todos" in result
        todo_file = tmp_path / ".h-agent" / "test_agent" / "todos.json"
        saved = json.loads(todo_file.read_text(encoding="utf-8"))
        assert len(saved) == 3

    def test_todo_write_overwrites_existing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sessions, "_global_agent_id", "test_agent")
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        todo_dir = tmp_path / ".h-agent" / "test_agent"
        todo_dir.mkdir(parents=True, exist_ok=True)
        old_file = todo_dir / "todos.json"
        old_file.write_text(json.dumps([{"content": "Old task"}]), encoding="utf-8")

        todos = [{"content": "New task", "status": "pending", "priority": "high"}]
        sessions.tool_todo_write(todos)

        saved = json.loads(old_file.read_text(encoding="utf-8"))
        assert len(saved) == 1
        assert saved[0]["content"] == "New task"


class TestToolCompress:
    """Tests for compress tool."""

    def test_compress_no_session(self, monkeypatch):
        monkeypatch.setattr(sessions, "_global_context_guard", None)
        monkeypatch.setattr(sessions, "_global_session_store", None)

        result = sessions.tool_compress()

        assert "Error" in result
        assert "No active session" in result

    def test_compress_with_messages(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sessions, "_global_agent_id", "test_agent")

        mock_store = MagicMock()
        mock_store.load_session.return_value = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Message 1"},
            {"role": "assistant", "content": "Response 1"},
            {"role": "user", "content": "Message 2"},
            {"role": "assistant", "content": "Response 2"},
            {"role": "user", "content": "Message 3"},
            {"role": "assistant", "content": "Response 3"},
            {"role": "user", "content": "Message 4"},
            {"role": "assistant", "content": "Response 4"},
        ]
        monkeypatch.setattr(sessions, "_global_session_store", mock_store)

        mock_guard = MagicMock()
        mock_guard.compact_messages.return_value = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "system", "content": "[Previous context summary]\nUser asked: Message 1; Message 2; Message 3"},
            {"role": "user", "content": "Message 4"},
            {"role": "assistant", "content": "Response 4"},
        ]
        monkeypatch.setattr(sessions, "_global_context_guard", mock_guard)

        result = sessions.tool_compress()

        assert "Compressed 9 messages to 4" in result
        assert "(5 removed)" in result
        mock_guard.compact_messages.assert_called_once()


class TestSessionAwareAgentGlobals:
    """Tests that SessionAwareAgent sets globals correctly."""

    def test_agent_sets_globals(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sessions, "WORKSPACE_DIR", tmp_path)

        agent = sessions.SessionAwareAgent(agent_id="my_agent")

        assert sessions._global_agent_id == "my_agent"
        assert sessions._global_context_guard is agent.context_guard
        assert sessions._global_session_store is agent.session_store


class TestToolDefinitions:
    """Verify tool definitions are correctly formatted."""

    def test_edit_file_in_tools(self):
        tool_names = [t["function"]["name"] for t in sessions.TOOLS]
        assert "edit_file" in tool_names

    def test_TodoWrite_in_tools(self):
        tool_names = [t["function"]["name"] for t in sessions.TOOLS]
        assert "TodoWrite" in tool_names

    def test_compress_in_tools(self):
        tool_names = [t["function"]["name"] for t in sessions.TOOLS]
        assert "compress" in tool_names

    def test_edit_file_in_handlers(self):
        assert "edit_file" in sessions.TOOL_HANDLERS

    def test_TodoWrite_in_handlers(self):
        assert "TodoWrite" in sessions.TOOL_HANDLERS

    def test_compress_in_handlers(self):
        assert "compress" in sessions.TOOL_HANDLERS


class TestEditFileParameterSchema:
    """Verify tool parameter schemas match requirements."""

    def test_edit_file_params(self):
        tool = next(t for t in sessions.TOOLS if t["function"]["name"] == "edit_file")
        params = tool["function"]["parameters"]["properties"]
        required = tool["function"]["parameters"]["required"]

        assert "file_path" in params
        assert "old_text" in params
        assert "new_text" in params
        assert set(required) == {"file_path", "old_text", "new_text"}

    def test_TodoWrite_params(self):
        tool = next(t for t in sessions.TOOLS if t["function"]["name"] == "TodoWrite")
        params = tool["function"]["parameters"]["properties"]
        required = tool["function"]["parameters"]["required"]

        assert "todos" in params
        assert set(required) == {"todos"}

    def test_compress_params(self):
        tool = next(t for t in sessions.TOOLS if t["function"]["name"] == "compress")
        params = tool["function"]["parameters"]["properties"]
        assert params == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
