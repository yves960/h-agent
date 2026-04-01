"""
h_agent/commands/help.py - /help Command

Show help and available commands with enhanced features.
"""

from typing import List

from h_agent.commands.base import Command, CommandContext, CommandResult


class HelpCommand(Command):
    name = "help"
    description = "Show help and available commands"
    aliases = ["?"]

    # Command categories for grouping
    CATEGORIES = {
        "Core": ["exit", "quit", "clear", "history", "status"],
        "Information": ["help", "tools", "model", "cost", "usage", "config"],
        "Session": ["sessions", "resume", "compact"],
        "Development": ["commit", "diff", "review", "tasks"],
        "Advanced": ["doctor", "mcp", "skills", "theme", "vim", "voice", "plugin", "bridge"],
        "Memory": ["memory"],
        "System": ["upgrade", "feedback"],
    }

    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        from h_agent.commands import get_registry

        registry = get_registry()
        commands = registry.list_commands()

        if args:
            # Show help for specific command
            return await self._show_command_help(args.strip(), registry)

        # Show general help with categories
        return self._show_general_help(commands)

    def _show_general_help(self, commands) -> CommandResult:
        """Show general help with command groupings."""
        # Build command lookup
        cmd_dict = {cmd.name: cmd for cmd in commands}
        aliases_dict = {}
        for cmd in commands:
            for alias in cmd.aliases:
                aliases_dict[alias] = cmd.name

        lines = [
            "=" * 60,
            "h-agent Help",
            "=" * 60,
            "",
            "Usage: /<command> [args] or /<command> <subcommand>",
            "",
            "📌 Command Categories:",
            "",
        ]

        # Show grouped commands
        for category, cmd_names in self.CATEGORIES.items():
            lines.append(f"\n  [{category}]")
            for cmd_name in cmd_names:
                if cmd_name in cmd_dict:
                    cmd = cmd_dict[cmd_name]
                    alias_str = f" ({', '.join(cmd.aliases)})" if cmd.aliases else ""
                    lines.append(f"    /{cmd.name:<16}{alias_str:<12} {cmd.description}")
                elif cmd_name in aliases_dict:
                    real_name = aliases_dict[cmd_name]
                    lines.append(f"    /{cmd_name:<16} (alias for /{real_name})")

        # Show ungrouped commands
        grouped = set()
        for cmd_names in self.CATEGORIES.values():
            grouped.update(cmd_names)
            grouped.update(aliases_dict.get(a, a) for a in cmd_names)

        ungrouped = [cmd for cmd in commands if cmd.name not in grouped]
        if ungrouped:
            lines.append(f"\n  [Other]")
            for cmd in ungrouped:
                alias_str = f" ({', '.join(cmd.aliases)})" if cmd.aliases else ""
                lines.append(f"    /{cmd.name:<16}{alias_str:<12} {cmd.description}")

        lines.append("")
        lines.append("-" * 60)
        lines.append("\n🔧 Examples:")

        examples = [
            ("/help memory", "Show memory command help"),
            ("/tools list", "List all available tools"),
            ("/history", "Show conversation history"),
            ("/doctor", "Run environment diagnostics"),
            ("/commit", "Create git commit"),
        ]

        for cmd, desc in examples:
            lines.append(f"  {cmd:<20} {desc}")

        lines.append("")
        lines.append("-" * 60)
        lines.append("\n💡 Tips:")
        lines.append("  • Use Tab for autocomplete")
        lines.append("  • Use ↑/↓ to navigate history")
        lines.append("  • Use /compact to reduce context")
        lines.append("  • Use Ctrl+C to interrupt")
        lines.append("")

        lines.append("Type /help <command> for detailed help on a specific command.")
        lines.append("")

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
        lines = [
            "=" * 60,
            f"Help: /{command.name}",
            "=" * 60,
            "",
            f"Description: {command.description}",
        ]

        if command.aliases:
            lines.append(f"Aliases: {', '.join('/' + a for a in command.aliases)}")

        # Get command-specific help
        detailed_help = command.get_help()
        if detailed_help and detailed_help != f"/{command.name} - {command.description}":
            lines.append("")
            lines.append("Usage:")
            lines.append(detailed_help)

        lines.append("")
        lines.append("-" * 60)

        return CommandResult.ok("\n".join(lines))

    def get_help(self) -> str:
        return """Usage: /help [command]

Show help for h-agent commands.

With no arguments, shows all available commands grouped by category.

With a command name, shows detailed help for that command.

Examples:
  /help           Show all commands
  /help memory    Show memory command help
  /help tools     Show tools command help
  /help doctor    Show doctor command help
"""
