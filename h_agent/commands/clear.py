"""
h_agent/commands/clear.py - /clear Command

Clear conversation history and reset context.
"""

from h_agent.commands.base import Command, CommandContext, CommandResult


class ClearCommand(Command):
    name = "clear"
    description = "Clear conversation history and reset context"
    aliases = ["cls", "reset"]

    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        # Clear messages
        context.messages.clear()
        
        # Reset token usage if engine is available
        if context.engine:
            context.engine.reset_usage()
        
        return CommandResult.ok("Conversation cleared.")
