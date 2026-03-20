"""Tests for tools."""
import os
os.environ["OPENAI_API_KEY"] = "test"
os.environ["OPENAI_BASE_URL"] = "http://localhost"
os.environ["MODEL_ID"] = "test"

from pyagent.tools import BashTool, ReadTool, WriteTool, ToolRegistry

def test_bash_tool():
    tool = BashTool()
    result = tool.execute("echo hello")
    assert "hello" in result

def test_bash_dangerous():
    tool = BashTool()
    result = tool.execute("rm -rf /")
    assert "blocked" in result.lower()

def test_tool_registry():
    registry = ToolRegistry()
    registry.register_defaults(".")
    assert "bash" in registry.list_tools()
