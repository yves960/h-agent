"""
h_agent/tools/registry.py - Tool Registry

Central registry for all tools. Provides registration, lookup,
and dispatch functionality.

Inspired by Claude Code's tool system.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, List, Optional, Type

from h_agent.tools.base import Tool, ToolDefinition, ToolResult


class ToolRegistry:
    """
    Central registry for all available tools.
    
    Supports:
    - Registration/deregistration of tools
    - Getting tool schemas for LLM
    - Tool dispatch by name
    - Permission checking
    
    Example:
        registry = ToolRegistry()
        registry.register(MyTool())
        
        # Get all tool schemas for OpenAI API
        schemas = registry.get_tool_schemas()
        
        # Execute a tool
        result = await registry.dispatch("my_tool", {"arg": "value"})
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._handlers: Dict[str, Callable] = {}
        self._aliases: Dict[str, str] = {}

    def register(self, tool: Tool, alias: Optional[str] = None) -> None:
        """
        Register a tool instance.
        
        Args:
            tool: Tool instance to register
            alias: Optional alias for the tool
        """
        if not tool.name:
            raise ValueError(f"Tool must have a name: {tool}")
        
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        
        self._tools[tool.name] = tool
        
        if alias:
            self._aliases[alias] = tool.name

    def register_handler(
        self,
        name: str,
        handler: Callable[..., ToolResult],
        schema: Optional[dict] = None,
    ) -> None:
        """
        Register a simple function handler as a tool.
        
        Args:
            name: Tool name
            handler: Function that takes args dict and returns ToolResult
            schema: Optional JSON Schema for the tool
        """
        self._handlers[name] = handler
        
        # Create a simple tool wrapper if schema provided
        if schema:
            class HandlerTool(Tool):
                def __init__(self, tool_name: str, tool_description: str, tool_schema: dict, tool_handler: Callable):
                    self.name = tool_name
                    self.description = tool_description
                    self._schema = tool_schema
                    self._handler = tool_handler
                
                @property
                def input_schema(self) -> dict:
                    return self._schema.get("parameters", self._schema)
                
                async def execute(self, args: dict) -> ToolResult:
                    try:
                        result = self._handler(args)
                        if asyncio.iscoroutine(result):
                            result = await result
                        if isinstance(result, ToolResult):
                            return result
                        return ToolResult.ok(str(result))
                    except Exception as e:
                        return ToolResult.err(str(e))
            
            tool_instance = HandlerTool(name, schema.get("description", ""), schema, handler)
            self._tools[name] = tool_instance

    def unregister(self, name: str) -> bool:
        """
        Unregister a tool.
        
        Args:
            name: Tool name
            
        Returns:
            True if tool was unregistered, False if not found
        """
        if name in self._tools:
            del self._tools[name]
            return True
        if name in self._aliases:
            del self._aliases[name]
            return True
        return False

    def get(self, name: str) -> Optional[Tool]:
        """
        Get a tool by name.
        
        Args:
            name: Tool name or alias
            
        Returns:
            Tool instance or None if not found
        """
        # Check aliases first
        if name in self._aliases:
            name = self._aliases[name]
        
        return self._tools.get(name)

    def get_handler(self, name: str) -> Optional[Callable]:
        """Get a handler function by name."""
        return self._handlers.get(name)

    def has(self, name: str) -> bool:
        """Check if a tool is registered."""
        if name in self._aliases:
            name = self._aliases[name]
        return name in self._tools or name in self._handlers

    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def get_tool_schemas(self) -> List[dict]:
        """
        Get all tool schemas in OpenAI format.
        
        Returns:
            List of OpenAI tool definition dictionaries
        """
        schemas = []
        for tool in self._tools.values():
            schemas.append(tool.get_definition().to_openai_format())
        return schemas

    def get_definitions(self) -> List[ToolDefinition]:
        """Get all tool definitions."""
        return [tool.get_definition() for tool in self._tools.values()]

    async def dispatch(self, name: str, args: dict) -> ToolResult:
        """
        Dispatch a tool call by name.
        
        Args:
            name: Tool name
            args: Arguments dict
            
        Returns:
            ToolResult from execution
            
        Raises:
            ValueError: If tool not found
        """
        # Resolve alias
        if name in self._aliases:
            name = self._aliases[name]
        
        # Check handlers first (simple function-based tools)
        if name in self._handlers:
            handler = self._handlers[name]
            try:
                result = handler(args)
                if asyncio.iscoroutine(result):
                    result = await result
                if isinstance(result, ToolResult):
                    return result
                return ToolResult.ok(str(result))
            except Exception as e:
                return ToolResult.err(str(e))
        
        # Check registered tools
        tool = self._tools.get(name)
        if not tool:
            return ToolResult.err(f"Unknown tool: {name}")
        
        try:
            return await tool.execute(args)
        except Exception as e:
            return ToolResult.err(str(e))

    def dispatch_sync(self, name: str, args: dict) -> ToolResult:
        """
        Synchronous dispatch (for use in thread pool).
        
        Args:
            name: Tool name
            args: Arguments dict
            
        Returns:
            ToolResult from execution
        """
        # Resolve alias
        if name in self._aliases:
            name = self._aliases[name]
        
        # Check handlers first
        if name in self._handlers:
            handler = self._handlers[name]
            try:
                result = handler(args)
                if asyncio.iscoroutine(result):
                    raise RuntimeError(f"Async handler called sync: {name}")
                if isinstance(result, ToolResult):
                    return result
                return ToolResult.ok(str(result))
            except Exception as e:
                return ToolResult.err(str(e))
        
        # This won't work for async tools - use dispatch() instead
        tool = self._tools.get(name)
        if not tool:
            return ToolResult.err(f"Unknown tool: {name}")
        
        raise RuntimeError(f"Use dispatch() for async tool: {name}")


# Global registry instance
_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """Get the global tool registry."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        _register_builtin_tools(_registry)
    return _registry


def _register_builtin_tools(registry: ToolRegistry) -> None:
    """Register built-in tools."""
    from h_agent.tools.bash import BashTool
    from h_agent.tools.file_read import FileReadTool
    from h_agent.tools.file_write import FileWriteTool
    from h_agent.tools.file_edit import FileEditTool
    from h_agent.tools.glob import GlobTool
    from h_agent.tools.grep import GrepTool
    from h_agent.tools.web_fetch import WebFetchTool
    from h_agent.tools.web_search import WebSearchTool
    from h_agent.tools.skill import SkillTool
    from h_agent.tools.mcp_tool import MCPTool
    from h_agent.tools.lsp import LSPTool
    from h_agent.tools.notebook import NotebookEditTool
    from h_agent.tools.plan import EnterPlanModeTool, ExitPlanModeTool
    from h_agent.tools.worktree import EnterWorktreeTool, ExitWorktreeTool
    from h_agent.tools.todo import TodoWriteTool
    from h_agent.tools.ask import AskUserQuestionTool
    from h_agent.tools.sleep import SleepTool
    from h_agent.tools.schedule import ScheduleCronTool

    # Multi-agent tools
    from h_agent.tools.task import TaskCreateTool, TaskGetTool, TaskListTool, TaskStopTool
    from h_agent.tools.agent import AgentTool, AgentSpawnTool, AgentTalkTool
    from h_agent.tools.team import TeamCreateTool, TeamDeleteTool, TeamListTool, SendMessageTool, ReadInboxTool, BroadcastTool

    registry.register(BashTool())
    registry.register(FileReadTool())
    registry.register(FileWriteTool())
    registry.register(FileEditTool())
    registry.register(GlobTool())
    registry.register(GrepTool())
    registry.register(WebFetchTool())
    registry.register(WebSearchTool())
    registry.register(SkillTool())
    registry.register(MCPTool())
    registry.register(LSPTool())
    registry.register(NotebookEditTool())
    registry.register(EnterPlanModeTool())
    registry.register(ExitPlanModeTool())
    registry.register(EnterWorktreeTool())
    registry.register(ExitWorktreeTool())
    registry.register(TodoWriteTool())
    registry.register(AskUserQuestionTool())
    registry.register(SleepTool())
    registry.register(ScheduleCronTool())
    # Multi-agent tools
    registry.register(TaskCreateTool())
    registry.register(TaskGetTool())
    registry.register(TaskListTool())
    registry.register(TaskStopTool())
    registry.register(AgentTool())
    registry.register(AgentSpawnTool())
    registry.register(AgentTalkTool())
    registry.register(TeamCreateTool())
    registry.register(TeamDeleteTool())
    registry.register(TeamListTool())
    registry.register(SendMessageTool())
    registry.register(ReadInboxTool())
    registry.register(BroadcastTool())


def register_tool(tool: Tool) -> None:
    """Register a tool with the global registry."""
    get_registry().register(tool)


def register_handler(
    name: str,
    handler: Callable,
    schema: Optional[dict] = None,
) -> None:
    """Register a handler function with the global registry."""
    get_registry().register_handler(name, handler, schema)


def list_registered_tools() -> List[str]:
    """List all registered tool names."""
    return get_registry().list_tools()


def get_tool_schemas() -> List[dict]:
    """Get all tool schemas in OpenAI format."""
    return get_registry().get_tool_schemas()
