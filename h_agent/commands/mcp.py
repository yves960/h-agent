"""MCP command - manage MCP servers."""

from h_agent.commands.base import Command, CommandResult, CommandContext
from h_agent.mcp import get_mcp_registry


class McpCommand(Command):
    name = "mcp"
    description = "Manage MCP servers"

    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        registry = get_mcp_registry()

        if not args or args == "list":
            lines = ["MCP Servers:"]
            for name, client in registry.clients.items():
                lines.append(f"  {name}:")
                lines.append(f"    Tools: {len(client.tools)}")
                lines.append(f"    Resources: {len(client.resources)}")

            if not registry.clients:
                lines.append("  (none connected)")

            return CommandResult(success=True, output="\n".join(lines))

        elif args.startswith("connect "):
            # Connect to a server from config
            # mcp connect filesystem
            server_name = args[8:].strip()
            return CommandResult(
                success=False,
                output=f"mcp connect: not implemented (configure servers in config.yaml)",
            )

        elif args.startswith("tools "):
            server_name = args[6:].strip()
            client = registry.get_client(server_name)
            if not client:
                return CommandResult(success=False, output=f"Server not found: {server_name}")

            lines = [f"Tools from {server_name}:"]
            for tool in client.tools:
                lines.append(f"  {tool.name}: {tool.description}")

            return CommandResult(success=True, output="\n".join(lines))

        return CommandResult(success=False, output=f"Unknown mcp command: {args}")
