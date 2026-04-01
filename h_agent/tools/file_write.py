"""
h_agent/tools/file_write.py - File Write Tool

Creates or overwrites files with content.
Inspired by Claude Code's FileWriteTool.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from h_agent.tools.base import Tool, ToolResult


class FileWriteTool(Tool):
    """
    Tool for writing content to files.
    
    Features:
    - Creates parent directories as needed
    - Supports append mode
    - Large file write progress reporting
    - Atomic write option (write to temp, then rename)
    """

    name = "write"
    description = "Write content to a file. Creates the file if it doesn't exist, overwrites if it does."
    concurrency_safe = False  # Write operation, not safe for parallel execution
    read_only = False

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to write"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file"
                },
                "append": {
                    "type": "boolean",
                    "description": "Append to existing file instead of overwriting",
                    "default": False,
                },
                "atomic": {
                    "type": "boolean",
                    "description": "Use atomic write (write to temp, then rename)",
                    "default": True,
                },
                "create_dirs": {
                    "type": "boolean",
                    "description": "Create parent directories if they don't exist",
                    "default": True,
                },
            },
            "required": ["path", "content"]
        }

    def _ensure_dir(self, path: str, create: bool = True) -> Optional[str]:
        """Ensure parent directory exists."""
        parent = os.path.dirname(path)
        if not parent:
            return None
        
        if os.path.exists(parent):
            if not os.path.isdir(parent):
                return f"Parent is not a directory: {parent}"
            return None
        
        if create:
            try:
                os.makedirs(parent, exist_ok=True)
                return None
            except Exception as e:
                return f"Cannot create directory: {e}"
        else:
            return f"Directory does not exist: {parent}"

    async def execute(self, args: dict) -> ToolResult:
        """
        Write content to a file.
        
        Args:
            args: dict with keys:
                - path: str (required)
                - content: str (required)
                - append: bool (optional, default False)
                - atomic: bool (optional, default True)
                - create_dirs: bool (optional, default True)
        """
        path = args.get("path", "")
        content = args.get("content", "")
        append = args.get("append", False)
        atomic = args.get("atomic", True)
        create_dirs = args.get("create_dirs", True)

        if not path:
            return ToolResult.err("No path provided")

        # Resolve relative paths
        if not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)

        # Create parent directories if needed
        if create_dirs:
            error = self._ensure_dir(path, create=True)
            if error:
                return ToolResult.err(error)

        # Check if path is a directory
        if os.path.exists(path) and os.path.isdir(path):
            return ToolResult.err(f"Path is a directory: {path}")

        # Large file warning
        if len(content) > 5 * 1024 * 1024:
            sys.stderr.write(
                f"[write] Writing {len(content)/(1024*1024):.1f} MB to {path}\n"
            )
            sys.stderr.flush()

        try:
            if atomic and not append:
                # Atomic write: write to temp, then rename
                import tempfile
                dir_name = os.path.dirname(path) or "."
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    dir=dir_name,
                    encoding="utf-8",
                    delete=False,
                ) as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name

                # Move temp file to final location
                os.replace(tmp_path, path)
            else:
                # Direct write or append
                mode = "a" if append else "w"
                # Check if we can write
                parent_dir = os.path.dirname(path) or "."
                if not os.path.exists(path) and not os.path.exists(parent_dir):
                    return ToolResult.err(f"Directory does not exist: {parent_dir}")
                
                with open(path, mode, encoding="utf-8") as f:
                    if append:
                        if not f.seekable():
                            return ToolResult.err("File is not seekable for append")
                        f.write(content)
                    else:
                        f.write(content)

            # Get final size
            final_size = os.path.getsize(path)

            if append:
                return ToolResult.ok(
                    f"Appended {len(content)} bytes to {path} (total: {final_size} bytes)"
                )
            else:
                return ToolResult.ok(
                    f"Successfully wrote {len(content)} bytes to {path}"
                )

        except PermissionError:
            return ToolResult.err(f"Permission denied: {path}")
        except Exception as e:
            return ToolResult.err(f"Error writing file: {e}")


# Convenience handler function
def write_handler(args: dict) -> ToolResult:
    """Simple handler function for write tool."""
    tool = FileWriteTool()
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
