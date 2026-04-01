"""
h_agent/vim/keybindings.py - Vim Keybindings

Maps Vim actions to terminal/UI operations.
"""

from __future__ import annotations

from typing import Callable, Dict, Optional


class VimKeyBindings:
    """
    Maps Vim actions to actual key sequences and operations.

    Handles the translation from Vim actions to terminal key sequences
    (for sending to underlying editor) and vice versa.
    """

    def __init__(self):
        # Action → display name
        self.action_names: Dict[str, str] = {
            "move_left": "←",
            "move_right": "→",
            "move_up": "↑",
            "move_down": "↓",
            "move_word_forward": "w",
            "move_word_back": "b",
            "move_word_end": "e",
            "move_line_start": "0",
            "move_line_end": "$",
            "move_file_start": "gg",
            "move_file_end": "G",
            "enter_insert": "i",
            "exit_insert": "ESC",
            "enter_visual": "v",
            "enter_visual_line": "V",
            "exit_visual": "ESC",
            "enter_command": ":",
            "exit_command": "ESC",
            "delete_char": "x",
            "delete_line": "dd",
            "yank_line": "yy",
            "paste": "p",
            "undo": "u",
            "open_line_below": "o",
            "open_line_above": "O",
            "insert_newline": "↵",
            "delete_back": "⌫",
        }

    def get_display(self, action: str) -> str:
        """Get display representation of an action."""
        return self.action_names.get(action, action)

    def get_status(self, mode: str) -> str:
        """Get status bar text for a mode."""
        status_map = {
            "normal": "-- NORMAL --",
            "insert": "-- INSERT --",
            "visual": "-- VISUAL --",
            "visual_line": "-- VISUAL LINE --",
            "command": "-- COMMAND --",
            "replace": "-- REPLACE --",
        }
        return status_map.get(mode, mode)
