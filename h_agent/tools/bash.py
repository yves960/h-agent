"""
h_agent/tools/bash.py - Bash Tool

Executes shell commands with timeout and safety protections.
Inspired by Claude Code's BashTool.
"""

from __future__ import annotations

import os
import re
import subprocess
import threading
import sys
from typing import Optional

from h_agent.tools.base import Tool, ToolResult


# Dangerous commands that are blocked
DANGEROUS_PATTERNS = [
    r"rm\s+-rf\s+/",
    r"sudo\s+rm",
    r"mkfs",
    r"dd\s+if=",
    r">\s*/dev/sd",
    r":\(\)\{\s*:\|\:\&\;:\}",  # Fork bomb
    r"curl.*\|.*sh",  # Pipe to shell (common install pattern - risky)
]

# Commands that are always considered read-only
READ_ONLY_COMMANDS = {
    "ls", "cat", "head", "tail", "grep", "rg", "ag", "find", "which",
    "whereis", "file", "stat", "wc", "du", "df", "pwd", "cd", "echo",
    "printf", "true", "false", ":", "type", "command", "builtin",
    "history", "jobs", "fg", "bg", "wait",
}

# Commands that typically modify state (but may have read-only uses)
MIXED_COMMANDS = {
    "ps", "top", "htop", "netstat", "ss", "lsof", "who", "w", "id",
    "uname", "hostname", "uptime", "date", "cal", "uptime",
}

# Timeout default and max
DEFAULT_TIMEOUT = 120
MAX_TIMEOUT = 300


class BashTool(Tool):
    """
    Tool for executing shell commands.
    
    Features:
    - Configurable timeout
    - Dangerous command blocking
    - Large output streaming with progress
    - Working directory support
    - Read-only detection for parallel execution
    """

    name = "bash"
    description = "Execute a shell command. Use for file operations, git, running scripts, etc."

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute"
                },
                "timeout": {
                    "type": "integer",
                    "description": f"Timeout in seconds (default: {DEFAULT_TIMEOUT}, max: {MAX_TIMEOUT})",
                    "minimum": 1,
                    "maximum": MAX_TIMEOUT,
                },
                "cwd": {
                    "type": "string",
                    "description": "Working directory for the command (defaults to current)"
                },
            },
            "required": ["command"]
        }

    def _is_dangerous(self, command: str) -> bool:
        """Check if a command matches dangerous patterns."""
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return True
        return False

    def _get_command_name(self, command: str) -> str:
        """Extract the base command name."""
        # Handle pipes and semicolons
        first_cmd = command.split("|")[0].split(";")[0].split("&&")[0].split("||")[0]
        parts = first_cmd.strip().split()
        if not parts:
            return ""
        
        # Get base command (remove path)
        cmd = parts[0]
        return os.path.basename(cmd)

    def _is_read_only(self, command: str) -> bool:
        """Heuristic: is this command read-only?"""
        cmd_name = self._get_command_name(command)
        
        # Check exact matches
        if cmd_name in READ_ONLY_COMMANDS:
            return True
        
        # Check if it starts with common read prefixes
        if cmd_name.startswith("git ") or cmd_name == "git":
            # Most git commands are read-only except push/pull
            git_subcmd = command.split()[1] if len(command.split()) > 1 else ""
            return git_subcmd not in ("push", "pull", "fetch", "checkout", "reset", "rebase")
        
        return False

    def _stream_output(
        self,
        process: subprocess.Popen,
        label: str = "",
    ) -> tuple[str, str]:
        """Stream output from a process (for large outputs)."""
        label_str = f"[{label}] " if label else ""
        stdout_lines = []
        stderr_lines = []
        total_out = 0
        total_err = 0

        def read_stream(stream, lines_list, is_stdout: bool):
            nonlocal total_out, total_err
            while True:
                chunk = stream.read(1024 * 1024)  # 1MB chunks
                if not chunk:
                    break
                lines_list.append(chunk)
                if is_stdout:
                    total_out += len(chunk)
                else:
                    total_err += len(chunk)

        import threading
        t_stdout = threading.Thread(target=read_stream, args=(process.stdout, stdout_lines, True))
        t_stderr = threading.Thread(target=read_stream, args=(process.stderr, stderr_lines, False))
        t_stdout.daemon = True
        t_stderr.daemon = True
        t_stdout.start()
        t_stderr.start()

        process.wait()
        t_stdout.join(timeout=1)
        t_stderr.join(timeout=1)

        stdout = "".join(stdout_lines)
        stderr = "".join(stderr_lines)
        return stdout, stderr

    async def execute(self, args: dict) -> ToolResult:
        """
        Execute a shell command.
        
        Args:
            args: dict with keys:
                - command: str (required)
                - timeout: int (optional, default 120)
                - cwd: str (optional)
        """
        command = args.get("command", "")
        timeout = min(args.get("timeout", DEFAULT_TIMEOUT), MAX_TIMEOUT)
        cwd = args.get("cwd") or os.getcwd()

        if not command:
            return ToolResult.err("No command provided")

        # Security check
        if self._is_dangerous(command):
            return ToolResult.err(
                f"Dangerous command blocked: {command[:50]}..."
            )

        # Set up environment
        env = os.environ.copy()
        env["TERM"] = env.get("TERM", "dumb")

        # Detect if this is a "large output" command
        cmd_name = self._get_command_name(command)
        large_output_cmds = {"ls", "find", "grep", "rg", "ag", "cat", "diff", "git log", "git diff"}
        is_large = any(
            command.strip().startswith(c) or cmd_name == c
            for c in large_output_cmds
        )

        try:
            if is_large:
                # Use streaming for potentially large outputs
                process = subprocess.Popen(
                    command,
                    shell=True,
                    cwd=cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                    text=True,
                )
                stdout, stderr = self._stream_output(process, label=cmd_name)
                returncode = process.returncode
            else:
                # Direct execution for smaller commands
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    env=env,
                )
                stdout = result.stdout
                stderr = result.stderr
                returncode = result.returncode

            # Combine stdout and stderr
            output = (stdout + stderr).strip()

            # Truncate if too long
            max_output = int(os.environ.get("MAX_TOOL_OUTPUT", "50000"))
            if len(output) > max_output:
                output = output[:max_output] + f"\n... [truncated, {len(output) - max_output} chars omitted]"

            if returncode != 0 and not output:
                output = f"(command exited with code {returncode})"

            return ToolResult.ok(output)

        except subprocess.TimeoutExpired:
            return ToolResult.err(f"Command timed out after {timeout}s")
        except Exception as e:
            return ToolResult.err(f"Execution error: {str(e)}")

    def execute_sync(self, args: dict) -> ToolResult:
        """Synchronous execution for use in thread pools."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context, need to use run_in_executor
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(self._execute_sync_impl, args)
                    return future.result()
            else:
                return loop.run_until_complete(self.execute(args))
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(self.execute(args))

    def _execute_sync_impl(self, args: dict) -> ToolResult:
        """Internal sync implementation."""
        command = args.get("command", "")
        timeout = min(args.get("timeout", DEFAULT_TIMEOUT), MAX_TIMEOUT)
        cwd = args.get("cwd") or os.getcwd()

        if not command:
            return ToolResult.err("No command provided")

        if self._is_dangerous(command):
            return ToolResult.err(f"Dangerous command blocked")

        env = os.environ.copy()
        env["TERM"] = env.get("TERM", "dumb")

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
            )
            output = (result.stdout + result.stderr).strip()
            
            max_output = int(os.environ.get("MAX_TOOL_OUTPUT", "50000"))
            if len(output) > max_output:
                output = output[:max_output] + f"\n... [truncated]"
            
            return ToolResult.ok(output)

        except subprocess.TimeoutExpired:
            return ToolResult.err(f"Command timed out after {timeout}s")
        except Exception as e:
            return ToolResult.err(f"Execution error: {str(e)}")


# Convenience handler function for simple registration
def bash_handler(args: dict) -> ToolResult:
    """Simple handler function for bash tool."""
    tool = BashTool()
    return tool.execute_sync(args)
