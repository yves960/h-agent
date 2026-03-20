"""Tests for Agent class."""
import os
import sys
import pytest

os.environ["OPENAI_API_KEY"] = "test"
os.environ["OPENAI_BASE_URL"] = "http://localhost:8000"
os.environ["MODEL_ID"] = "test-model"

from pyagent import Agent, AgentConfig


class TestAgent:
    """Agent tests."""
    
    def test_create_agent(self):
        config = AgentConfig(agent_id="test", model="test-model")
        agent = Agent(config)
        
        assert agent.config.agent_id == "test"
        assert agent.config.model == "test-model"
    
    def test_agent_tools(self):
        agent = Agent()
        tools = agent.tools.list_tools()
        
        assert "bash" in tools
        assert "read" in tools
        assert "write" in tools
    
    def test_agent_memory(self):
        agent = Agent()
        agent.memory.set("test_key", "test_value")
        
        result = agent.memory.get("test_key")
        assert result == "test_value"
    
    def test_agent_session(self):
        agent = Agent()
        messages = agent.sessions.get_or_create("test-session")
        
        assert messages == []
        agent.sessions.add_message("test-session", "user", "hello")
        
        messages = agent.sessions.get_or_create("test-session")
        assert len(messages) == 1