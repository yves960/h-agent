"""Features module - Extended capabilities for h_agent."""

from h_agent.features.sessions import SessionStore, ContextGuard, SessionAwareAgent
from h_agent.features.channels import Channel, CLIChannel, ChannelManager, MultiChannelAgent
from h_agent.features.rag import CodebaseRAG, CodebaseIndex, VectorStore
from h_agent.features.subagents import run_subagent, SubagentResult
from h_agent.features.skills import list_available_skills, load_skill_content, get_skill_info

__all__ = [
    "SessionStore", "ContextGuard", "SessionAwareAgent",
    "Channel", "CLIChannel", "ChannelManager", "MultiChannelAgent",
    "CodebaseRAG", "CodebaseIndex", "VectorStore",
    "run_subagent", "SubagentResult",
    "list_available_skills", "load_skill_content", "get_skill_info",
]
