"""
h_agent/commands/plugin.py - Plugin Management Command

Manage h-agent plugins.
"""

from __future__ import annotations

from h_agent.commands.base import Command, CommandContext, CommandResult
from h_agent.plugins.registry import get_plugin_registry


class PluginCommand(Command):
    """Plugin management command."""

    name = "plugin"
    description = "Manage plugins (list/enable/disable/reload)"
    aliases = []

    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute plugin command."""
        registry = get_plugin_registry()

        # Ensure plugins are discovered
        if not registry.plugins:
            count = registry.discover()

        if not args or args == "list":
            plugins = registry.list_plugins()
            if not plugins:
                return CommandResult.ok("No plugins installed. Place plugins in ~/.h-agent/plugins/")

            lines = ["Plugins:"]
            for p in plugins:
                status = "✓" if p.enabled else "✗"
                lines.append(f"  [{status}] {p.manifest.name} ({p.manifest.version}) - {p.manifest.description}")
            return CommandResult.ok("\n".join(lines))

        elif args.startswith("enable "):
            name = args[7:].strip()
            if registry.enable(name):
                return CommandResult.ok(f"Enabled: {name}")
            return CommandResult.err(f"Plugin not found: {name}")

        elif args.startswith("disable "):
            name = args[8:].strip()
            if registry.disable(name):
                return CommandResult.ok(f"Disabled: {name}")
            return CommandResult.err(f"Plugin not found: {name}")

        elif args.startswith("reload "):
            name = args[7:].strip()
            if registry.reload(name):
                return CommandResult.ok(f"Reloaded: {name}")
            return CommandResult.err(f"Plugin not found: {name}")

        elif args == "discover":
            count = registry.discover()
            return CommandResult.ok(f"Discovered {count} plugin(s)")

        elif args == "info":
            plugins = registry.list_plugins()
            if not plugins:
                return CommandResult.ok("No plugins installed")

            lines = ["Plugin Details:"]
            for p in plugins:
                lines.append(f"\n  {p.manifest.name} v{p.manifest.version}")
                lines.append(f"    Author: {p.manifest.author}")
                lines.append(f"    Path: {p.path}")
                lines.append(f"    Enabled: {p.enabled}")
                if p.manifest.commands:
                    lines.append(f"    Commands: {', '.join(p.manifest.commands)}")
                if p.manifest.tools:
                    lines.append(f"    Tools: {', '.join(p.manifest.tools)}")
            return CommandResult.ok("\n".join(lines))

        else:
            return CommandResult.ok(
                "Plugin commands:\n"
                "  /plugin list     - List all plugins\n"
                "  /plugin info     - Show detailed plugin info\n"
                "  /plugin discover - Scan for plugins\n"
                "  /plugin enable <name>  - Enable a plugin\n"
                "  /plugin disable <name> - Disable a plugin\n"
                "  /plugin reload <name>  - Reload a plugin"
            )
