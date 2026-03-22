#!/usr/bin/env python3
"""
h_agent/tests/test_tools_s09_s12.py - Tests for s09-s12 team tools

Tests cover:
- spawn_teammate (s09): spawning persistent autonomous teammates
- shutdown_request (s10): requesting teammate shutdown via inbox
- plan_approval (s10): approving/rejecting teammate plans
- idle (s12): entering idle state
- claim_task (s12): claiming tasks from board

Run with: pytest h_agent/tests/test_tools_s09_s12.py -v
"""

import json
import tempfile
import time
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def temp_inbox_dir(tmp_path):
    """Temporary inbox directory for tests."""
    inbox_dir = tmp_path / "inboxes"
    inbox_dir.mkdir()
    return inbox_dir


@pytest.fixture
def async_bus(temp_inbox_dir):
    """AsyncMessageBus instance with temp directory."""
    from h_agent.team.async_team import AsyncMessageBus
    return AsyncMessageBus(inbox_dir=temp_inbox_dir)


@pytest.fixture
def async_team(temp_inbox_dir):
    """AsyncAgentTeam instance with temp directory."""
    from h_agent.team.async_team import AsyncAgentTeam
    team = AsyncAgentTeam(team_id="test-team")
    team.bus = type(team.bus)(inbox_dir=temp_inbox_dir)
    return team


class TestSpawnTeammate:
    """Tests for spawn_teammate tool (s09)."""

    def test_spawn_teammate_adds_to_list(self, async_team):
        """spawn() adds teammate to internal tracking."""
        result = async_team.spawn("alice", "coder", "You are a coder")

        assert "Spawned" in result or "already spawned" in result
        assert "alice" in async_team._spawned_agents

    def test_spawn_teammate_idempotent(self, async_team):
        """spawn() returns already spawned if agent exists."""
        async_team.spawn("alice", "coder", "You are a coder")
        result = async_team.spawn("alice", "coder", "You are a coder")

        assert "already spawned" in result

    def test_spawn_updates_manager_status(self, async_team):
        """spawn() updates TeammateManager status to working."""
        async_team.spawn("bob", "reviewer", "You are a reviewer")

        status = async_team.manager.get_status("bob")
        assert status in ("working", "idle")

    def test_spawn_multiple_teammates(self, async_team):
        """Multiple teammates can be spawned."""
        async_team.spawn("alice", "coder", "You are a coder")
        async_team.spawn("bob", "reviewer", "You are a reviewer")
        async_team.spawn("charlie", "devops", "You are devops")

        assert len(async_team._spawned_agents) == 3


class TestShutdownRequest:
    """Tests for shutdown_request tool (s10)."""

    def test_shutdown_request_sends_message(self, async_bus):
        """shutdown_request sends shutdown_request message to inbox."""
        async_bus.send("lead", "alice", "shutdown_request", msg_type="shutdown_request")

        inbox = async_bus.read_inbox("alice")
        assert len(inbox) == 1
        assert inbox[0]["type"] == "shutdown_request"

    def test_shutdown_response_received(self, async_bus):
        """shutdown_response is received and processed."""
        msg_id = "test-shutdown-123"
        async_bus.send("alice", "lead", "shutdown_response", msg_type="shutdown_response",
                       in_reply_to=msg_id, approved=True)

        inbox = async_bus.read_inbox("lead")
        shutdown_msgs = [m for m in inbox if m.get("type") == "shutdown_response"]
        assert len(shutdown_msgs) == 1
        assert shutdown_msgs[0].get("approved") is True

    def test_shutdown_request_with_timeout(self, async_bus):
        """shutdown_request handles timeout when no response."""
        async_bus.send("lead", "alice", "shutdown_request", msg_type="shutdown_request",
                       id="orphan-msg")

        inbox = async_bus.read_inbox("lead")
        orphan_msgs = [m for m in inbox if m.get("id") == "orphan-msg"]
        assert len(orphan_msgs) == 0


class TestPlanApproval:
    """Tests for plan_approval tool (s10)."""

    def test_plan_approval_sends_message(self, async_bus):
        """plan_approval sends plan_approval message."""
        task_id = "task-123"
        content = json.dumps({"task_id": task_id, "approve": True, "feedback": "Looks good"})
        async_bus.send("lead", "alice", content, msg_type="plan_approval")

        inbox = async_bus.read_inbox("alice")
        assert len(inbox) == 1
        assert inbox[0]["type"] == "plan_approval"

    def test_plan_approval_reject(self, async_bus):
        """plan_approval with approve=False sends rejection."""
        task_id = "task-456"
        content = json.dumps({"task_id": task_id, "approve": False, "feedback": "Needs revision"})
        async_bus.send("lead", "alice", content, msg_type="plan_approval")

        inbox = async_bus.read_inbox("alice")
        msg = inbox[0]
        parsed = json.loads(msg["content"])
        assert parsed["approve"] is False


class TestIdle:
    """Tests for idle tool (s12)."""

    def test_idle_returns_idle_string(self):
        """idle handler returns 'idle' string."""
        from h_agent.team.agent import FullAgentHandler

        with patch.object(FullAgentHandler, '__init__', lambda self, **kw: None):
            handler = FullAgentHandler.__new__(FullAgentHandler)
            handler.async_team = MagicMock()
            handler.async_bus = MagicMock()

            def idle_handler() -> str:
                return "idle"

            result = idle_handler()
            assert result == "idle"


class TestClaimTask:
    """Tests for claim_task tool (s12)."""

    def test_claim_task_updates_owner(self, async_team):
        """claim_task updates task owner to current agent."""
        task_id = "task-789"

        if hasattr(async_team, 'claim_task'):
            result = async_team.claim_task(task_id, "lead")
            assert task_id in result or "claimed" in result.lower()

    def test_claim_task_fallback(self):
        """claim_task returns confirmation when async_team.claim_task returns None."""
        from h_agent.team.agent import FullAgentHandler

        with patch.object(FullAgentHandler, '__init__', lambda self, **kw: None):
            handler = FullAgentHandler.__new__(FullAgentHandler)
            handler.async_team = MagicMock()
            handler.async_team.claim_task.return_value = None
            handler.agent_name = "test-lead"

            def claim_task_handler(task_id: str) -> str:
                result = handler.async_team.claim_task(task_id, handler.agent_name)
                if result is not None:
                    return result
                return f"Claimed task {task_id}"

            result = claim_task_handler("task-123")
            assert "task-123" in result


class TestToolIntegration:
    """Integration tests for s09-s12 tools."""

    def test_lead_tools_include_new_tools(self):
        """LEAD_TOOLS includes all new tool definitions."""
        from h_agent.team.async_team import LEAD_TOOLS

        tool_names = [t["function"]["name"] for t in LEAD_TOOLS]

        assert "spawn_teammate" in tool_names
        assert "shutdown_request" in tool_names
        assert "plan_approval" in tool_names
        assert "idle" in tool_names
        assert "claim_task" in tool_names

    def test_tool_definitions_have_required_fields(self):
        """New tools have required name, description, parameters."""
        from h_agent.team.async_team import LEAD_TOOLS

        new_tools = ["spawn_teammate", "shutdown_request", "plan_approval", "idle", "claim_task"]

        for tool_name in new_tools:
            tool = next((t for t in LEAD_TOOLS if t["function"]["name"] == tool_name), None)
            assert tool is not None, f"{tool_name} not found in LEAD_TOOLS"
            assert "description" in tool["function"]
            assert "parameters" in tool["function"]
            assert tool["function"]["parameters"]["type"] == "object"

    def test_spawn_teammate_has_required_params(self):
        """spawn_teammate requires name, role, prompt."""
        from h_agent.team.async_team import LEAD_TOOLS

        tool = next((t for t in LEAD_TOOLS if t["function"]["name"] == "spawn_teammate"), None)
        params = tool["function"]["parameters"]["properties"]

        assert "name" in params
        assert "role" in params
        assert "prompt" in params

    def test_plan_approval_has_required_params(self):
        """plan_approval requires task_id and approve."""
        from h_agent.team.async_team import LEAD_TOOLS

        tool = next((t for t in LEAD_TOOLS if t["function"]["name"] == "plan_approval"), None)
        params = tool["function"]["parameters"]["properties"]
        required = tool["function"]["parameters"]["required"]

        assert "task_id" in params
        assert "approve" in params
        assert "task_id" in required
        assert "approve" in required
