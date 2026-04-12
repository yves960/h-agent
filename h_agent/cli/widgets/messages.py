"""
h_agent/cli/widgets/messages.py - Message formatting helpers.
"""

from __future__ import annotations

from h_agent.cli.state import SessionState, UiMessage


ROLE_LABELS = {
    "user": "You",
    "assistant": "Assistant",
    "system": "System",
    "tool": "Tool",
}


def format_message(message: UiMessage) -> str:
    """Render a UI message as plain text."""
    label = ROLE_LABELS.get(message.role, message.role.title())
    body = message.text.rstrip()
    if not body:
        body = "(empty)"
    prefix = {
        "thinking": "... ",
        "tool": "$ ",
        "progress": "⏳ ",
        "error": "! ",
        "permission": "? ",
        "command": "> ",
        "command_result": "= ",
    }.get(message.kind, "")
    return f"{label}: {prefix}{body}"


def render_messages_text(state: SessionState) -> str:
    """Render the full message list for the transcript pane."""
    if not state.messages:
        return "No messages yet.\nType a prompt or /help to begin."
    return "\n\n".join(format_message(item) for item in state.messages)
