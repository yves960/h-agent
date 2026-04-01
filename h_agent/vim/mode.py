"""
h_agent/vim/mode.py - Vim Mode Management

Vim engine with mode tracking and key handling.
"""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional


class VimMode(str, Enum):
    """Vim editing modes."""
    NORMAL = "normal"
    INSERT = "insert"
    VISUAL = "visual"
    COMMAND = "command"
    REPLACE = "replace"


@dataclass
class VimState:
    """Current Vim state."""
    mode: VimMode = VimMode.NORMAL
    register: str = ""
    count: int = 0
    partial_command: str = ""
    visual_start: Optional[tuple[int, int]] = None  # (line, col)


class VimEngine:
    """
    Vim editing engine.

    Handles mode transitions and key → action mapping.
    """

    def __init__(self):
        self.state = VimState()
        self._key_map: dict[str, str] = {}

    def reset(self):
        """Reset to normal mode."""
        self.state = VimState()

    def handle_key(self, key: str) -> Optional[str]:
        """
        Handle a key press.

        Args:
            key: The key pressed (single char or special key name)

        Returns:
            Action string or None if key was consumed as part of a command
        """
        # Count prefix (e.g., 3w)
        if key.isdigit() and self.state.partial_command == "":
            self.state.count = self.state.count * 10 + int(key)
            return None

        # Build up command
        self.state.partial_command += key

        action = self._get_action(self.state.partial_command)
        if action:
            self.state.partial_command = ""
            self.state.count = 0
            return action

        return None

    def _get_action(self, cmd: str) -> Optional[str]:
        """Look up action for a command sequence."""
        if self.state.mode == VimMode.NORMAL:
            return self._normal_action(cmd)
        elif self.state.mode == VimMode.INSERT:
            return self._insert_action(cmd)
        elif self.state.mode == VimMode.VISUAL:
            return self._visual_action(cmd)
        elif self.state.mode == VimMode.COMMAND:
            return self._command_action(cmd)
        return None

    def _normal_action(self, cmd: str) -> Optional[str]:
        """Normal mode actions."""
        if cmd == "i":
            self.state.mode = VimMode.INSERT
            return "enter_insert"
        if cmd == "a":
            self.state.mode = VimMode.INSERT
            return "append"
        if cmd == "I":
            self.state.mode = VimMode.INSERT
            return "insert_line_start"
        if cmd == "A":
            self.state.mode = VimMode.INSERT
            return "append_line_end"
        if cmd == "v":
            self.state.mode = VimMode.VISUAL
            return "enter_visual"
        if cmd == "V":
            self.state.mode = VimMode.VISUAL
            return "enter_visual_line"
        if cmd == ":":
            self.state.mode = VimMode.COMMAND
            return "enter_command"
        if cmd == "h":
            return "move_left"
        if cmd == "l":
            return "move_right"
        if cmd == "j":
            return "move_down"
        if cmd == "k":
            return "move_up"
        if cmd == "w":
            return "move_word_forward"
        if cmd == "b":
            return "move_word_back"
        if cmd == "e":
            return "move_word_end"
        if cmd == "0":
            return "move_line_start"
        if cmd == "$":
            return "move_line_end"
        if cmd == "gg":
            return "move_file_start"
        if cmd == "G":
            return "move_file_end"
        if cmd == "x":
            return "delete_char"
        if cmd == "dd":
            return "delete_line"
        if cmd == "yy":
            return "yank_line"
        if cmd == "p":
            return "paste"
        if cmd == "u":
            return "undo"
        if cmd == "r":
            return "enter_replace"
        if cmd == "o":
            return "open_line_below"
        if cmd == "O":
            return "open_line_above"
        if cmd == "cw":
            return "change_word"
        if cmd == "dw":
            return "delete_word"
        if cmd == "yw":
            return "yank_word"
        if cmd == "/":
            return "enter_search"
        if cmd == "n":
            return "search_next"
        if cmd == "N":
            return "search_prev"
        if cmd == ".":
            return "repeat"
        if cmd == "zz":
            return "center_view"
        # Invalid command
        if len(cmd) > 1:
            self.state.partial_command = ""
        return None

    def _insert_action(self, cmd: str) -> Optional[str]:
        """Insert mode actions."""
        if cmd == "\x1b":  # ESC
            self.state.mode = VimMode.NORMAL
            return "exit_insert"
        if cmd == "\r":
            return "insert_newline"
        if cmd == "\x7f":  # Backspace
            return "delete_back"
        return f"insert:{cmd}"

    def _visual_action(self, cmd: str) -> Optional[str]:
        """Visual mode actions."""
        if cmd == "\x1b":  # ESC
            self.state.mode = VimMode.NORMAL
            return "exit_visual"
        if cmd == "d":
            return "visual_delete"
        if cmd == "y":
            return "visual_yank"
        if cmd == "c":
            return "visual_change"
        if cmd == "x":
            return "visual_delete"
        if cmd == "p":
            return "visual_paste"
        if cmd == ">":
            return "visual_indent"
        if cmd == "<":
            return "visual_dedent"
        return None

    def _command_action(self, cmd: str) -> Optional[str]:
        """Command mode actions."""
        if cmd == "\x1b":
            self.state.mode = VimMode.NORMAL
            return "exit_command"
        if cmd == "\r":
            return "execute_command"
        return f"command:{cmd}"
