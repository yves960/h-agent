"""
h_agent/tools/file_read.py - File Read Tool

Reads files with support for text, images, and PDFs.
Inspired by Claude Code's FileReadTool.
"""

from __future__ import annotations

import os
import sys
import mimetypes
from pathlib import Path
from typing import Optional

from h_agent.tools.base import Tool, ToolResult


# Maximum file size for reading (10MB default)
DEFAULT_MAX_SIZE = 10 * 1024 * 1024
DEFAULT_MAX_TOKENS = 150000

# Blocked paths for security
BLOCKED_PATHS = {
    "/dev/zero",
    "/dev/random",
    "/dev/urandom",
    "/dev/full",
    "/dev/stdin",
    "/dev/tty",
    "/dev/console",
    "/dev/stdout",
    "/dev/stderr",
}


class FileReadTool(Tool):
    """
    Tool for reading file contents.
    
    Supports:
    - Plain text files
    - Binary files (with size limits)
    - Images (with token-based truncation)
    - PDFs (page extraction)
    
    Features:
    - Line offset and limit support
    - Large file streaming with progress
    - Path validation
    """

    name = "read"
    description = "Read the contents of a file. Supports text, images, and PDFs."
    concurrency_safe = True  # Read-only operation, safe for parallel execution
    read_only = True

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to read"
                },
                "offset": {
                    "type": "integer",
                    "description": "Line number to start reading from (1-indexed, default: 1)",
                    "minimum": 1,
                    "default": 1,
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of lines to read (default: 2000, 0 = all)",
                    "minimum": 0,
                    "default": 2000,
                },
                "show_lines": {
                    "type": "boolean",
                    "description": "Whether to prefix each line with its line number",
                    "default": False,
                },
                "max_size": {
                    "type": "integer",
                    "description": "Maximum file size in bytes to read (default: 10MB)",
                    "default": DEFAULT_MAX_SIZE,
                },
            },
            "required": ["path"]
        }

    def _is_blocked_path(self, path: str) -> bool:
        """Check if path is blocked for security."""
        abs_path = os.path.abspath(path)
        return abs_path in BLOCKED_PATHS

    def _get_mime_type(self, path: str) -> Optional[str]:
        """Detect MIME type of a file."""
        mime_type, _ = mimetypes.guess_type(path)
        return mime_type

    def _is_text_file(self, path: str) -> bool:
        """Check if a file is likely text."""
        mime_type = self._get_mime_type(path)
        if mime_type:
            return mime_type.startswith("text/") or mime_type in (
                "application/json",
                "application/javascript",
                "application/xml",
                "application/xhtml+xml",
                "application/csv",
                "application/sql",
            )
        
        # Try reading first few bytes
        try:
            with open(path, "rb") as f:
                chunk = f.read(8192)
                # Check for null bytes (binary indicator)
                if b"\x00" in chunk:
                    return False
                # Try decoding as UTF-8
                try:
                    chunk.decode("utf-8")
                    return True
                except UnicodeDecodeError:
                    return False
        except Exception:
            return False

    def _is_image_file(self, path: str) -> bool:
        """Check if file is an image."""
        mime_type = self._get_mime_type(path)
        if mime_type:
            return mime_type.startswith("image/")
        ext = Path(path).suffix.lower()
        return ext in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg"}

    def _is_pdf_file(self, path: str) -> bool:
        """Check if file is a PDF."""
        mime_type = self._get_mime_type(path)
        if mime_type:
            return mime_type == "application/pdf"
        return Path(path).suffix.lower() == ".pdf"

    async def execute(self, args: dict) -> ToolResult:
        """
        Read a file.
        
        Args:
            args: dict with keys:
                - path: str (required)
                - offset: int (optional, default 1)
                - limit: int (optional, default 2000)
                - show_lines: bool (optional, default False)
                - max_size: int (optional, default 10MB)
        """
        path = args.get("path", "")
        offset = args.get("offset", 1)
        limit = args.get("limit", 2000)
        show_lines = args.get("show_lines", False)
        max_size = args.get("max_size", DEFAULT_MAX_SIZE)

        if not path:
            return ToolResult.err("No path provided")

        # Security check
        if self._is_blocked_path(path):
            return ToolResult.err("Access to this path is blocked")

        # Resolve relative paths
        if not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)

        # Check existence
        if not os.path.exists(path):
            return ToolResult.err(f"File not found: {path}")

        if not os.path.isfile(path):
            return ToolResult.err(f"Not a file: {path}")

        # Check size
        try:
            size = os.path.getsize(path)
            if size > max_size:
                return ToolResult.err(
                    f"File too large: {size} bytes (max: {max_size} bytes). "
                    f"Use limit parameter to read in chunks."
                )
        except OSError as e:
            return ToolResult.err(f"Cannot access file: {e}")

        # Handle different file types
        if self._is_image_file(path):
            return await self._read_image(path, size)
        elif self._is_pdf_file(path):
            return await self._read_pdf(path, size)
        else:
            return await self._read_text(
                path, offset=offset, limit=limit, show_lines=show_lines
            )

    async def _read_text(
        self,
        path: str,
        offset: int = 1,
        limit: int = 2000,
        show_lines: bool = False,
    ) -> ToolResult:
        """Read a text file with optional line range."""
        try:
            # Large file warning
            size = os.path.getsize(path)
            if size > 5 * 1024 * 1024:
                sys.stderr.write(f"[read] Large file: {size/(1024*1024):.1f} MB\n")
                sys.stderr.flush()

            with open(path, "r", encoding="utf-8", errors="replace") as f:
                if offset > 1:
                    # Skip to offset
                    lines_skipped = 0
                    while lines_skipped < offset - 1:
                        f.readline()
                        lines_skipped += 1
                
                if limit > 0:
                    lines = []
                    for i in range(limit):
                        line = f.readline()
                        if not line:
                            break
                        if show_lines:
                            lines.append(f"{offset + i:6d}  {line}")
                        else:
                            lines.append(line)
                    content = "".join(lines)
                else:
                    content = f.read()

            if not content:
                return ToolResult.ok("(empty file)")

            # Truncate if still too large
            max_chars = 100000
            if len(content) > max_chars:
                content = content[:max_chars] + f"\n... [truncated, {len(content) - max_chars} chars omitted]"

            return ToolResult.ok(content)

        except Exception as e:
            return ToolResult.err(f"Error reading file: {e}")

    async def _read_image(self, path: str, size: int) -> ToolResult:
        """Read an image file (returns info, not raw bytes)."""
        try:
            import magic
            
            mime = magic.Magic(mime=True)
            mime_type = mime.from_file(path)
            
            info = f"[Image file: {path}]\n"
            info += f"Size: {size} bytes ({size/(1024*1024):.2f} MB)\n"
            info += f"MIME type: {mime_type}\n"
            
            # For small images, include base64
            if size < 500 * 1024:  # 500KB
                import base64
                with open(path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")
                info += f"\nBase64 (for display):\ndata:{mime_type};base64,{b64[:100]}..."
            
            return ToolResult.ok(info)
        except ImportError:
            return ToolResult.ok(f"[Image file: {path}] Size: {size} bytes")
        except Exception as e:
            return ToolResult.err(f"Error reading image: {e}")

    async def _read_pdf(self, path: str, size: int) -> ToolResult:
        """Read a PDF file."""
        try:
            # Try using PyPDF2 or pypdf
            try:
                from pypdf import PdfReader
                reader = PdfReader(path)
                num_pages = len(reader.pages)
                
                info = f"[PDF file: {path}]\n"
                info += f"Pages: {num_pages}\n"
                info += f"Size: {size} bytes\n\n"
                
                # Extract first page as sample
                if num_pages > 0:
                    first_page = reader.pages[0]
                    text = first_page.extract_text()
                    info += f"First page preview:\n{text[:2000]}"
                    if len(text) > 2000:
                        info += "\n... [truncated]"
                
                return ToolResult.ok(info)
            except ImportError:
                return ToolResult.ok(
                    f"[PDF file: {path}]\nSize: {size} bytes\n"
                    "(Install pypdf to extract text: pip install pypdf)"
                )
        except Exception as e:
            return ToolResult.err(f"Error reading PDF: {e}")
