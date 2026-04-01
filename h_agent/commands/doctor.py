"""
h_agent/commands/doctor.py - /doctor Command

Run diagnostics on your environment to verify setup.
"""

import sys

from h_agent.commands.base import Command, CommandContext, CommandResult


class DoctorCommand(Command):
    name = "doctor"
    description = "Run diagnostics on your environment"

    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        checks = []

        # 1. Python version
        checks.append(f"✓ Python {sys.version.split()[0]}")

        # 2. Dependency checks
        try:
            import openai
            checks.append("✓ openai installed")
        except ImportError:
            checks.append("✗ openai not installed")

        try:
            import tiktoken
            checks.append("✓ tiktoken installed")
        except ImportError:
            checks.append("✗ tiktoken not installed")

        try:
            import yaml
            checks.append("✓ pyyaml installed")
        except ImportError:
            checks.append("✗ pyyaml not installed")

        # 3. API connection check
        from h_agent.core.client import get_client
        try:
            client = get_client()
            # Simple test - just verify client is created
            checks.append("✓ API client configured")
        except Exception as e:
            checks.append(f"✗ API error: {e}")

        # 4. Config check
        from h_agent.core.config import get_config
        try:
            config = get_config("MODEL_ID")
            checks.append(f"✓ Config loaded (model: {config})")
        except Exception as e:
            checks.append(f"✗ Config error: {e}")

        # 5. Tool check
        try:
            from h_agent.tools import get_registry
            registry = get_registry()
            tool_count = len(registry.list_tools())
            checks.append(f"✓ {tool_count} tools registered")
        except Exception as e:
            checks.append(f"⚠ Tools check skipped: {e}")

        # 6. Command registry check
        try:
            from h_agent.commands import get_registry as get_cmd_registry
            cmd_registry = get_cmd_registry()
            cmd_count = len(cmd_registry.list_commands())
            checks.append(f"✓ {cmd_count} commands registered")
        except Exception as e:
            checks.append(f"⚠ Commands check skipped: {e}")

        return CommandResult(
            success=True,
            output="\n".join(checks)
        )
