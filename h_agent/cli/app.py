"""
h_agent/cli/app.py - First-stage interactive CLI application.

This is a pragmatic shell built on prompt_toolkit when available. It
centralizes session state and controller wiring, while keeping a simple
fallback path when prompt_toolkit is not installed.
"""

from __future__ import annotations

import asyncio
import os
from typing import Optional

from h_agent.cli.controller import CliController
from h_agent.cli.keybindings import create_keybindings
from h_agent.cli.render import CliRenderer
from h_agent.cli.state import SessionState, UiMessage
from h_agent.commands import get_registry as get_command_registry
from h_agent.core.engine import QueryEngine
from h_agent.session import SessionStorage, Transcript
from h_agent.tools import get_registry as get_tool_registry

try:
    from prompt_toolkit import print_formatted_text
    from prompt_toolkit.application import Application
    from prompt_toolkit.formatted_text import HTML
    HAS_PROMPT_TOOLKIT = True
except ImportError:  # pragma: no cover - runtime fallback
    Application = None
    print_formatted_text = None
    HTML = None
    HAS_PROMPT_TOOLKIT = False


class CliApp:
    """Stateful interactive CLI shell."""

    def __init__(
        self,
        model: str,
        system_prompt: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        self.model = model
        self.system_prompt = system_prompt or (
            f"You are a helpful AI assistant. Current directory: {os.getcwd()}"
        )
        self.storage = SessionStorage()
        self.tool_registry = get_tool_registry()
        self.command_registry = get_command_registry()
        self.state = self._build_initial_state(session_id)
        self.engine = QueryEngine(
            model=model,
            tools=self.tool_registry.get_tool_schemas(),
            system_prompt=self.system_prompt,
            tool_registry=self.tool_registry,
        )
        self.controller = CliController(
            state=self.state,
            engine=self.engine,
            command_registry=self.command_registry,
            tool_registry=self.tool_registry,
            storage=self.storage,
            system_prompt=self.system_prompt,
        )
        self.controller.bind_output(
            message_sink=self._display_message,
            status_sink=self._display_status,
        )
        self.renderer = CliRenderer(self.state)
        self._pt_app = None
        self.controller.refresh_status_line()

    def _build_initial_state(self, session_id: Optional[str]) -> SessionState:
        transcript = None
        if session_id:
            transcript = self.storage.load_session(session_id)
        if transcript is None:
            actual_session_id = session_id or self.storage.generate_session_id()
            transcript = Transcript.create(actual_session_id, self.model)
        else:
            actual_session_id = transcript.session_id

        state = SessionState(
            session_id=actual_session_id,
            model=self.model,
            cwd=os.getcwd(),
            transcript=transcript,
        )
        state.raw_messages = [
            {"role": item.role, "content": item.content}
            for item in transcript.messages
            if item.role in {"user", "assistant", "tool"}
        ]
        for item in transcript.messages:
            state.messages.append(
                UiMessage(
                    id=f"replay-{len(state.messages)}",
                    role=item.role,
                    text=item.content,
                    kind="history",
                    timestamp=0.0,
                )
            )
        return state

    async def run_async(self, initial_prompt: Optional[str] = None) -> int:
        """Run the interactive shell."""
        if initial_prompt:
            await self.controller.submit_input(initial_prompt)
            return 0

        if not HAS_PROMPT_TOOLKIT:
            self._print_welcome()
            self._replay_transcript()
            return await self._run_fallback_loop()

        return await self._run_prompt_toolkit_ui()

    def run(self, initial_prompt: Optional[str] = None) -> int:
        """Synchronous wrapper."""
        return asyncio.run(self.run_async(initial_prompt=initial_prompt))

    async def _run_fallback_loop(self) -> int:
        """Fallback loop when prompt_toolkit is unavailable."""
        while True:
            try:
                text = input(">> ")
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            raw = text.strip()
            if raw.lower() in {"q", "exit"}:
                print("Goodbye!")
                break

            await self.controller.submit_input(raw)
            await self._drain_pending_permissions_fallback()
            if self.controller.should_exit:
                break
        return 0

    async def _drain_pending_permissions_fallback(self) -> None:
        """Fallback permission handling using built-in input()."""
        while self.state.pending_permissions:
            current = self.state.pending_permissions[0]
            try:
                answer = input(f"[permission] {current.reason} [y/N] ")
            except (EOFError, KeyboardInterrupt):
                answer = "n"
            await self.controller.resolve_permission(
                current.id,
                answer.strip().lower() in {"y", "yes"},
            )

    async def _run_prompt_toolkit_ui(self) -> int:
        """Run the prompt_toolkit multi-pane interface."""
        layout = self.renderer.build_layout()
        key_bindings = create_keybindings(
            self.controller,
            self.state,
            self.renderer.input_area,
        )
        self._pt_app = Application(
            layout=layout,
            key_bindings=key_bindings,
            full_screen=True,
        )
        self._display_status(self.state.status_text)
        result = await self._pt_app.run_async()
        return 0 if result is None else int(result)

    def _print_welcome(self) -> None:
        self._println("h-agent - Interactive CLI")
        self._println(f"Session: {self.state.session_id}")
        self._println(f"Model: {self.state.model}")
        self._println("Type /help for commands, or exit to quit.")
        self._println("")

    def _replay_transcript(self) -> None:
        for item in self.state.transcript.messages:
            self._display_message(item)

    def _display_message(self, message) -> None:
        if self._pt_app is not None:
            self.renderer.refresh()
            if self.controller.should_exit:
                self._pt_app.exit(result=0)
            self._pt_app.invalidate()
            return

        text = getattr(message, "text", getattr(message, "content", ""))
        label_map = {
            "user": "You",
            "assistant": "Assistant",
            "system": "System",
            "tool": "Tool",
        }
        label = label_map.get(message.role, message.role.title())
        if HAS_PROMPT_TOOLKIT and print_formatted_text and HTML:
            color = {
                "error": "ansired",
                "thinking": "ansigray",
                "tool": "ansiyellow",
                "permission": "ansiyellow",
                "command_result": "ansicyan",
            }.get(getattr(message, "kind", ""), "ansiwhite")
            print_formatted_text(HTML(f"<b>{label}:</b> <style fg='{color}'>{self._escape(text)}</style>"))
        else:
            print(f"{label}: {text}")

    def _display_status(self, status: str) -> None:
        self.state.status_text = status
        if self._pt_app is not None:
            self.renderer.refresh()
            if self.controller.should_exit:
                self._pt_app.exit(result=0)
            self._pt_app.invalidate()

    def _println(self, text: str) -> None:
        if HAS_PROMPT_TOOLKIT and print_formatted_text:
            print_formatted_text(text)
        else:
            print(text)

    @staticmethod
    def _escape(text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
