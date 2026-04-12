"""
h_agent/cli/controller.py - State transitions for the interactive CLI.
"""

from __future__ import annotations

import os
import time
import uuid
from typing import Callable, Optional

from h_agent.cli.state import PendingPermission, SessionState, UiMessage
from h_agent.commands.base import CommandContext
from h_agent.core.engine import StreamEvent, StreamEventType
from h_agent.session.transcript import Message


class CliController:
    """Owns state updates and bridges user input to the engine."""

    def __init__(
        self,
        state: SessionState,
        engine,
        command_registry,
        tool_registry,
        storage,
        system_prompt: Optional[str] = None,
    ) -> None:
        self.state = state
        self.engine = engine
        self.command_registry = command_registry
        self.tool_registry = tool_registry
        self.storage = storage
        self.system_prompt = system_prompt
        self.should_exit = False
        self._message_sink: Optional[Callable[[UiMessage], None]] = None
        self._status_sink: Optional[Callable[[str], None]] = None

    def bind_output(
        self,
        message_sink: Optional[Callable[[UiMessage], None]] = None,
        status_sink: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Bind terminal output hooks."""
        self._message_sink = message_sink
        self._status_sink = status_sink

    async def submit_input(self, text: str) -> None:
        """Entry point for one user submission."""
        raw = text.strip()
        if not raw:
            return

        self.state.input_value = ""
        self.update_input_state("")
        self._remember_input(raw)
        if raw.startswith("/"):
            await self.run_command(raw[1:])
            return

        await self.run_prompt(raw)

    async def run_command(self, command_text: str) -> None:
        """Execute a slash command through the command registry."""
        parts = command_text.split(maxsplit=1)
        cmd_name = parts[0].lower() if parts else ""
        args = parts[1] if len(parts) > 1 else ""
        if not cmd_name:
            return

        self.append_ui_message("user", f"/{command_text}", kind="command")
        context = self.build_command_context()
        result = await self.command_registry.execute(cmd_name, args, context)
        if result.success:
            if result.output:
                self.append_ui_message("system", result.output, kind="command_result")
        else:
            error = result.error or "Command failed"
            self.state.last_error = error
            self.append_ui_message("system", error, kind="error")
        if not context.running:
            self.should_exit = True
        self.refresh_status_line()
        self.persist_transcript()

    async def run_prompt(self, prompt: str) -> None:
        """Send a user prompt through the engine."""
        self.state.is_loading = True
        self.state.is_streaming = True
        self.refresh_status_line()

        self.state.raw_messages.append({"role": "user", "content": prompt})
        self.state.transcript.add_message(
            Message(
                role="user",
                content=prompt,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
                tokens=0,
            )
        )
        self.append_ui_message("user", prompt)

        try:
            final_content = await self.engine.run_tool_loop(
                messages=self.state.raw_messages,
                system_prompt=self.system_prompt,
                event_callback=self.handle_engine_event,
            )
            if final_content and not self._has_assistant_message(final_content):
                self.append_ui_message("assistant", final_content)

            self.state.transcript.add_message(
                Message(
                    role="assistant",
                    content=final_content or "",
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
                    tokens=self.engine.get_usage().total_tokens,
                )
            )
        except Exception as exc:
            self.state.last_error = str(exc)
            self.append_ui_message("system", f"Query failed: {exc}", kind="error")
        finally:
            self.state.is_loading = False
            self.state.is_streaming = False
            self.refresh_status_line()
            self.persist_transcript()

    def handle_engine_event(self, event: StreamEvent) -> None:
        """Consume engine events and project them onto the session state."""
        if event.type == StreamEventType.THINKING:
            self.append_ui_message("assistant", str(event.content or ""), kind="thinking")
        elif event.type == StreamEventType.CONTENT:
            self.append_ui_message("assistant", str(event.content or ""), kind="stream")
        elif event.type == StreamEventType.TOOL_CALL:
            label = self._format_tool_call(event.tool_name or "tool", event.tool_args or {})
            self.append_ui_message("tool", label, kind="tool")
        elif event.type == StreamEventType.PROGRESS:
            self.state.status_text = f"⏳ {event.content}"
            self.append_ui_message("system", str(event.content or ""), kind="progress")
            if self._status_sink:
                self._status_sink(self.state.status_text)
        elif event.type == StreamEventType.USAGE and event.usage:
            self.state.metrics.total_tokens = event.usage.get("total_tokens", 0)
            self.state.metrics.total_cost_usd = self.engine.get_usage().cost_usd
            self.refresh_status_line()
        elif event.type == StreamEventType.PERMISSION_ASK:
            request = PendingPermission(
                id=str(uuid.uuid4()),
                tool_name=event.tool_name or "tool",
                tool_args=event.tool_args or {},
                reason=str(event.content or "Permission confirmation required"),
                created_at=time.time(),
            )
            self.state.pending_permissions.append(request)
            self.append_ui_message("system", request.reason, kind="permission")
        elif event.type == StreamEventType.ERROR:
            self.state.last_error = event.error
            self.append_ui_message("system", event.error or "Unknown engine error", kind="error")

    async def resolve_permission(self, request_id: str, allow: bool) -> None:
        """Resolve a pending permission request.

        The current engine only surfaces permission prompts as events, so the
        resolution is recorded in the transcript and state for now.
        """
        pending = None
        remainder = []
        for item in self.state.pending_permissions:
            if item.id == request_id:
                pending = item
            else:
                remainder.append(item)
        self.state.pending_permissions = remainder

        if not pending:
            return

        verdict = "allowed" if allow else "denied"
        self.append_ui_message(
            "user",
            f"{verdict}: {pending.tool_name}",
            kind="permission_result",
        )

    async def resolve_prompt(self, request_id: str, value: str) -> None:
        """Resolve a generic input request."""
        self.state.pending_prompts = [
            item for item in self.state.pending_prompts if item.id != request_id
        ]
        self.append_ui_message("user", value, kind="prompt_result")

    def build_command_context(self) -> CommandContext:
        """Create a command context backed by the current session state."""
        context = CommandContext(
            messages=self.state.raw_messages,
            running=True,
            engine=self.engine,
        )
        context.set("session_state", self.state)
        context.set("controller", self)
        return context

    def append_ui_message(self, role: str, text: str, kind: str = "message", **meta) -> None:
        """Append a rendered message and notify the sink."""
        if text is None:
            return
        if kind in {"stream", "thinking"} and self.state.messages:
            last = self.state.messages[-1]
            if last.role == role and last.kind == kind:
                last.text += text
                last.meta.update(meta)
                if self._message_sink:
                    self._message_sink(last)
                return
        message = UiMessage(
            id=str(uuid.uuid4()),
            role=role,
            text=text,
            kind=kind,
            timestamp=time.time(),
            meta=meta,
        )
        self.state.messages.append(message)
        if self._message_sink:
            self._message_sink(message)

    def refresh_status_line(self) -> None:
        """Recompute the bottom status line text."""
        usage = self.engine.get_usage() if self.engine else None
        total_tokens = usage.total_tokens if usage else self.state.metrics.total_tokens
        cost = usage.cost_usd if usage else self.state.metrics.total_cost_usd
        mode = "loading" if self.state.is_loading else self.state.input_mode
        cwd_name = os.path.basename(self.state.cwd.rstrip(os.sep)) or self.state.cwd
        self.state.status_text = (
            f"{self.state.model} | {mode} | {cwd_name} | "
            f"{total_tokens:,} tok | ${cost:.4f}"
        )
        if self._status_sink:
            self._status_sink(self.state.status_text)

    def persist_transcript(self) -> None:
        """Persist transcript state to disk."""
        try:
            self.storage.save_session(self.state.transcript)
        except Exception as exc:
            self.state.last_error = str(exc)

    def complete_command(self, text: str) -> str:
        """Complete a slash command using the registered command names."""
        raw = text.strip()
        if not raw.startswith("/"):
            return text
        body = raw[1:]
        if " " in body:
            return text
        matches = self.command_registry.find_partial(body)
        if len(matches) == 1:
            self.state.command_suggestions = [f"/{matches[0].name}"]
            return f"/{matches[0].name} "
        if matches:
            self.state.command_suggestions = [f"/{item.name}" for item in matches[:8]]
            names = ", ".join(self.state.command_suggestions)
            self.state.status_text = f"matches: {names}"
            if self._status_sink:
                self._status_sink(self.state.status_text)
        return text

    def history_previous(self, current_text: str) -> str:
        """Move backward through local input history."""
        if not self.state.input_history:
            return current_text
        if self.state.history_index == -1:
            self.state.history_index = len(self.state.input_history) - 1
        elif self.state.history_index > 0:
            self.state.history_index -= 1
        return self.state.input_history[self.state.history_index]

    def history_next(self, current_text: str) -> str:
        """Move forward through local input history."""
        if not self.state.input_history or self.state.history_index == -1:
            return current_text
        if self.state.history_index < len(self.state.input_history) - 1:
            self.state.history_index += 1
            return self.state.input_history[self.state.history_index]
        self.state.history_index = -1
        return ""

    def update_input_state(self, text: str) -> None:
        """Update transient input-derived UI state."""
        self.state.input_value = text
        raw = text.strip()
        if raw.startswith("/"):
            body = raw[1:]
            cmd = body.split(maxsplit=1)[0]
            matches = self.command_registry.find_partial(cmd) if cmd else self.command_registry.list_commands()
            self.state.command_suggestions = [f"/{item.name} - {item.description}" for item in matches[:8]]
        else:
            self.state.command_suggestions = []

    def toggle_help_overlay(self) -> None:
        """Toggle the lightweight help overlay."""
        self.state.show_help_overlay = not self.state.show_help_overlay

    def _has_assistant_message(self, text: str) -> bool:
        """Avoid duplicating the final assistant line when streaming already printed it."""
        for item in reversed(self.state.messages[-20:]):
            if item.role == "assistant" and item.text == text:
                return True
        return False

    def _remember_input(self, raw: str) -> None:
        """Store user input in the local history ring."""
        if not raw:
            return
        if not self.state.input_history or self.state.input_history[-1] != raw:
            self.state.input_history.append(raw)
        self.state.history_index = -1

    @staticmethod
    def _format_tool_call(tool_name: str, tool_args: dict) -> str:
        """Compact tool call text for the transcript."""
        if not tool_args:
            return tool_name
        preview_parts = []
        for key, value in list(tool_args.items())[:3]:
            text = str(value).replace("\n", " ")
            if len(text) > 40:
                text = text[:37] + "..."
            preview_parts.append(f"{key}={text}")
        joined = ", ".join(preview_parts)
        return f"{tool_name}({joined})"
