"""
h_agent/commands/status.py - /status Command

Show session status and statistics.
"""

from h_agent.commands.base import Command, CommandContext, CommandResult


class StatusCommand(Command):
    name = "status"
    description = "Show session status"
    aliases = ["st"]

    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        lines = [
            f"Messages: {len(context.messages)}",
        ]

        # Engine info if available
        if context.engine:
            lines.append(f"Model: {context.engine.model}")
            lines.append(f"Tokens: {context.engine.token_counter.total_tokens}")
            
            # Tools count
            from h_agent.tools import get_registry
            registry = get_registry()
            lines.append(f"Tools: {len(registry.list_tools())}")

        # Command registry info
        from h_agent.commands import get_registry as get_cmd_registry
        cmd_registry = get_cmd_registry()
        lines.append(f"Commands: {len(cmd_registry.list_commands())}")

        return CommandResult(
            success=True,
            output="\n".join(lines)
        )
