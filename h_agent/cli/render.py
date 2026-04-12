"""
h_agent/cli/render.py - prompt_toolkit layout assembly for the CLI.
"""

from __future__ import annotations

from h_agent.cli.widgets.dialogs import build_permission_text
from h_agent.cli.widgets.commands import build_command_suggestions_text
from h_agent.cli.widgets.messages import render_messages_text
from h_agent.cli.widgets.prompt import get_prompt_prefix
from h_agent.cli.widgets.status import build_status_text

try:
    from prompt_toolkit.formatted_text import FormattedText
    from prompt_toolkit.filters import Condition
    from prompt_toolkit.layout.containers import ConditionalContainer, HSplit, Window
    from prompt_toolkit.layout.controls import FormattedTextControl
    from prompt_toolkit.layout.dimension import Dimension
    from prompt_toolkit.layout.layout import Layout
    from prompt_toolkit.widgets import TextArea
    HAS_PROMPT_TOOLKIT = True
except ImportError:  # pragma: no cover - import guard
    FormattedText = None
    Condition = None
    ConditionalContainer = None
    HSplit = None
    Window = None
    FormattedTextControl = None
    Dimension = None
    Layout = None
    TextArea = None
    HAS_PROMPT_TOOLKIT = False


class CliRenderer:
    """Build a simple multi-pane layout from the current session state."""

    def __init__(self, state) -> None:
        self.state = state
        self.messages_area = None
        self.input_area = None
        self.status_bar = None
        self.permission_bar = None
        self.command_bar = None

    def build_layout(self):
        """Create the prompt_toolkit layout."""
        if not HAS_PROMPT_TOOLKIT:  # pragma: no cover - runtime fallback
            return None

        self.messages_area = TextArea(
            text=render_messages_text(self.state),
            focusable=False,
            scrollbar=True,
            wrap_lines=True,
            read_only=True,
        )
        self.input_area = TextArea(
            multiline=False,
            prompt=get_prompt_prefix(self.state),
            height=1,
            wrap_lines=False,
        )
        self.input_area.buffer.on_text_changed += self._on_input_changed
        self.permission_bar = Window(
            content=FormattedTextControl(self._permission_fragments),
            height=Dimension(min=0, preferred=0, max=4),
        )
        self.command_bar = Window(
            content=FormattedTextControl(self._command_fragments),
            height=Dimension(min=0, preferred=0, max=10),
        )
        self.status_bar = Window(
            content=FormattedTextControl(self._status_fragments),
            height=1,
        )

        container = HSplit(
            [
                self.messages_area,
                ConditionalContainer(
                    self.permission_bar,
                    filter=Condition(lambda: bool(self.state.pending_permissions)),
                ),
                ConditionalContainer(
                    self.command_bar,
                    filter=Condition(
                        lambda: bool(
                            self.state.command_suggestions or self.state.show_help_overlay
                        )
                    ),
                ),
                self.input_area,
                self.status_bar,
            ]
        )
        return Layout(container, focused_element=self.input_area)

    def refresh(self) -> None:
        """Refresh widget content from state."""
        if self.messages_area is not None:
            self.messages_area.text = render_messages_text(self.state)
        if self.input_area is not None:
            self.input_area.prompt = get_prompt_prefix(self.state)

    def _status_fragments(self):
        return FormattedText([("reverse", build_status_text(self.state))])

    def _permission_fragments(self):
        text = build_permission_text(self.state)
        return FormattedText([("fg:yellow", text)])

    def _command_fragments(self):
        text = build_command_suggestions_text(self.state)
        return FormattedText([("fg:cyan", text)])

    def _on_input_changed(self, _event) -> None:
        if self.input_area is None:
            return
        self.state.input_value = self.input_area.text
        if hasattr(self.state, "command_suggestions"):
            # App/controller wiring may update the suggestion list later; this
            # keeps state.input_value in sync even before those hooks fire.
            pass
