"""
h_agent/cli/widgets/commands.py - Command suggestion and help text.
"""

from __future__ import annotations

from h_agent.cli.state import SessionState


def build_command_suggestions_text(state: SessionState) -> str:
    """Render slash-command suggestions."""
    if state.show_help_overlay:
        return build_help_overlay_text(state)
    if not state.command_suggestions:
        return ""
    lines = ["Command Suggestions"]
    lines.extend(state.command_suggestions)
    return "\n".join(lines)


def build_help_overlay_text(state: SessionState) -> str:
    """Render a lightweight keybinding/help overlay."""
    lines = [
        "CLI Help",
        "Enter: submit input",
        "Tab: complete slash command",
        "Up/Down: input history",
        "Ctrl+L: clear terminal",
        "Ctrl+C: exit",
        "F1: toggle this help",
    ]
    if state.pending_permissions:
        lines.append("y / n: resolve permission request")
    return "\n".join(lines)
