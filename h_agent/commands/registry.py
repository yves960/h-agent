"""
h_agent/commands/registry.py - Command Registry

Central registry for all commands. Provides registration, lookup,
and dispatch functionality. Mirrors the ToolRegistry pattern.

Inspired by Claude Code's commands.ts architecture.
"""

from __future__ import annotations

import asyncio
from typing import Dict, List, Optional, TYPE_CHECKING

from h_agent.commands.base import Command, CommandContext, CommandResult

if TYPE_CHECKING:
    from h_agent.core.engine import QueryEngine


class CommandRegistry:
    """
    Central registry for all available commands.
    
    Supports:
    - Registration/deregistration of commands
    - Lookup by name or alias
    - Sorted listing
    - Command execution
    
    Example:
        registry = CommandRegistry()
        registry.register(HelpCommand())
        
        # List all commands
        commands = registry.list_commands()
        
        # Execute a command
        result = await registry.execute("help", "", context)
    """

    def __init__(self):
        self._commands: Dict[str, Command] = {}
        self._aliases: Dict[str, str] = {}  # alias -> command name

    def register(self, command: Command) -> None:
        """
        Register a command.
        
        Args:
            command: Command instance to register
            
        Raises:
            ValueError: If command has no name or is already registered
        """
        if not command.name:
            raise ValueError(f"Command must have a name: {command}")
        
        if command.name in self._commands:
            raise ValueError(f"Command already registered: {command.name}")
        
        self._commands[command.name] = command
        
        # Register aliases
        for alias in command.aliases:
            if alias in self._aliases:
                raise ValueError(f"Alias already registered: {alias}")
            self._aliases[alias] = command.name

    def unregister(self, name: str) -> bool:
        """
        Unregister a command.
        
        Args:
            name: Command name or alias
            
        Returns:
            True if unregistered, False if not found
        """
        # Resolve alias
        if name in self._aliases:
            name = self._aliases.pop(name)
        
        if name in self._commands:
            # Remove aliases for this command
            cmd = self._commands[name]
            for alias in cmd.aliases:
                self._aliases.pop(alias, None)
            del self._commands[name]
            return True
        return False

    def get(self, name: str) -> Optional[Command]:
        """
        Get a command by name or alias.
        
        Args:
            name: Command name or alias
            
        Returns:
            Command instance or None if not found
        """
        # Check aliases first
        if name in self._aliases:
            name = self._aliases[name]
        
        return self._commands.get(name)

    def has(self, name: str) -> bool:
        """Check if a command is registered."""
        return self.get(name) is not None

    def list_commands(self) -> List[Command]:
        """
        List all registered commands, sorted by name.
        
        Returns:
            List of Command instances sorted alphabetically
        """
        return sorted(self._commands.values(), key=lambda c: c.name)

    def list_names(self) -> List[str]:
        """List all command names (not aliases)."""
        return sorted(self._commands.keys())

    async def execute(
        self,
        name: str,
        args: str,
        context: CommandContext,
    ) -> CommandResult:
        """
        Execute a command by name.
        
        Args:
            name: Command name or alias
            args: Arguments string
            context: Execution context
            
        Returns:
            CommandResult from execution
        """
        command = self.get(name)
        if not command:
            return CommandResult.err(f"Unknown command: /{name}")
        
        try:
            result = command.execute(args, context)
            if asyncio.iscoroutine(result):
                result = await result
            return result
        except Exception as e:
            return CommandResult.err(str(e))

    def find_partial(self, prefix: str) -> List[Command]:
        """
        Find commands that start with a prefix (for tab completion).
        
        Args:
            prefix: Prefix to match
            
        Returns:
            List of matching commands
        """
        prefix_lower = prefix.lower()
        matches = []
        
        for name, cmd in self._commands.items():
            if name.lower().startswith(prefix_lower):
                matches.append(cmd)
                continue
            for alias in cmd.aliases:
                if alias.lower().startswith(prefix_lower):
                    matches.append(cmd)
                    break
        
        return sorted(matches, key=lambda c: c.name)


# ============================================================
# Global Registry
# ============================================================

_registry: Optional[CommandRegistry] = None


def get_registry() -> CommandRegistry:
    """Get the global command registry."""
    global _registry
    if _registry is None:
        _registry = CommandRegistry()
        _register_builtin_commands(_registry)
    return _registry


def _register_builtin_commands(registry: CommandRegistry) -> None:
    """Register built-in commands."""
    from h_agent.commands.help import HelpCommand
    from h_agent.commands.clear import ClearCommand
    from h_agent.commands.tools import ToolsCommand
    from h_agent.commands.model import ModelCommand
    from h_agent.commands.cost import CostCommand
    from h_agent.commands.config import ConfigCommand
    from h_agent.commands.exit import ExitCommand
    from h_agent.commands.history import HistoryCommand
    from h_agent.commands.resume import ResumeCommand
    from h_agent.commands.sessions import SessionsCommand
    from h_agent.commands.mcp import McpCommand
    from h_agent.commands.skills import SkillsCommand
    from h_agent.commands.doctor import DoctorCommand
    from h_agent.commands.compact import CompactCommand
    from h_agent.commands.commit import CommitCommand
    from h_agent.commands.diff import DiffCommand
    from h_agent.commands.review import ReviewCommand
    from h_agent.commands.status import StatusCommand
    from h_agent.commands.theme import ThemeCommand
    from h_agent.commands.tasks import TasksCommand

    registry.register(HelpCommand())
    registry.register(ClearCommand())
    registry.register(ToolsCommand())
    registry.register(ModelCommand())
    registry.register(CostCommand())
    registry.register(ConfigCommand())
    registry.register(ExitCommand())
    registry.register(HistoryCommand())
    registry.register(ResumeCommand())
    registry.register(SessionsCommand())
    registry.register(McpCommand())
    registry.register(SkillsCommand())
    registry.register(DoctorCommand())
    registry.register(CompactCommand())
    registry.register(CommitCommand())
    registry.register(DiffCommand())
    registry.register(ReviewCommand())
    registry.register(StatusCommand())
    registry.register(ThemeCommand())
    registry.register(TasksCommand())


def register_command(command: Command) -> None:
    """Register a command with the global registry."""
    get_registry().register(command)


def list_commands() -> List[Command]:
    """List all registered commands."""
    return get_registry().list_commands()
