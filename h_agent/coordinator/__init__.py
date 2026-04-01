"""
h_agent/coordinator/__init__.py - Multi-Agent Coordinator Module

Provides:
- MessageBus: File-based agent messaging
- Orchestrator: Task orchestration across agents
- AgentPool: Pool of available agents
"""

from h_agent.coordinator.messaging import MessageBus, Message
from h_agent.coordinator.orchestrator import Orchestrator, TaskSpec
from h_agent.coordinator.pool import AgentPool, Agent

__all__ = [
    "MessageBus",
    "Message",
    "Orchestrator",
    "TaskSpec",
    "AgentPool",
    "Agent",
]
