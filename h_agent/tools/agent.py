"""
h_agent/tools/agent.py - Agent Spawning Tool

Provides a tool for spawning sub-agents to handle tasks.
"""

import asyncio
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

from h_agent.tools.base import Tool, ToolResult


class AgentTool(Tool):
    """
    Spawn a sub-agent to handle a task.
    
    This tool creates a new agent session and executes the given prompt,
    optionally with additional context and specific tools.
    """
    
    name = "agent"
    description = "Spawn a sub-agent to handle a task"
    
    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Task for the sub-agent"},
                "context": {"type": "string", "description": "Additional context"},
                "tools": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tools to give the agent",
                },
                "model": {"type": "string", "description": "Optional model override"},
            },
            "required": ["prompt"],
        }
    
    async def execute(
        self,
        args: dict,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> ToolResult:
        """
        Execute the agent tool by spawning a sub-agent.
        """
        if progress_callback:
            progress_callback("Spawning sub-agent...")
        
        result = await self._run_sub_agent(
            prompt=args["prompt"],
            context=args.get("context", ""),
            tools=args.get("tools"),
            model=args.get("model"),
            progress_callback=progress_callback,
        )
        
        return ToolResult.ok(result)
    
    async def _run_sub_agent(
        self,
        prompt: str,
        context: str,
        tools: Optional[List[str]] = None,
        model: Optional[str] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> str:
        """
        Run a sub-agent with the given prompt and context.
        
        This is a simplified implementation that uses the core client
        to execute a single-turn task.
        """
        try:
            from h_agent.core.client import get_client
            from h_agent.core.config import MODEL
            from h_agent.tools.registry import get_registry
            
            client = get_client()
            actual_model = model or MODEL
            
            # Build system prompt
            system_prompt = "You are a helpful assistant."
            if context:
                system_prompt += f"\n\nContext:\n{context}"
            
            # Build messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ]
            
            # Get tool schemas if tools specified
            tool_schemas = None
            if tools:
                registry = get_registry()
                tool_schemas = []
                for tool_name in tools:
                    tool = registry.get(tool_name)
                    if tool:
                        tool_schemas.append(tool.get_definition().to_openai_format())
            
            if progress_callback:
                progress_callback("Executing sub-agent...")
            
            # Execute
            kwargs = {
                "model": actual_model,
                "messages": messages,
                "max_tokens": 4000,
            }
            if tool_schemas:
                kwargs["tools"] = tool_schemas
            
            response = client.chat.completions.create(**kwargs)
            
            content = response.choices[0].message.content
            if not content:
                content = "(no output)"
            
            return content
            
        except Exception as e:
            return f"Error executing sub-agent: {str(e)}"


class AgentSpawnTool(Tool):
    """
    Spawn a persistent agent that continues running.
    """
    
    name = "agent_spawn"
    description = "Spawn a persistent sub-agent (long-running)"
    
    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Agent name"},
                "role": {"type": "string", "description": "Agent role"},
                "prompt": {"type": "string", "description": "Agent system prompt"},
            },
            "required": ["name", "role", "prompt"],
        }
    
    async def execute(
        self,
        args: dict,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> ToolResult:
        """Spawn a persistent agent."""
        try:
            from h_agent.team.async_team import AsyncAgentTeam
            
            team = AsyncAgentTeam()
            result = team.spawn(
                name=args["name"],
                role=args["role"],
                prompt=args["prompt"],
            )
            
            return ToolResult.ok(result)
        except Exception as e:
            return ToolResult.err(f"Failed to spawn agent: {str(e)}")


class AgentTalkTool(Tool):
    """
    Send a message to a spawned agent and wait for response.
    """
    
    name = "agent_talk"
    description = "Send a message to a spawned agent"
    
    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "agent": {"type": "string", "description": "Agent name"},
                "message": {"type": "string", "description": "Message to send"},
                "timeout": {"type": "number", "description": "Timeout in seconds", "default": 120},
            },
            "required": ["agent", "message"],
        }
    
    async def execute(
        self,
        args: dict,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> ToolResult:
        """Talk to a spawned agent."""
        try:
            from h_agent.team.async_team import AsyncAgentTeam
            
            team = AsyncAgentTeam()
            result = team.talk_to_async(
                agent_name=args["agent"],
                message=args["message"],
                timeout=args.get("timeout", 120),
            )
            
            if result.get("success"):
                return ToolResult.ok(result.get("content", ""))
            else:
                return ToolResult.err(result.get("error", "Unknown error"))
        except Exception as e:
            return ToolResult.err(f"Failed to talk to agent: {str(e)}")
