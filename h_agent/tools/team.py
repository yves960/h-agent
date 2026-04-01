"""
h_agent/tools/team.py - Team Management Tools

Provides tools for creating and managing agent teams.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

from h_agent.tools.base import Tool, ToolResult


@dataclass
class TeamMember:
    """Represents a team member."""
    id: str
    role: str
    status: str = "idle"
    name: Optional[str] = None


@dataclass
class Team:
    """Represents an agent team."""
    id: str
    name: str
    members: List[TeamMember] = field(default_factory=list)


class TeamCreateTool(Tool):
    """Create a team of agents."""
    
    name = "team_create"
    description = "Create a team of agents"
    
    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Team name"},
                "members": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "role": {"type": "string"},
                        },
                    },
                    "description": "Team members",
                },
            },
            "required": ["name", "members"],
        }
    
    async def execute(
        self,
        args: dict,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> ToolResult:
        """Create a new team."""
        try:
            from h_agent.team.async_team import AsyncAgentTeam
            
            team_id = args["name"]
            team = AsyncAgentTeam(team_id=team_id)
            
            # Store reference for later use
            _active_teams[team_id] = team
            
            # Spawn members
            spawned = []
            for member_spec in args.get("members", []):
                name = member_spec.get("name")
                role = member_spec.get("role")
                prompt = member_spec.get("prompt", f"You are {name}, role: {role}.")
                
                if name:
                    result = team.spawn(name, role, prompt)
                    spawned.append(f"{name}: {result}")
            
            lines = [f"Team '{team_id}' created with {len(spawned)} members:"]
            for s in spawned:
                lines.append(f"  - {s}")
            
            return ToolResult.ok("\n".join(lines))
        except Exception as e:
            return ToolResult.err(f"Failed to create team: {str(e)}")


class TeamDeleteTool(Tool):
    """Delete a team."""
    
    name = "team_delete"
    description = "Delete a team and all its members"
    
    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Team name to delete"},
            },
            "required": ["name"],
        }
    
    async def execute(
        self,
        args: dict,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> ToolResult:
        """Delete a team."""
        team_id = args["name"]
        
        if team_id in _active_teams:
            team = _active_teams[team_id]
            team.shutdown_all()
            del _active_teams[team_id]
            return ToolResult.ok(f"Team '{team_id}' deleted")
        
        return ToolResult.err(f"Team not found: {team_id}")


class TeamListTool(Tool):
    """List all teams and their members."""
    
    name = "team_list"
    description = "List all teams"
    
    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {},
        }
    
    async def execute(
        self,
        args: dict,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> ToolResult:
        """List all teams."""
        if not _active_teams:
            return ToolResult.ok("No active teams")
        
        lines = ["Active teams:"]
        for team_id, team in _active_teams.items():
            members = team.list_teammates()
            lines.append(f"\nTeam '{team_id}':")
            for m in members:
                lines.append(f"  - {m['name']} ({m['role']}): {m['status']}")
        
        return ToolResult.ok("\n".join(lines))


class SendMessageTool(Tool):
    """Send a message to a team member."""
    
    name = "send_message"
    description = "Send a message to a team member"
    
    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient name"},
                "content": {"type": "string", "description": "Message content"},
                "team": {"type": "string", "description": "Team name (optional)"},
            },
            "required": ["to", "content"],
        }
    
    async def execute(
        self,
        args: dict,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> ToolResult:
        """Send a message to a team member via inbox."""
        try:
            from h_agent.coordinator.messaging import MessageBus
            
            bus = MessageBus()
            sender = args.get("sender", "main")
            recipient = args["to"]
            content = args["content"]
            
            bus.send(sender, recipient, content)
            
            return ToolResult.ok(f"Message sent to {recipient}")
        except Exception as e:
            return ToolResult.err(f"Failed to send message: {str(e)}")


class ReadInboxTool(Tool):
    """Read messages from inbox."""
    
    name = "read_inbox"
    description = "Read messages from your inbox"
    
    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "recipient": {"type": "string", "description": "Inbox owner (defaults to 'main')"},
            },
        }
    
    async def execute(
        self,
        args: dict,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> ToolResult:
        """Read inbox messages."""
        try:
            from h_agent.coordinator.messaging import MessageBus
            
            bus = MessageBus()
            recipient = args.get("recipient", "main")
            messages = bus.read(recipient)
            
            if not messages:
                return ToolResult.ok("No messages in inbox")
            
            lines = ["Messages:"]
            for msg in messages:
                lines.append(f"\nFrom: {msg.sender}")
                lines.append(f"Content: {msg.content[:200]}...")
            
            return ToolResult.ok("\n".join(lines))
        except Exception as e:
            return ToolResult.err(f"Failed to read inbox: {str(e)}")


class BroadcastTool(Tool):
    """Broadcast a message to all team members."""
    
    name = "broadcast"
    description = "Broadcast a message to all team members"
    
    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Message to broadcast"},
                "team": {"type": "string", "description": "Team name"},
            },
            "required": ["content"],
        }
    
    async def execute(
        self,
        args: dict,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> ToolResult:
        """Broadcast to team."""
        try:
            from h_agent.team.async_team import AsyncAgentTeam
            
            team = None
            team_name = args.get("team")
            
            if team_name and team_name in _active_teams:
                team = _active_teams[team_name]
            
            if not team:
                # Try to use any active team
                if _active_teams:
                    team = list(_active_teams.values())[0]
                else:
                    return ToolResult.err("No active team found")
            
            result = team.bus.broadcast("lead", [], args["content"])
            return ToolResult.ok(result)
        except Exception as e:
            return ToolResult.err(f"Failed to broadcast: {str(e)}")


# Active teams storage
_active_teams: Dict[str, Any] = {}
