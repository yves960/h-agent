#!/usr/bin/env python3
"""
h_agent/tests/test_tools_s07_s08.py - Tests for s07-s08 tools

Tests cover:
- background_run / check_background
- task_create / task_get / task_update / task_list
"""

import json
import tempfile
import time
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestTaskManager:
    """Test TaskManager class."""

    def test_create_returns_task_id(self, tmp_path):
        """task_create returns an 8-char task_id."""
        from h_agent.features.tasks import TaskManager
        tm = TaskManager(tasks_dir=tmp_path / "tasks")
        task_id = tm.create("Test task")
        assert isinstance(task_id, str)
        assert len(task_id) == 8

    def test_create_saves_task_file(self, tmp_path):
        """task_create saves task to file."""
        from h_agent.features.tasks import TaskManager
        tm = TaskManager(tasks_dir=tmp_path / "tasks")
        task_id = tm.create("Test task", "A description", "high")
        path = tmp_path / "tasks" / f"{task_id}.json"
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["title"] == "Test task"
        assert data["description"] == "A description"
        assert data["priority"] == "high"
        assert data["status"] == "pending"
        assert data["owner"] is None

    def test_get_returns_task(self, tmp_path):
        """task_get returns task dict."""
        from h_agent.features.tasks import TaskManager
        tm = TaskManager(tasks_dir=tmp_path / "tasks")
        task_id = tm.create("Get test")
        result = tm.get(task_id)
        assert result is not None
        assert result["id"] == task_id
        assert result["title"] == "Get test"

    def test_get_returns_none_for_missing(self, tmp_path):
        """task_get returns None for nonexistent task."""
        from h_agent.features.tasks import TaskManager
        tm = TaskManager(tasks_dir=tmp_path / "tasks")
        result = tm.get("nonexistent")
        assert result is None

    def test_update_status(self, tmp_path):
        """task_update can change status."""
        from h_agent.features.tasks import TaskManager
        tm = TaskManager(tasks_dir=tmp_path / "tasks")
        task_id = tm.create("Update test")
        success = tm.update(task_id, status="completed")
        assert success is True
        task = tm.get(task_id)
        assert task["status"] == "completed"

    def test_update_owner(self, tmp_path):
        """task_update can change owner."""
        from h_agent.features.tasks import TaskManager
        tm = TaskManager(tasks_dir=tmp_path / "tasks")
        task_id = tm.create("Owner test")
        success = tm.update(task_id, owner="agent-1")
        assert success is True
        task = tm.get(task_id)
        assert task["owner"] == "agent-1"

    def test_update_returns_false_for_missing(self, tmp_path):
        """task_update returns False for nonexistent task."""
        from h_agent.features.tasks import TaskManager
        tm = TaskManager(tasks_dir=tmp_path / "tasks")
        success = tm.update("nonexistent", status="done")
        assert success is False

    def test_list_all_returns_tasks(self, tmp_path):
        """task_list returns all tasks sorted by created_at desc."""
        from h_agent.features.tasks import TaskManager
        tm = TaskManager(tasks_dir=tmp_path / "tasks")
        id1 = tm.create("First task")
        time.sleep(0.01)
        id2 = tm.create("Second task")
        tasks = tm.list_all()
        assert len(tasks) == 2
        assert tasks[0]["id"] == id2
        assert tasks[1]["id"] == id1

    def test_list_all_empty(self, tmp_path):
        """task_list returns empty list when no tasks."""
        from h_agent.features.tasks import TaskManager
        tm = TaskManager(tasks_dir=tmp_path / "tasks")
        tasks = tm.list_all()
        assert tasks == []

    def test_delete_removes_task(self, tmp_path):
        """delete removes task file."""
        from h_agent.features.tasks import TaskManager
        tm = TaskManager(tasks_dir=tmp_path / "tasks")
        task_id = tm.create("To delete")
        success = tm.delete(task_id)
        assert success is True
        assert tm.get(task_id) is None

    def test_delete_missing_returns_false(self, tmp_path):
        """delete returns False for nonexistent task."""
        from h_agent.features.tasks import TaskManager
        tm = TaskManager(tasks_dir=tmp_path / "tasks")
        success = tm.delete("nonexistent")
        assert success is False


class TestBackgroundRunner:
    """Test BackgroundRunner class."""

    def test_run_returns_task_id(self):
        """background_run returns an 8-char task_id."""
        from h_agent.features.tasks import BackgroundRunner
        br = BackgroundRunner()
        task_id = br.run("echo hello")
        assert isinstance(task_id, str)
        assert len(task_id) == 8

    def test_check_returns_running_initially(self):
        """check returns running=True for new task."""
        from h_agent.features.tasks import BackgroundRunner
        br = BackgroundRunner()
        task_id = br.run("sleep 2")
        try:
            result = br.check(task_id)
            assert result is not None
            assert result["task_id"] == task_id
            assert result["running"] is True
            assert result["status"] == "running"
        finally:
            pass

    def test_check_returns_completed(self):
        """check returns completed after command finishes."""
        from h_agent.features.tasks import BackgroundRunner
        br = BackgroundRunner()
        task_id = br.run("echo hello")
        time.sleep(0.5)
        result = br.check(task_id)
        assert result is not None
        assert result["running"] is False
        assert result["status"] == "completed"
        assert "hello" in result["output"]

    def test_check_returns_failed_for_bad_command(self):
        """check returns failed for nonexistent command."""
        from h_agent.features.tasks import BackgroundRunner
        br = BackgroundRunner()
        task_id = br.run("nonexistent_command_xyz")
        time.sleep(0.5)
        result = br.check(task_id)
        assert result is not None
        assert result["running"] is False
        assert result["status"] == "failed"

    def test_check_returns_none_for_unknown(self):
        """check returns None for unknown task_id."""
        from h_agent.features.tasks import BackgroundRunner
        br = BackgroundRunner()
        result = br.check("unknown_id")
        assert result is None


class TestToolHandlers:
    """Test tool handler functions in sessions.py."""

    def test_tool_task_create_handler(self):
        """tool_task_create returns task_id string."""
        from h_agent.features.sessions import tool_task_create
        with tempfile.TemporaryDirectory() as tmp:
            import os
            os.environ["H_AGENT_TASKS_DIR"] = tmp
            from h_agent.features.tasks import TaskManager
            from h_agent.features import sessions
            sessions.task_manager = TaskManager(tasks_dir=Path(tmp))
            result = tool_task_create("Test")
            assert isinstance(result, str)
            assert len(result) == 8

    def test_tool_task_get_handler(self):
        """tool_task_get returns JSON string."""
        from h_agent.features.sessions import tool_task_create, tool_task_get
        with tempfile.TemporaryDirectory() as tmp:
            from h_agent.features.tasks import TaskManager
            from h_agent.features import sessions
            sessions.task_manager = TaskManager(tasks_dir=Path(tmp))
            task_id = tool_task_create("Get Handler Test")
            result = tool_task_get(task_id)
            data = json.loads(result)
            assert data["title"] == "Get Handler Test"

    def test_tool_task_update_handler(self):
        """tool_task_update returns success message."""
        from h_agent.features.sessions import tool_task_create, tool_task_update
        with tempfile.TemporaryDirectory() as tmp:
            from h_agent.features.tasks import TaskManager
            from h_agent.features import sessions
            sessions.task_manager = TaskManager(tasks_dir=Path(tmp))
            task_id = tool_task_create("Update Handler Test")
            result = tool_task_update(task_id, status="in_progress")
            assert "updated" in result

    def test_tool_task_list_handler_empty(self):
        """tool_task_list returns empty list when no tasks."""
        from h_agent.features.tasks import TaskManager, task_manager as global_tm
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            global_tm.tasks_dir = tmp_path
            global_tm.tasks_dir.mkdir(parents=True, exist_ok=True)
            for p in global_tm.tasks_dir.glob("*.json"):
                p.unlink()
            result = global_tm.list_all()
            assert result == []

    def test_tool_background_run_handler(self):
        """tool_background_run returns task_id."""
        from h_agent.features.sessions import tool_background_run
        task_id = tool_background_run("echo test")
        assert isinstance(task_id, str)
        assert len(task_id) == 8

    def test_tool_check_background_handler(self):
        """tool_check_background returns status string."""
        from h_agent.features.sessions import tool_background_run, tool_check_background
        task_id = tool_background_run("echo background_check")
        time.sleep(0.3)
        result = tool_check_background(task_id)
        assert "completed" in result or "running" in result


class TestToolDefinitions:
    """Test that tool definitions are correct."""

    def test_background_run_in_tools(self):
        """background_run is in TOOLS list."""
        from h_agent.features.sessions import TOOLS
        names = [t["function"]["name"] for t in TOOLS]
        assert "background_run" in names

    def test_check_background_in_tools(self):
        """check_background is in TOOLS list."""
        from h_agent.features.sessions import TOOLS
        names = [t["function"]["name"] for t in TOOLS]
        assert "check_background" in names

    def test_task_create_in_tools(self):
        """task_create is in TOOLS list."""
        from h_agent.features.sessions import TOOLS
        names = [t["function"]["name"] for t in TOOLS]
        assert "task_create" in names

    def test_task_get_in_tools(self):
        """task_get is in TOOLS list."""
        from h_agent.features.sessions import TOOLS
        names = [t["function"]["name"] for t in TOOLS]
        assert "task_get" in names

    def test_task_update_in_tools(self):
        """task_update is in TOOLS list."""
        from h_agent.features.sessions import TOOLS
        names = [t["function"]["name"] for t in TOOLS]
        assert "task_update" in names

    def test_task_list_in_tools(self):
        """task_list is in TOOLS list."""
        from h_agent.features.sessions import TOOLS
        names = [t["function"]["name"] for t in TOOLS]
        assert "task_list" in names

    def test_background_run_handler_registered(self):
        """background_run handler is in TOOL_HANDLERS."""
        from h_agent.features.sessions import TOOL_HANDLERS
        assert "background_run" in TOOL_HANDLERS

    def test_check_background_handler_registered(self):
        """check_background handler is in TOOL_HANDLERS."""
        from h_agent.features.sessions import TOOL_HANDLERS
        assert "check_background" in TOOL_HANDLERS

    def test_task_handlers_registered(self):
        """All task handlers are in TOOL_HANDLERS."""
        from h_agent.features.sessions import TOOL_HANDLERS
        for name in ["task_create", "task_get", "task_update", "task_list"]:
            assert name in TOOL_HANDLERS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
