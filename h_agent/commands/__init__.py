"""
h_agent/commands/__init__.py - Command System

Exports the command system components.
"""

from h_agent.commands.base import Command, CommandContext, CommandResult
from h_agent.commands.registry import (
    CommandRegistry,
    get_registry,
    register_command,
    list_commands,
)

__all__ = [
    "Command",
    "CommandContext",
    "CommandResult",
    "CommandRegistry",
    "get_registry",
    "register_command",
    "list_commands",
]
