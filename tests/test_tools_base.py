"""
Unit tests for h_agent.tools.base module.
"""

import pytest
from h_agent.tools.base import ToolResult, ToolDefinition, Tool

# Import error types if available
try:
    from h_agent.errors import AgentError, ErrorType
    HAS_ERROR_TYPES = True
except ImportError:
    HAS_ERROR_TYPES = False


def test_tool_result_creation():
    """Test ToolResult creation methods."""
    # Test ok method
    result = ToolResult.ok("Success message")
    assert result.success is True
    assert result.output == "Success message"
    assert result.error is None
    
    # Test err method
    result = ToolResult.err("Error message")
    assert result.success is False
    assert result.output == ""
    assert result.error == "Error message"
    
    # Test err method with output
    result = ToolResult.err("Error message", "Some output")
    assert result.success is False
    assert result.output == "Some output"
    assert result.error == "Error message"


def test_tool_result_to_dict():
    """Test ToolResult to_dict method."""
    result = ToolResult(success=True, output="test output", error=None)
    result_dict = result.to_dict()
    assert result_dict == {
        "success": True,
        "output": "test output",
        "error": None,
    }
    
    result = ToolResult.err("error message", "some output")
    result_dict = result.to_dict()
    assert result_dict == {
        "success": False,
        "output": "some output",
        "error": "error message",
    }


def test_tool_result_with_error_type():
    """Test ToolResult with error_type and retryable."""
    # Test with retryable error
    if HAS_ERROR_TYPES:
        result = ToolResult.err(
            "Network error",
            "some output",
            error_type=ErrorType.NETWORK,
            retryable=True
        )
        assert result.success is False
        assert result.error_type == ErrorType.NETWORK
        assert result.retryable is True
        assert result.to_dict()["retryable"] is True
    
    # Test err method with error_type
    if HAS_ERROR_TYPES:
        result = ToolResult.err(
            "Timeout error",
            "",
            error_type=ErrorType.TIMEOUT,
            retryable=True
        )
        assert result.error_type == ErrorType.TIMEOUT
        assert result.retryable is True


def test_tool_definition_creation():
    """Test ToolDefinition creation and format conversion."""
    definition = ToolDefinition(
        name="test_tool",
        description="A test tool",
        parameters={"type": "object", "properties": {}}
    )
    
    assert definition.type == "function"
    assert definition.name == "test_tool"
    assert definition.description == "A test tool"
    assert definition.parameters == {"type": "object", "properties": {}}
    
    # Test OpenAI format conversion
    openai_format = definition.to_openai_format()
    expected = {
        "type": "function",
        "function": {
            "name": "test_tool",
            "description": "A test tool",
            "parameters": {"type": "object", "properties": {}}
        }
    }
    assert openai_format == expected


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
    
    async def execute(self, args, progress_callback=None):
        if progress_callback:
            progress_callback("Starting execution...")
        result = ToolResult.ok(f"Executed with {args}")
        if progress_callback:
            progress_callback("Done!")
        return result


def test_tool_interface():
    """Test Tool interface implementation."""
    tool = MockTool()
    
    assert tool.name == "mock_tool"
    assert tool.description == "A mock tool for testing"
    
    schema = tool.input_schema
    assert isinstance(schema, dict)
    assert "param" in schema["properties"]
    
    # Test get_definition
    definition = tool.get_definition()
    assert definition.name == "mock_tool"
    assert definition.description == "A mock tool for testing"


@pytest.mark.asyncio
async def test_tool_execution():
    """Test tool execution."""
    tool = MockTool()
    result = await tool.execute({"param": "test_value"})
    
    assert result.success is True
    assert "test_value" in result.output


@pytest.mark.asyncio
async def test_tool_execution_with_progress_callback():
    """Test tool execution with progress callback."""
    tool = MockTool()
    progress_messages = []
    
    def callback(msg):
        progress_messages.append(msg)
    
    result = await tool.execute({"param": "test_value"}, progress_callback=callback)
    
    assert result.success is True
    assert len(progress_messages) == 2
    assert "Starting" in progress_messages[0]
    assert "Done" in progress_messages[1]


@pytest.mark.asyncio
async def test_tool_execute_with_progress():
    """Test tool execute_with_progress generator."""
    tool = MockTool()
    progress_messages = []
    
    async for msg in tool.execute_with_progress({"param": "test"}):
        progress_messages.append(msg)
    
    # Default execute_with_progress yields at least one message
    assert len(progress_messages) >= 1


if __name__ == "__main__":
    test_tool_result_creation()
    test_tool_result_to_dict()
    test_tool_definition_creation()
    test_tool_interface()
    import asyncio
    asyncio.run(test_tool_execution())
    print("All tests passed!")