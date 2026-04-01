"""
h_agent/commands/exit.py - /exit Command

Exit the REPL.
"""

from h_agent.commands.base import Command, CommandContext, CommandResult


class ExitCommand(Command):
    name = "exit"
    description = "Exit the REPL"
    aliases = ["quit", "q"]

    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        context.running = False
        return CommandResult.ok("Goodbye!")
