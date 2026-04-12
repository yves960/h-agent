"""
h_agent/cli/widgets/dialogs.py - Dialog text helpers.
"""

from __future__ import annotations

from h_agent.cli.state import SessionState


def build_permission_text(state: SessionState) -> str:
    """Render the top pending permission request."""
    if not state.pending_permissions:
        return ""
    pending = state.pending_permissions[0]
    lines = [
        "Permission Request",
        f"Tool: {pending.tool_name}",
        f"Reason: {pending.reason}",
        "Press y to allow or n to deny.",
    ]
    return "\n".join(lines)

