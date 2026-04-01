"""
h_agent/commands/help.py - /help Command

Show help and available commands.
"""

from typing import List

from h_agent.commands.base import Command, CommandContext, CommandResult


class HelpCommand(Command):
    name = "help"
    description = "Show help and available commands"
    aliases = ["?"]

    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        from h_agent.commands import get_registry

        registry = get_registry()
        commands = registry.list_commands()

        if args:
            # Show help for specific command
            return await self._show_command_help(args.strip(), registry)
        
        # Show general help
        lines = [
            "Available commands:",
            "",
            "  /exit, /quit       Exit the REPL",
            "  /clear             Clear conversation history",
            "  /tools             List available tools",
            "  /model             Show current model",
            "  /cost              Show token usage cost",
            "  /history           Show conversation history",
            "  /config            Show configuration",
            "",
            "Slash commands:",
        ]
        
        for cmd in commands:
            alias_str = f" ({', '.join(cmd.aliases)})" if cmd.aliases else ""
            lines.append(f"  /{cmd.name:<16}{alias_str}  {cmd.description}")
        
        lines.append("")
        lines.append("Type /help <command> for detailed help on a command.")
        
        return CommandResult.ok("\n".join(lines))

    async def _show_command_help(
        self, cmd_name: str, registry
    ) -> CommandResult:
        """Show detailed help for a specific command."""
        command = registry.get(cmd_name)
        
        if not command:
            # Try partial match
            matches = registry.find_partial(cmd_name)
            if len(matches) == 1:
                command = matches[0]
            elif len(matches) > 1:
                names = ", ".join(f"/{c.name}" for c in matches)
                return CommandResult.err(
                    f"Ambiguous command: {cmd_name}. Matches: {names}"
                )
        
        if not command:
            return CommandResult.err(f"Unknown command: /{cmd_name}")
        
        # Show detailed help
        help_text = command.get_help()
        return CommandResult.ok(help_text)
