"""
h_agent/coordinator/pool.py - Agent Pool

Manages a pool of available agents for task execution.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
import asyncio


@dataclass
class Agent:
    """Represents an agent in the pool."""
    id: str
    role: str
    status: str = "idle"
    capabilities: List[str] = field(default_factory=list)
    current_task: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentPool:
    """
    Agent 池 - Pool of available agents.
    
    Manages agent lifecycle and task assignment.
    """
    
    def __init__(self, max_size: int = 10):
        """
        Initialize the agent pool.
        
        Args:
            max_size: Maximum number of agents in pool
        """
        self.max_size = max_size
        self.agents: Dict[str, Agent] = {}
        self._lock = asyncio.Lock()
    
    async def add_agent(
        self,
        agent_id: str,
        role: str,
        capabilities: List[str] = None,
        **metadata: Any,
    ) -> Agent:
        """
        Add an agent to the pool.
        
        Args:
            agent_id: Unique agent identifier
            role: Agent role
            capabilities: List of capabilities
            **metadata: Additional metadata
            
        Returns:
            Created Agent instance
        """
        async with self._lock:
            if agent_id in self.agents:
                raise ValueError(f"Agent already exists: {agent_id}")
            
            if len(self.agents) >= self.max_size:
                raise RuntimeError(f"Agent pool full (max: {self.max_size})")
            
            agent = Agent(
                id=agent_id,
                role=role,
                capabilities=capabilities or [],
                metadata=metadata,
            )
            self.agents[agent_id] = agent
            return agent
    
    async def remove_agent(self, agent_id: str) -> bool:
        """
        Remove an agent from the pool.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            True if removed, False if not found
        """
        async with self._lock:
            if agent_id in self.agents:
                del self.agents[agent_id]
                return True
            return False
    
    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """
        Get an agent by ID.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Agent instance or None
        """
        return self.agents.get(agent_id)
    
    async def find_available(
        self,
        role: str = None,
        capability: str = None,
    ) -> Optional[Agent]:
        """
        Find an available agent matching criteria.
        
        Args:
            role: Required role (optional)
            capability: Required capability (optional)
            
        Returns:
            Available Agent or None
        """
        async with self._lock:
            for agent in self.agents.values():
                if agent.status != "idle":
                    continue
                if role and agent.role != role:
                    continue
                if capability and capability not in agent.capabilities:
                    continue
                return agent
        return None
    
    async def assign_task(
        self,
        agent_id: str,
        task_id: str,
    ) -> bool:
        """
        Assign a task to an agent.
        
        Args:
            agent_id: Agent identifier
            task_id: Task identifier
            
        Returns:
            True if assigned, False otherwise
        """
        async with self._lock:
            agent = self.agents.get(agent_id)
            if agent and agent.status == "idle":
                agent.status = "busy"
                agent.current_task = task_id
                return True
        return False
    
    async def release_agent(self, agent_id: str) -> bool:
        """
        Release an agent after task completion.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            True if released, False otherwise
        """
        async with self._lock:
            agent = self.agents.get(agent_id)
            if agent:
                agent.status = "idle"
                agent.current_task = None
                return True
        return False
    
    async def list_agents(
        self,
        role: str = None,
        status: str = None,
    ) -> List[Dict]:
        """
        List agents with optional filtering.
        
        Args:
            role: Filter by role (optional)
            status: Filter by status (optional)
            
        Returns:
            List of agent info dicts
        """
        async with self._lock:
            agents = list(self.agents.values())
        
        if role:
            agents = [a for a in agents if a.role == role]
        if status:
            agents = [a for a in agents if a.status == status]
        
        return [
            {
                "id": a.id,
                "role": a.role,
                "status": a.status,
                "capabilities": a.capabilities,
                "current_task": a.current_task,
            }
            for a in agents
        ]
    
    async def get_stats(self) -> Dict:
        """
        Get pool statistics.
        
        Returns:
            Stats dict
        """
        async with self._lock:
            total = len(self.agents)
            idle = sum(1 for a in self.agents.values() if a.status == "idle")
            busy = sum(1 for a in self.agents.values() if a.status == "busy")
            
            roles: Dict[str, int] = {}
            for a in self.agents.values():
                roles[a.role] = roles.get(a.role, 0) + 1
            
            return {
                "total": total,
                "idle": idle,
                "busy": busy,
                "available_slots": self.max_size - total,
                "roles": roles,
            }
