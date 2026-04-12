import asyncio

import pytest

from h_agent.cli.controller import CliController
from h_agent.cli.state import SessionState
from h_agent.commands.base import CommandResult
from h_agent.session.transcript import Transcript


class DummyEngine:
    def __init__(self):
        self._usage = type("Usage", (), {"total_tokens": 12, "cost_usd": 0.25})()

    async def run_tool_loop(self, messages, system_prompt=None, event_callback=None):
        if event_callback is not None:
            from h_agent.core.engine import StreamEvent, StreamEventType

            event_callback(StreamEvent(type=StreamEventType.CONTENT, content="hel"))
            event_callback(StreamEvent(type=StreamEventType.CONTENT, content="lo"))
        return "hello"

    def get_usage(self):
        return self._usage


class DummyStorage:
    def __init__(self):
        self.saved = []

    def save_session(self, transcript):
        self.saved.append(transcript.session_id)


class DummyRegistry:
    def __init__(self):
        self.items = {
            "help": type("Cmd", (), {"name": "help", "description": "Show help"})(),
            "history": type("Cmd", (), {"name": "history", "description": "Show history"})(),
        }

    async def execute(self, name, args, context):
        if name == "exit":
            context.running = False
            return CommandResult.ok("Goodbye!")
        return CommandResult.ok(f"ran:{name}:{args}")

    def find_partial(self, prefix):
        return [item for key, item in self.items.items() if key.startswith(prefix)]

    def list_commands(self):
        return list(self.items.values())


@pytest.fixture
def controller():
    state = SessionState(
        session_id="sess-test",
        model="gpt-4o",
        cwd="/tmp/project",
        transcript=Transcript.create("sess-test", "gpt-4o"),
    )
    return CliController(
        state=state,
        engine=DummyEngine(),
        command_registry=DummyRegistry(),
        tool_registry=object(),
        storage=DummyStorage(),
        system_prompt="test",
    )


def test_complete_command_single_match(controller):
    assert controller.complete_command("/he") == "/help "


def test_update_input_state_sets_suggestions(controller):
    controller.update_input_state("/h")
    assert controller.state.command_suggestions
    assert controller.state.command_suggestions[0].startswith("/help")


def test_history_navigation(controller):
    controller._remember_input("first")
    controller._remember_input("second")
    assert controller.history_previous("") == "second"
    assert controller.history_previous("") == "first"
    assert controller.history_next("") == "second"
    assert controller.history_next("") == ""


def test_stream_messages_are_merged(controller):
    asyncio.run(controller.run_prompt("hello?"))
    assistant_streams = [
        item for item in controller.state.messages
        if item.role == "assistant" and item.kind == "stream"
    ]
    assert len(assistant_streams) == 1
    assert assistant_streams[0].text == "hello"
