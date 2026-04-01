"""
h_agent/coordinator/orchestrator.py - Multi-Agent Orchestrator

Orchestrates tasks across multiple agents with role-based assignment
and message passing.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import asyncio


@dataclass
class TaskSpec:
    """Specification for a task to be dispatched."""
    prompt: str
    tools: List[str] = None
    context: Dict[str, Any] = None
    timeout: float = 120.0
    

@dataclass
class AgentSpec:
    """Specification for an agent in the pool."""
    id: str
    role: str
    tools: List[str] = None
    status: str = "idle"
    

class Orchestrator:
    """
    多 Agent 编排器 - Multi-agent orchestrator.
    
    Manages agents, dispatches tasks, and coordinates messaging.
    """
    
    def __init__(self):
        """Initialize the orchestrator."""
        self.agents: Dict[str, Any] = {}
        self.tasks: Dict[str, TaskSpec] = {}
        self.bus = None  # Lazy initialization
    
    @property
    def message_bus(self):
        """Get the message bus (lazy init)."""
        if self.bus is None:
            from h_agent.coordinator.messaging import MessageBus
            self.bus = MessageBus()
        return self.bus
    
    async def spawn_agent(
        self,
        agent_id: str,
        role: str,
        tools: List[str] = None,
    ) -> str:
        """
        生成一个 agent.
        
        Args:
            agent_id: Unique agent identifier
            role: Agent role (used for task assignment)
            tools: List of tool names to give the agent
            
        Returns:
            Confirmation string
        """
        from h_agent.team.async_team import AsyncAgentTeam
        
        if agent_id in self.agents:
            return f"Agent already exists: {agent_id}"
        
        # Create async team agent
        team = AsyncAgentTeam()
        prompt = f"You are '{agent_id}', role: {role}. Use tools to help with tasks."
        
        result = team.spawn(agent_id, role, prompt)
        
        self.agents[agent_id] = {
            "role": role,
            "status": "running",
            "tools": tools or [],
            "team": team,
        }
        
        return result
    
    async def dispatch(self, task: TaskSpec, target_agent: str = None) -> str:
        """
        派发任务到合适的 agent.
        
        Args:
            task: Task specification
            target_agent: Specific agent to dispatch to (optional)
            
        Returns:
            Task ID
        """
        task_id = f"task-{len(self.tasks) + 1}"
        self.tasks[task_id] = task
        
        if target_agent:
            # Dispatch directly to specified agent
            self.message_bus.send("orchestrator", target_agent, task.prompt)
            return task_id
        
        # Auto-select agent based on role
        if task.context and "role" in task.context:
            target_role = task.context["role"]
            for agent_id, agent_info in self.agents.items():
                if agent_info.get("role") == target_role:
                    self.message_bus.send("orchestrator", agent_id, task.prompt)
                    return task_id
        
        # Fallback: broadcast to all agents
        agent_ids = list(self.agents.keys())
        if agent_ids:
            self.message_bus.broadcast("orchestrator", agent_ids, task.prompt)
        
        return task_id
    
    async def broadcast(self, message: str) -> str:
        """
        广播消息到所有 agent.
        
        Args:
            message: Message to broadcast
            
        Returns:
            Confirmation string
        """
        agent_ids = list(self.agents.keys())
        if not agent_ids:
            return "No agents to broadcast to"
        
        return self.message_bus.broadcast("orchestrator", agent_ids, message)
    
    async def send_message(self, agent_id: str, message: str) -> str:
        """
        发送消息到特定 agent.
        
        Args:
            agent_id: Target agent identifier
            message: Message content
            
        Returns:
            Confirmation string
        """
        if agent_id not in self.agents:
            return f"Agent not found: {agent_id}"
        
        return self.message_bus.send("orchestrator", agent_id, message)
    
    async def get_agent_status(self, agent_id: str) -> Optional[Dict]:
        """
        Get status of an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Agent status dict or None
        """
        return self.agents.get(agent_id)
    
    async def list_agents(self) -> List[Dict]:
        """
        List all managed agents.
        
        Returns:
            List of agent info dicts
        """
        return [
            {
                "id": agent_id,
                "role": info.get("role"),
                "status": info.get("status"),
                "tools": info.get("tools", []),
            }
            for agent_id, info in self.agents.items()
        ]
    
    async def shutdown_agent(self, agent_id: str) -> str:
        """
        Shutdown an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Confirmation string
        """
        if agent_id not in self.agents:
            return f"Agent not found: {agent_id}"
        
        agent_info = self.agents[agent_id]
        team = agent_info.get("team")
        if team:
            team.shutdown_teammate(agent_id)
        
        del self.agents[agent_id]
        return f"Agent shutdown: {agent_id}"
    
    async def shutdown_all(self) -> str:
        """
        Shutdown all agents.
        
        Returns:
            Confirmation string
        """
        count = len(self.agents)
        for agent_id in list(self.agents.keys()):
            await self.shutdown_agent(agent_id)
        return f"Shutdown {count} agents"
