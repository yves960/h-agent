"""
h_agent/tools/base.py - Tool Base Class

Defines the base Tool interface and ToolResult for the modern tool system.
Inspired by Claude Code's Tool.ts architecture.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Callable, Optional

# Permission system integration
try:
    from h_agent.permissions import (
        PermissionContext,
        PermissionChecker,
        PermissionResult,
        PermissionDecision,
    )
    HAS_PERMISSIONS = True
except ImportError:
    HAS_PERMISSIONS = False
    PermissionContext = None
    PermissionChecker = None
    PermissionResult = None
    PermissionDecision = None


@dataclass
class ToolResult:
    """
    Result of a tool execution.
    
    Attributes:
        success: Whether the tool execution succeeded
        output: The output content (text or error message)
        error: Optional error message if success is False
    """
    success: bool
    output: str
    error: Optional[str] = None

    @classmethod
    def ok(cls, output: str) -> "ToolResult":
        """Create a successful result."""
        return cls(success=True, output=output)

    @classmethod
    def err(cls, error: str, output: str = "") -> "ToolResult":
        """Create an error result."""
        return cls(success=False, output=output, error=error)

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
        }


@dataclass
class ToolDefinition:
    """
    OpenAI-compatible tool definition.
    
    Attributes:
        type: Always "function" for OpenAI compatibility
        name: Tool name
        description: Tool description for the LLM
        parameters: JSON Schema for tool arguments
    """
    type: str = "function"
    name: str = ""
    description: str = ""
    parameters: dict = field(default_factory=dict)

    def to_openai_format(self) -> dict:
        """Convert to OpenAI tool format."""
        return {
            "type": self.type,
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }


class Tool(ABC):
    """
    Abstract base class for all tools.
    
    Subclass this to create a new tool. Implement the `execute` method
    with the tool's logic.
    
    Example:
        class ReadTool(Tool):
            name = "read"
            description = "Read a file"
            
            @property
            def input_schema(self) -> dict:
                return {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path"}
                    },
                    "required": ["path"]
                }
            
            async def execute(self, args: dict) -> ToolResult:
                path = args["path"]
                try:
                    with open(path) as f:
                        return ToolResult.ok(f.read())
                except Exception as e:
                    return ToolResult.err(str(e))
    """

    # Tool metadata - override in subclass
    name: str = ""
    description: str = ""

    @property
    @abstractmethod
    def input_schema(self) -> dict:
        """
        Return the JSON Schema for this tool's input arguments.
        
        Should return an object with:
        - type: "object"
        - properties: dict of argument name -> schema
        - required: list of required argument names
        """
        pass

    @abstractmethod
    async def execute(self, args: dict) -> ToolResult:
        """
        Execute the tool with the given arguments.
        
        Args:
            args: Dictionary of arguments matching input_schema
            
        Returns:
            ToolResult with the execution outcome
        """
        pass

    def get_definition(self) -> ToolDefinition:
        """Get the OpenAI-compatible tool definition."""
        return ToolDefinition(
            type="function",
            name=self.name,
            description=self.description,
            parameters=self.input_schema,
        )

    async def execute_with_progress(
        self,
        args: dict,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> ToolResult:
        """
        Execute with optional progress reporting.
        
        Override this in subclasses to support long-running operations
        with progress updates.
        """
        return await self.execute(args)

    def check_permissions(
        self,
        args: dict,
        context: Optional[PermissionContext] = None,
    ) -> PermissionResult:
        """
        Check if this tool execution is permitted.
        
        Args:
            args: Tool arguments
            context: Permission context (uses default if None)
            
        Returns:
            PermissionResult with decision and reasoning
        """
        if not HAS_PERMISSIONS or context is None:
            # No permission system or no context = allow
            return PermissionResult(
                decision=PermissionDecision.ALLOW if PermissionDecision else "allow",
                reason="No permission context provided",
                risk_level="low",
                requires_confirmation=False,
            )
        
        checker = PermissionChecker(context)
        return checker.check(self.name, args)


class AsyncTool(Tool):
    """
    Tool that runs a synchronous function in a thread pool.
    
    Use this as a base class when you have a synchronous tool function
    but want non-blocking execution.
    """

    async def execute_async(self, args: dict) -> ToolResult:
        """
        Override this for async execution instead of using thread pool.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.execute_sync, args)

    def execute_sync(self, args: dict) -> ToolResult:
        """
        Synchronous execution - override in subclass.
        """
        raise NotImplementedError

    async def execute(self, args: dict) -> ToolResult:
        """Execute synchronously in thread pool."""
        return await self.execute_async(args)


class ProgressTool(Tool):
    """
    Tool that supports streaming progress updates.
    
    Use this base class for tools that may take a long time
    and want to report progress to the user.
    """

    async def execute(
        self,
        args: dict,
        progress: Optional[AsyncGenerator[str, None]] = None,
    ) -> ToolResult:
        """
        Override to handle progress streaming.
        """
        raise NotImplementedError


# ============================================================
# Tool Categories (for permission system)
# ============================================================

class ReadOnlyTool(Tool):
    """Marker class for read-only tools (no filesystem modifications)."""
    pass


class WriteTool(Tool):
    """Marker class for tools that write to filesystem."""
    pass


class ExecutionTool(Tool):
    """Marker class for tools that execute commands/scripts."""
    pass
