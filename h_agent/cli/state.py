"""
h_agent/cli/state.py - Session state for the interactive CLI.

The first-stage terminal app keeps all mutable UI state here so the
controller and renderer have a single source of truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from h_agent.session.transcript import Transcript


@dataclass
class UiMessage:
    """A rendered message in the terminal session."""

    id: str
    role: str
    text: str
    kind: str = "message"
    timestamp: float = 0.0
    meta: dict = field(default_factory=dict)


@dataclass
class PendingPermission:
    """A pending permission request surfaced to the user."""

    id: str
    tool_name: str
    tool_args: dict
    reason: str
    risk_level: str = "medium"
    created_at: float = 0.0


@dataclass
class PendingPrompt:
    """A generic prompt that requires user input."""

    id: str
    title: str
    body: str
    options: list[str] = field(default_factory=list)
    created_at: float = 0.0


@dataclass
class SessionMetrics:
    """Rolling session metrics shown in the status line."""

    total_tokens: int = 0
    total_cost_usd: float = 0.0


@dataclass
class SessionState:
    """Mutable state for one CLI session."""

    session_id: str
    model: str
    cwd: str
    transcript: Transcript
    raw_messages: list[dict] = field(default_factory=list)
    messages: list[UiMessage] = field(default_factory=list)
    input_value: str = ""
    input_mode: str = "prompt"
    vim_mode: str = "insert"
    status_text: str = ""
    is_loading: bool = False
    is_streaming: bool = False
    pending_permissions: list[PendingPermission] = field(default_factory=list)
    pending_prompts: list[PendingPrompt] = field(default_factory=list)
    queued_commands: list[str] = field(default_factory=list)
    input_history: list[str] = field(default_factory=list)
    history_index: int = -1
    command_suggestions: list[str] = field(default_factory=list)
    show_help_overlay: bool = False
    metrics: SessionMetrics = field(default_factory=SessionMetrics)
    last_error: Optional[str] = None
