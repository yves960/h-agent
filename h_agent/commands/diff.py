"""
h_agent/commands/diff.py - /diff Command

Show uncommitted changes.
"""

import subprocess

from h_agent.commands.base import Command, CommandContext, CommandResult


class DiffCommand(Command):
    name = "diff"
    description = "Show uncommitted changes"
    aliases = ["d"]

    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        result = subprocess.run(
            ["git", "diff"],
            capture_output=True, text=True
        )

        if not result.stdout:
            return CommandResult(
                success=True,
                output="No uncommitted changes"
            )

        return CommandResult(
            success=True,
            output=result.stdout[:5000]
        )
