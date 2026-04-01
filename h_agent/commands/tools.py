"""
h_agent/commands/tools.py - /tools Command

List available tools and show tool details.
"""

from h_agent.commands.base import Command, CommandContext, CommandResult


class ToolsCommand(Command):
    name = "tools"
    description = "List available tools"

    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        from h_agent.tools import get_registry

        registry = get_registry()
        tools = registry.list_tools()

        if not tools:
            return CommandResult.ok("No tools available.")

        # Filter by args if provided
        if args:
            args_lower = args.lower()
            filtered = [t for t in tools if args_lower in t.lower()]
            if not filtered:
                return CommandResult.err(
                    f"No tools matching '{args}'. Available: {', '.join(sorted(tools))}"
                )
            tools = filtered

        lines = ["Available tools:"]
        for tool_name in sorted(tools):
            tool = registry.get(tool_name)
            if tool:
                desc = tool.description[:60] if tool.description else "No description"
                lines.append(f"  {tool_name:<20} {desc}")
        
        return CommandResult.ok("\n".join(lines))

    def get_help(self) -> str:
        return (
            f"/{self.name} - {self.description}\n"
            f"  Usage: /{self.name} [filter]\n"
            f"  Filter tools by name (optional)"
        )
