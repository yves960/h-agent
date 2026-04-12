"""
h_agent/cli/widgets/status.py - Status line helpers.
"""

from __future__ import annotations

from h_agent.cli.state import SessionState


def build_status_text(state: SessionState) -> str:
    """Build the bottom status line."""
    status = state.status_text.strip()
    if not status:
        status = f"{state.model} | {state.input_mode}"
    if state.pending_permissions:
        status = f"{status} | permission pending"
    if state.input_history:
        status = f"{status} | history:{len(state.input_history)}"
    if state.last_error:
        status = f"{status} | last error: {state.last_error}"
    return status
