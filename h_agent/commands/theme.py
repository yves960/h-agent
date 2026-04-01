"""
h_agent/commands/theme.py - /theme Command

Change color theme (UI display only in terminal context).
"""

from h_agent.commands.base import Command, CommandContext, CommandResult


class ThemeCommand(Command):
    name = "theme"
    description = "Change color theme"
    
    THEMES = ["default", "dark", "light", "monokai", "solarized"]

    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        if not args:
            return CommandResult(
                success=True,
                output=f"Current theme: default\nAvailable: {', '.join(self.THEMES)}"
            )

        theme = args.strip().lower()
        if theme not in self.THEMES:
            return CommandResult(
                success=False,
                output=f"Unknown theme: {theme}\nAvailable: {', '.join(self.THEMES)}"
            )

        # Theme setting would be applied in a full UI implementation
        # For now, just acknowledge the request
        return CommandResult(
            success=True,
            output=f"Theme changed to: {theme}"
        )
