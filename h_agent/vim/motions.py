"""
h_agent/vim/motions.py - Vim Motions

Text object and motion handling for Vim-style editing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class TextRange:
    """Represents a range of text in a buffer."""
    start_line: int
    start_col: int
    end_line: int
    end_col: int

    def __repr__(self):
        return f"TextRange({self.start_line}:{self.start_col}-{self.end_line}:{self.end_col})"


class VimMotions:
    """
    Vim motion utilities.

    Provides utilities for parsing and executing Vim-style text objects
    and motions within a text buffer.
    """

    # Text object patterns: aw (a word), iw (inner word), as (a sentence), etc.
    TEXT_OBJECTS = {
        "iw": "inner_word",
        "aw": "a_word",
        "iW": "inner_WORD",
        "aW": "a_WORD",
        "is": "inner_sentence",
        "as": "a_sentence",
        "ip": "inner_paragraph",
        "ap": "a_paragraph",
        "i]": "inner_bracket",
        "a]": "a_bracket",
        "i(": "inner_paren",
        "a(": "a_paren",
    }

    @staticmethod
    def count_repeat(motion: str, count: int) -> str:
        """Apply count to a motion."""
        if count <= 1:
            return motion
        return motion * count

    @staticmethod
    def is_motion(s: str) -> bool:
        """Check if string is a motion command."""
        motions = {"h", "j", "k", "l", "w", "b", "e", "0", "$", "gg", "G", "f", "F", "t", "T"}
        return s in motions

    @staticmethod
    def expand_text_object(text: str, obj: str, pos: tuple[int, int]) -> TextRange:
        """
        Expand a text object to a range.

        Args:
            text: Full buffer text
            obj: Text object identifier (e.g., "iw", "aw")
            pos: Current position (line, col) 1-indexed

        Returns:
            TextRange covering the text object
        """
        lines = text.split("\n")
        line_idx = pos[0] - 1
        col_idx = pos[1] - 1

        if obj == "iw" or obj == "aw":
            # Word - find word boundaries
            word_chars = r"\w"
            padding = 1 if obj == "aw" else 0

            # Find word start
            line = lines[line_idx]
            start_col = col_idx
            end_col = col_idx

            # Move back to word start
            while start_col > 0 and re.match(word_chars, line[start_col - 1]):
                start_col -= 1

            # Move forward to word end
            while end_col < len(line) and re.match(word_chars, line[end_col]):
                end_col += 1

            return TextRange(line_idx + 1, start_col + 1 - padding,
                            line_idx + 1, end_col + padding)

        return TextRange(pos[0], pos[1], pos[0], pos[1])
