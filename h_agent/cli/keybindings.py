"""
h_agent/cli/keybindings.py - Shared prompt_toolkit key bindings.
"""

from __future__ import annotations

try:
    from prompt_toolkit.key_binding import KeyBindings
except ImportError:  # pragma: no cover - import guard
    KeyBindings = None


def create_keybindings(controller, state, input_field):
    """Create prompt_toolkit key bindings for the CLI layout."""
    if KeyBindings is None:  # pragma: no cover - runtime fallback
        return None

    kb = KeyBindings()

    @kb.add("enter")
    def _(event) -> None:
        if state.pending_permissions:
            return
        text = input_field.text
        input_field.buffer.text = ""
        event.app.create_background_task(controller.submit_input(text))

    @kb.add("c-c")
    def _(event) -> None:
        event.app.exit(result=0)

    @kb.add("c-l")
    def _(event) -> None:
        event.app.renderer.clear()

    @kb.add("up")
    def _(event) -> None:
        new_text = controller.history_previous(input_field.text)
        input_field.buffer.text = new_text
        controller.update_input_state(new_text)

    @kb.add("down")
    def _(event) -> None:
        new_text = controller.history_next(input_field.text)
        input_field.buffer.text = new_text
        controller.update_input_state(new_text)

    @kb.add("tab")
    def _(event) -> None:
        if state.pending_permissions:
            return
        new_text = controller.complete_command(input_field.text)
        input_field.buffer.text = new_text
        controller.update_input_state(new_text)

    @kb.add("f1")
    def _(event) -> None:
        controller.toggle_help_overlay()
        event.app.invalidate()

    @kb.add("y")
    def _(event) -> None:
        if not state.pending_permissions:
            return
        pending = state.pending_permissions[0]
        event.app.create_background_task(controller.resolve_permission(pending.id, True))

    @kb.add("n")
    def _(event) -> None:
        if not state.pending_permissions:
            return
        pending = state.pending_permissions[0]
        event.app.create_background_task(controller.resolve_permission(pending.id, False))

    return kb
