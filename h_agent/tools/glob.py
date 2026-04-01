"""
h_agent/tools/glob.py - Glob Tool

Fast file pattern matching using glob patterns.
"""

from pathlib import Path
from typing import Optional

from h_agent.tools.base import Tool, ToolResult


class GlobTool(Tool):
    """Fast file pattern matching using glob patterns."""
    
    name = "glob"
    description = "Find files matching a glob pattern. Use ** for recursive search, *.py for single level."
    concurrency_safe = True
    read_only = True
    
    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern (e.g., **/*.py, *.txt, **/*.json)"
                },
                "path": {
                    "type": "string",
                    "description": "Base directory to search from (default: current directory)"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 100)"
                }
            },
            "required": ["pattern"]
        }
    
    async def execute(self, args: dict, progress_callback=None) -> ToolResult:
        pattern = args["pattern"]
        base_path = Path(args.get("path", ".")).resolve()
        max_results = args.get("max_results", 100)
        
        # Security: prevent escaping base path
        try:
            base_path = base_path.resolve()
        except (OSError, ValueError):
            return ToolResult.err(f"Invalid path: {base_path}")
        
        # Filter patterns that could escape base
        dangerous_patterns = ["~", "$", "|", ";"]
        for danger in dangerous_patterns:
            if danger in pattern:
                return ToolResult.err(f"Dangerous pattern rejected: {pattern}")
        
        try:
            matches = list(base_path.glob(pattern))
            
            # Filter out hidden files, node_modules, __pycache__, .git, etc.
            filtered = []
            skip_dirs = {'.git', 'node_modules', '__pycache__', '.venv', '.pytest_cache', 
                        '.mypy_cache', '.tox', 'dist', 'build', '.tox', '.eggs', '*.egg-info',
                        '.idea', '.vscode', '.DS_Store'}
            
            for m in matches:
                # Skip if any part of path matches skip_dirs
                parts = m.parts
                should_skip = False
                for part in parts:
                    if part in skip_dirs or part.startswith('.'):
                        should_skip = True
                        break
                if not should_skip:
                    filtered.append(m)
            
            # Sort by path
            filtered.sort()
            
            # Limit results
            filtered = filtered[:max_results]
            
            if not filtered:
                return ToolResult.ok(f"No files matching '{pattern}' found in {base_path}")
            
            result_lines = [str(m.relative_to(base_path)) if m.is_relative_to(base_path) else str(m) 
                          for m in filtered]
            
            return ToolResult.ok(f"Found {len(result_lines)} files:\n" + "\n".join(result_lines))
        
        except Exception as e:
            return ToolResult.err(f"Glob error: {e}")
