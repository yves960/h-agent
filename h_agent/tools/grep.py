"""
h_agent/tools/grep.py - Grep Tool

Search file contents using ripgrep (rg).
"""

import subprocess
from typing import Optional

from h_agent.tools.base import Tool, ToolResult


class GrepTool(Tool):
    """Search file contents using ripgrep."""
    
    name = "grep"
    description = "Search for text/regex patterns in files. Use ripgrep for fast content search."
    concurrency_safe = True
    read_only = True
    
    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Regex pattern to search for"
                },
                "path": {
                    "type": "string",
                    "description": "Directory or file to search in (default: current directory)"
                },
                "file_pattern": {
                    "type": "string",
                    "description": "File glob to match (e.g., *.py, *.txt, *.md)"
                },
                "ignore_case": {
                    "type": "boolean",
                    "description": "Case insensitive search (default: false)"
                },
                "line_numbers": {
                    "type": "boolean",
                    "description": "Show line numbers (default: true)"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of matches to return (default: 50)"
                },
                "context": {
                    "type": "integer",
                    "description": "Lines of context around matches (default: 0)"
                }
            },
            "required": ["pattern"]
        }
    
    async def execute(self, args: dict, progress_callback=None) -> ToolResult:
        pattern = args["pattern"]
        path = args.get("path", ".")
        file_pattern = args.get("file_pattern")
        ignore_case = args.get("ignore_case", False)
        line_numbers = args.get("line_numbers", True)
        max_results = args.get("max_results", 50)
        context = args.get("context", 0)
        
        # Build ripgrep command
        cmd = ["rg", "--json"]
        
        if ignore_case:
            cmd.append("--ignore-case")
        
        if line_numbers:
            cmd.append("--line-number")
        else:
            cmd.append("--no-line-number")
        
        if context > 0:
            cmd.extend(["--context", str(context)])
        
        # Limit results
        cmd.extend(["--max-count", str(max_results)])
        
        # Add pattern and path
        cmd.append(pattern)
        cmd.append(path)
        
        # Add file pattern if specified
        if file_pattern:
            cmd.extend(["--glob", file_pattern])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            if result.returncode == 1:
                # No matches found
                return ToolResult.ok(f"No matches for '{pattern}' in {path}")
            
            if result.returncode != 0:
                return ToolResult.err(f"Grep error: {result.stderr}")
            
            # Parse JSON output
            matches = []
            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    import json
                    entry = json.loads(line)
                    if entry.get("type") == "match":
                        data = entry.get("data", {})
                        path = data.get("path", {}).get("text", "?")
                        line_num = data.get("line_number", 0)
                        lines = data.get("lines", {}).get("text", "").rstrip()
                        matches.append(f"{path}:{line_num}:{lines}")
                except (json.JSONDecodeError, KeyError):
                    # Skip malformed lines
                    continue
            
            if not matches:
                return ToolResult.ok(f"No matches for '{pattern}' in {path}")
            
            return ToolResult.ok(f"Found {len(matches)} matches:\n" + "\n".join(matches))
        
        except subprocess.TimeoutExpired:
            return ToolResult.err("Grep timed out after 30 seconds")
        except FileNotFoundError:
            return ToolResult.err("ripgrep (rg) not found. Please install ripgrep.")
        except Exception as e:
            return ToolResult.err(f"Grep error: {e}")
