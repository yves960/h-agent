"""
h_agent/commands/compact.py - /compact Command

Compress conversation history to save tokens.
"""

from h_agent.commands.base import Command, CommandContext, CommandResult
from h_agent.services.compact import compact_messages


class CompactCommand(Command):
    name = "compact"
    description = "Compress conversation history to save tokens"

    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        original_count = len(context.messages)
        
        if original_count == 0:
            return CommandResult(
                success=True,
                output="No messages to compact"
            )

        context.messages = await compact_messages(context.messages)
        new_count = len(context.messages)

        return CommandResult(
            success=True,
            output=f"Compacted: {original_count} → {new_count} messages"
        )
