"""
Unit tests for h_agent.tools.registry module.
"""

import pytest
from h_agent.tools.registry import ToolRegistry, get_registry, register_tool
from h_agent.tools.base import Tool, ToolResult


class MockTool(Tool):
    """Mock tool for testing purposes."""
    name = "mock_tool"
    description = "A mock tool for testing"
    
    @property
    def input_schema(self):
        return {
            "type": "object",
            "properties": {
                "param": {"type": "string"}
            },
            "required": ["param"]
        }
    
    async def execute(self, args):
        return ToolResult.ok(f"Executed with {args}")


class AnotherMockTool(Tool):
    """Another mock tool for testing."""
    name = "another_tool"
    description = "Another mock tool"
    
    @property
    def input_schema(self):
        return {
            "type": "object",
            "properties": {},
        }
    
    async def execute(self, args):
        return ToolResult.ok("Another tool executed")


def test_tool_registry_initialization():
    """Test ToolRegistry initialization."""
    registry = ToolRegistry()
    assert len(registry.list_tools()) == 0
    assert registry.get("nonexistent") is None


def test_tool_registration():
    """Test tool registration."""
    registry = ToolRegistry()
    
    tool = MockTool()
    registry.register(tool)
    
    # Check if tool is registered
    assert "mock_tool" in registry.list_tools()
    assert registry.has("mock_tool") is True
    assert registry.get("mock_tool") is not None
    assert registry.get("mock_tool").name == "mock_tool"


def test_duplicate_tool_registration():
    """Test that registering a duplicate tool raises an error."""
    registry = ToolRegistry()
    
    tool1 = MockTool()
    registry.register(tool1)
    
    tool2 = MockTool()  # Same name
    with pytest.raises(ValueError, match="Tool already registered"):
        registry.register(tool2)


def test_tool_with_alias():
    """Test tool registration with alias."""
    registry = ToolRegistry()
    
    tool = MockTool()
    registry.register(tool, alias="mt")
    
    # Should be accessible by both name and alias
    assert registry.get("mock_tool") is not None
    assert registry.get("mt") is not None
    assert registry.get("mt").name == "mock_tool"


def test_tool_unregistration():
    """Test tool unregistration."""
    registry = ToolRegistry()
    
    tool = MockTool()
    registry.register(tool)
    
    # Unregister
    result = registry.unregister("mock_tool")
    assert result is True
    assert "mock_tool" not in registry.list_tools()
    assert registry.get("mock_tool") is None
    
    # Try to unregister non-existent tool
    result = registry.unregister("nonexistent")
    assert result is False


def test_tool_dispatch():
    """Test tool dispatch functionality."""
    registry = ToolRegistry()
    
    tool = MockTool()
    registry.register(tool)
    
    # Test successful dispatch
    import asyncio
    result = asyncio.run(registry.dispatch("mock_tool", {"param": "test"}))
    assert result.success is True
    assert "test" in result.output
    
    # Test dispatch to non-existent tool
    result = asyncio.run(registry.dispatch("nonexistent", {}))
    assert result.success is False
    assert "Unknown tool" in result.error


def test_global_registry():
    """Test global registry functions."""
    # Test get_registry creates and returns global instance
    registry1 = get_registry()
    registry2 = get_registry()
    assert registry1 is registry2  # Same instance
    
    # Test that built-in tools are registered
    tool_names = registry1.list_tools()
    expected_builtins = {"bash", "read", "write", "edit"}
    assert expected_builtins.issubset(set(tool_names))


def test_register_tool_function():
    """Test the register_tool convenience function."""
    from h_agent.tools.registry import _registry
    # Reset registry for this test
    original_registry = _registry
    try:
        # Create a fresh registry
        import h_agent.tools.registry
        h_agent.tools.registry._registry = None
        
        tool = AnotherMockTool()
        register_tool(tool)
        
        # Check that tool was registered in global registry
        registry = get_registry()
        assert "another_tool" in registry.list_tools()
    finally:
        # Restore original registry
        h_agent.tools.registry._registry = original_registry


def test_handler_registration():
    """Test handler function registration."""
    registry = ToolRegistry()
    
    def mock_handler(args):
        return ToolResult.ok(f"Handler executed with {args}")
    
    schema = {
        "type": "object",
        "properties": {"param": {"type": "string"}},
        "required": ["param"]
    }
    
    registry.register_handler("handler_tool", mock_handler, schema)
    
    # Check if handler was registered as a tool
    assert "handler_tool" in registry.list_tools()
    
    # Test dispatch to handler
    import asyncio
    result = asyncio.run(registry.dispatch("handler_tool", {"param": "test"}))
    assert result.success is True
    assert "test" in result.output


@pytest.mark.asyncio
async def test_tool_dispatch_async():
    """Test async tool dispatch."""
    registry = ToolRegistry()
    
    tool = MockTool()
    registry.register(tool)
    
    # Test successful async dispatch
    result = await registry.dispatch("mock_tool", {"param": "async_test"})
    assert result.success is True
    assert "async_test" in result.output


if __name__ == "__main__":
    test_tool_registry_initialization()
    test_tool_registration()
    test_duplicate_tool_registration()
    test_tool_with_alias()
    test_tool_unregistration()
    test_tool_dispatch()
    test_global_registry()
    test_handler_registration()
    import asyncio
    asyncio.run(test_tool_dispatch_async())
    print("All registry tests passed!")