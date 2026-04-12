"""
h_agent/cli/widgets/prompt.py - Prompt helpers.
"""

from __future__ import annotations

from h_agent.cli.state import SessionState


def get_prompt_prefix(state: SessionState) -> str:
    """Return the visual prompt prefix."""
    if state.pending_permissions:
        return "[permission] "
    if state.input_mode == "command":
        return "/ "
    return ">> "

