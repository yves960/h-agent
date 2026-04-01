"""
h_agent/commands/vim.py - Vim Mode Command

Toggle Vim mode for text editing.
"""

from __future__ import annotations

from h_agent.commands.base import Command, CommandContext, CommandResult
from h_agent.vim.mode import VimEngine


# Global vim engine instance
_vim_engine: VimEngine | None = None


def get_vim_engine() -> VimEngine:
    """Get or create the global vim engine."""
    global _vim_engine
    if _vim_engine is None:
        _vim_engine = VimEngine()
    return _vim_engine


class VimCommand(Command):
    """Vim mode control command."""

    name = "vim"
    description = "Toggle Vim mode for text editing"
    aliases = ["vim"]

    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute vim command."""
        vim_enabled = context.get("vim_enabled", False)

        if args == "on":
            context.set("vim_enabled", True)
            return CommandResult.ok("Vim mode: enabled")

        elif args == "off":
            context.set("vim_enabled", False)
            return CommandResult.ok("Vim mode: disabled")

        elif args == "status":
            status = "enabled" if vim_enabled else "disabled"
            return CommandResult.ok(f"Vim mode: {status}")

        elif args == "reset":
            engine = get_vim_engine()
            engine.reset()
            return CommandResult.ok("Vim state reset")

        elif args == "info":
            engine = get_vim_engine()
            state = engine.state
            info = [
                f"Mode: {state.mode.value}",
                f"Count: {state.count or '-'}",
                f"Register: {state.register or '-'}",
            ]
            return CommandResult.ok("\n".join(info))

        else:
            # Toggle
            new_state = not vim_enabled
            context.set("vim_enabled", new_state)
            return CommandResult.ok(f"Vim mode: {'enabled' if new_state else 'disabled'}")
