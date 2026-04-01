"""
h_agent/tools/file_edit.py - File Edit Tool

Makes precise edits to files using string replacement.
Inspired by Claude Code's FileEditTool.
"""

from __future__ import annotations

import os
import sys
import difflib
from pathlib import Path
from typing import Optional

from h_agent.tools.base import Tool, ToolResult


class FileEditTool(Tool):
    """
    Tool for making precise edits to files.
    
    Features:
    - Exact string replacement (old_text must match exactly)
    - Diff preview option
    - Multiple occurrence detection (prevents accidental multi-edit)
    - Line-based editing support
    """

    name = "edit"
    description = "Make a precise edit to a file by replacing exact text. The old_text must match the file content exactly."

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to edit"
                },
                "old_text": {
                    "type": "string",
                    "description": "Exact text to find and replace. Must match the file content exactly, including whitespace."
                },
                "new_text": {
                    "type": "string",
                    "description": "Text to replace the old_text with"
                },
                "allow_multi": {
                    "type": "boolean",
                    "description": "Allow replacing multiple occurrences (default: False - error if > 1 occurrence)",
                    "default": False,
                },
                "strict": {
                    "type": "boolean",
                    "description": "Require exact whitespace matching (default: True)",
                    "default": True,
                },
            },
            "required": ["path", "old_text", "new_text"]
        }

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace for comparison when strict=False."""
        import re
        return re.sub(r"\s+", " ", text.strip())

    def _find_matches(
        self,
        content: str,
        old_text: str,
        strict: bool = True,
    ) -> list:
        """Find all occurrences of old_text in content."""
        if strict:
            # Exact match
            matches = []
            start = 0
            while True:
                idx = content.find(old_text, start)
                if idx == -1:
                    break
                matches.append(idx)
                start = idx + 1
            return matches
        else:
            # Normalized match
            normalized_old = self._normalize_whitespace(old_text)
            normalized_content = self._normalize_whitespace(content)
            matches = []
            start = 0
            while True:
                idx = normalized_content.find(normalized_old, start)
                if idx == -1:
                    break
                matches.append(idx)
                start = idx + 1
            return matches

    def _create_diff(
        self,
        old_text: str,
        new_text: str,
        path: str,
        context_lines: int = 3,
    ) -> str:
        """Create a unified diff preview."""
        old_lines = old_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=path,
            tofile=path,
            n=context_lines,
        )
        return "".join(diff)

    async def execute(self, args: dict) -> ToolResult:
        """
        Edit a file by replacing text.
        
        Args:
            args: dict with keys:
                - path: str (required)
                - old_text: str (required) - exact text to replace
                - new_text: str (required) - replacement text
                - allow_multi: bool (optional, default False)
                - strict: bool (optional, default True)
        """
        path = args.get("path", "")
        old_text = args.get("old_text", "")
        new_text = args.get("new_text", "")
        allow_multi = args.get("allow_multi", False)
        strict = args.get("strict", True)

        if not path:
            return ToolResult.err("No path provided")
        if not old_text:
            return ToolResult.err("No old_text provided")

        # Resolve relative paths
        if not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)

        # Check existence
        if not os.path.exists(path):
            return ToolResult.err(f"File not found: {path}")

        if not os.path.isfile(path):
            return ToolResult.err(f"Not a file: {path}")

        # Read current content
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return ToolResult.err(f"Error reading file: {e}")

        # Find matches
        matches = self._find_matches(content, old_text, strict=strict)
        
        if not matches:
            if not strict:
                # In non-strict mode, try to suggest similar text
                normalized_content = self._normalize_whitespace(content)
                normalized_old = self._normalize_whitespace(old_text)
                if normalized_old in normalized_content:
                    return ToolResult.err(
                        "Text found but whitespace doesn't match exactly. "
                        "Use strict=False to ignore whitespace differences."
                    )
            return ToolResult.err(
                "Text not found in file. The old_text must match exactly."
            )

        # Check number of matches
        if len(matches) > 1 and not allow_multi:
            return ToolResult.err(
                f"Found {len(matches)} occurrences of old_text. "
                "It must be unique. Use allow_multi=True to replace all."
            )

        # Create replacement
        if strict:
            new_content = content.replace(old_text, new_text)
        else:
            # Non-strict: need to rebuild preserving structure
            # This is more complex - for now, replace all at once
            normalized_content = self._normalize_whitespace(content)
            normalized_old = self._normalize_whitespace(old_text)
            
            result_parts = []
            last_end = 0
            for match_idx in self._find_matches(normalized_content, normalized_old, strict=False):
                result_parts.append(content[last_end:match_idx])
                result_parts.append(new_text)
                last_end = match_idx + len(old_text)
            result_parts.append(content[last_end:])
            new_content = "".join(result_parts)

        # Verify the replacement will work
        if new_content == content:
            return ToolResult.err("Replacement would not change the file")

        # Write back
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)
        except Exception as e:
            return ToolResult.err(f"Error writing file: {e}")

        # Report result
        count = len(matches)
        if count == 1:
            return ToolResult.ok(f"Successfully edited {path}")
        else:
            return ToolResult.ok(
                f"Successfully replaced {count} occurrences in {path}"
            )


# Convenience handler function
def edit_handler(args: dict) -> ToolResult:
    """Simple handler function for edit tool."""
    tool = FileEditTool()
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, tool.execute(args))
                return future.result()
        else:
            return loop.run_until_complete(tool.execute(args))
    except RuntimeError:
        return asyncio.run(tool.execute(args))
