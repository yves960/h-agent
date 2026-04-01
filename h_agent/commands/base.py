"""
h_agent/commands/base.py - Command Base Class

Defines the base Command interface, following the same pattern
as the Tool system. Inspired by Claude Code's Command architecture.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional, ClassVar

if TYPE_CHECKING:
    from h_agent.core.engine import QueryEngine


@dataclass
class CommandResult:
    """
    Result of a command execution.
    
    Attributes:
        success: Whether the command succeeded
        output: The output text to display
        error: Optional error message if success is False
    """
    success: bool
    output: str
    error: Optional[str] = None

    @classmethod
    def ok(cls, output: str) -> "CommandResult":
        """Create a successful result."""
        return cls(success=True, output=output)

    @classmethod
    def err(cls, error: str, output: str = "") -> "CommandResult":
        """Create an error result."""
        return cls(success=False, output=output, error=error)


@dataclass
class CommandContext:
    """
    Context passed to command execution.
    
    Contains the REPL state and access to engine/tools.
    """
    messages: List[dict] = field(default_factory=list)
    running: bool = True
    engine: Optional["QueryEngine"] = None
    # Additional context can be added here
    extra: dict = field(default_factory=dict)

    def get(self, key: str, default=None):
        """Get context value."""
        return self.extra.get(key, default)

    def set(self, key: str, value) -> None:
        """Set context value."""
        self.extra[key] = value


class Command(ABC):
    """
    Abstract base class for all commands.
    
    Subclass this to create a new command. Implement the `execute` method.

    Attributes:
        name: Command name (without the / prefix)
        description: Short help description
        aliases: Alternative names for the command
    
    Example:
        class HelpCommand(Command):
            name = "help"
            description = "Show help message"
            aliases = ["?"]
            
            async def execute(self, args: str, context: CommandContext) -> CommandResult:
                return CommandResult.ok("Help text here...")
    """

    # Command metadata - override in subclass
    name: str = ""
    description: str = ""
    aliases: List[str] = []

    @abstractmethod
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """
        Execute the command.
        
        Args:
            args: Arguments after the command name (e.g., "/help tools" -> args="tools")
            context: Execution context with REPL state
            
        Returns:
            CommandResult with output or error
        """
        pass

    def get_help(self) -> str:
        """
        Get detailed help for this command.
        
        Override to provide detailed usage information.
        Default: just returns the description.
        """
        alias_str = f" ({', '.join(self.aliases)})" if self.aliases else ""
        return f"/{self.name}{alias_str} - {self.description}"
