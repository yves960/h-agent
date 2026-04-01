"""
h_agent/commands/bridge.py - Bridge Command

IDE bridge control command.
"""

from __future__ import annotations

from h_agent.commands.base import Command, CommandContext, CommandResult
from h_agent.bridge.server import BridgeServer


# Global bridge server instance
_bridge_server: BridgeServer | None = None


def get_bridge_server() -> BridgeServer:
    """Get or create the global bridge server."""
    global _bridge_server
    if _bridge_server is None:
        _bridge_server = BridgeServer()
    return _bridge_server


class BridgeCommand(Command):
    """IDE Bridge control command."""

    name = "bridge"
    description = "IDE bridge control (start/stop/status)"
    aliases = []

    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute bridge command."""
        server = get_bridge_server()

        if not args or args == "status":
            status = "running" if server.running else "stopped"
            return CommandResult.ok(f"Bridge: {status} on port {server.port}")

        elif args == "start":
            if server.running:
                return CommandResult.ok("Bridge already running")
            server.start()
            return CommandResult.ok(f"Bridge started on port {server.port}")

        elif args == "stop":
            if not server.running:
                return CommandResult.ok("Bridge not running")
            server.stop()
            return CommandResult.ok("Bridge stopped")

        else:
            return CommandResult.err(f"Unknown bridge command: {args}")
