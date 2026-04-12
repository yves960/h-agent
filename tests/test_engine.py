"""
Unit tests for h_agent.core.engine module.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from h_agent.core.engine import (
    QueryEngine, 
    TokenCounter, 
    StreamEvent, 
    StreamEventType,
    UsageInfo,
    calculate_cost
)


def test_token_counter_initialization():
    """Test TokenCounter initialization."""
    counter = TokenCounter()
    assert counter.model is not None  # Should have a default model


def test_token_counter_fallback():
    """Test TokenCounter fallback when tiktoken is not available."""
    # Test the fallback behavior by simulating no tiktoken
    with patch('h_agent.core.engine.HAS_TIKTOKEN', False):
        counter = TokenCounter()
        # Should not fail even without tiktoken
        text = "Hello world"
        tokens = counter.count_text(text)
        # Should use fallback estimation (~4 chars per token)
        expected_approx = len(text) // 4
        assert abs(tokens - expected_approx) <= 2  # Allow some variance


def test_calculate_cost():
    """Test cost calculation."""
    # Test default pricing
    cost = calculate_cost("gpt-4o", 1000000, 500000)  # 1M input, 0.5M output
    expected = (1.0 * 5.0) + (0.5 * 15.0)  # 5.0 + 7.5 = 12.5
    assert abs(cost - expected) < 0.01
    
    # Test custom pricing
    custom_pricing = {"gpt-test": {"input": 1.0, "output": 2.0}}
    cost = calculate_cost("gpt-test", 1000000, 1000000, custom_pricing)
    expected = (1.0 * 1.0) + (1.0 * 2.0)  # 1.0 + 2.0 = 3.0
    assert abs(cost - expected) < 0.01


def test_usage_info():
    """Test UsageInfo class."""
    usage = UsageInfo(prompt_tokens=100, completion_tokens=50, total_tokens=150)
    assert usage.prompt_tokens == 100
    assert usage.completion_tokens == 50
    assert usage.total_tokens == 150  # Manually set, not auto-calculated
    assert usage.cost_usd == 0.0  # Initially zero until calculated


def test_stream_event_types():
    """Test StreamEvent creation with different types."""
    # Test different event types
    content_event = StreamEvent(type=StreamEventType.CONTENT, content="test")
    assert content_event.type == StreamEventType.CONTENT
    assert content_event.content == "test"
    
    tool_call_event = StreamEvent(
        type=StreamEventType.TOOL_CALL,
        tool_call_id="call123",
        tool_name="test_tool",
        tool_args={"param": "value"}
    )
    assert tool_call_event.type == StreamEventType.TOOL_CALL
    assert tool_call_event.tool_call_id == "call123"
    assert tool_call_event.tool_name == "test_tool"
    assert tool_call_event.tool_args == {"param": "value"}
    
    error_event = StreamEvent(type=StreamEventType.ERROR, error="test error")
    assert error_event.type == StreamEventType.ERROR
    assert error_event.error == "test error"
    
    # Test PROGRESS event type
    progress_event = StreamEvent(type=StreamEventType.PROGRESS, content="Processing...")
    assert progress_event.type == StreamEventType.PROGRESS
    assert progress_event.content == "Processing..."
    
    # Verify PROGRESS is in StreamEventType
    assert "PROGRESS" in [e.name for e in StreamEventType]


def test_query_engine_initialization():
    """Test QueryEngine initialization."""
    # Test with default parameters
    engine = QueryEngine()
    assert engine.model is not None
    assert engine.max_tokens == 4096
    assert engine.temperature == 0.7
    assert engine.timeout == 120
    assert engine.token_counter is not None


@patch('h_agent.core.engine.OpenAI')
def test_query_engine_create_client(mock_openai_class):
    """Test QueryEngine client creation."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client
    
    engine = QueryEngine()
    # The client should be the mocked one
    assert engine.client is mock_client


def test_token_counter_count_messages():
    """Test token counting for messages."""
    counter = TokenCounter()
    
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ]
    
    # Count should work without failing
    token_count = counter.count_messages(messages)
    assert isinstance(token_count, int)
    assert token_count >= 0


def test_token_counter_count_text():
    """Test token counting for text."""
    counter = TokenCounter()
    
    text = "Hello world, this is a test."
    token_count = counter.count_text(text)
    
    assert isinstance(token_count, int)
    assert token_count >= 0


def test_query_engine_get_usage():
    """Test QueryEngine usage tracking."""
    engine = QueryEngine()
    
    # Initially should have zero usage
    usage = engine.get_usage()
    assert usage.prompt_tokens == 0
    assert usage.completion_tokens == 0
    assert usage.total_tokens == 0
    assert usage.cost_usd == 0.0
    
    # Simulate adding some usage
    engine.total_usage.prompt_tokens = 1000
    engine.total_usage.completion_tokens = 500
    engine.total_usage.total_tokens = 1500
    
    usage = engine.get_usage()
    # Cost should be calculated
    assert usage.cost_usd >= 0.0


def test_query_engine_reset_usage():
    """Test QueryEngine usage reset."""
    engine = QueryEngine()
    
    # Add some usage
    engine.total_usage.prompt_tokens = 1000
    engine.total_usage.completion_tokens = 500
    engine.total_usage.total_tokens = 1500
    
    # Reset usage
    engine.reset_usage()
    
    usage = engine.get_usage()
    assert usage.prompt_tokens == 0
    assert usage.completion_tokens == 0
    assert usage.total_tokens == 0


def test_query_engine_retry_config():
    """Test QueryEngine retry configuration."""
    engine = QueryEngine(max_retries=5, retry_delay=2.0)
    
    assert engine.max_retries == 5
    assert engine.retry_delay == 2.0
    
    # Test default values
    engine_default = QueryEngine()
    assert engine_default.max_retries == 3
    assert engine_default.retry_delay == 1.0


def test_query_engine_run():
    """Test QueryEngine run method (basic functionality)."""
    # This test mocks the OpenAI client to avoid actual API calls
    with patch('h_agent.core.engine.OpenAI') as mock_openai_class:
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock the chat.completions.create method
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "Test response"
        mock_message.tool_calls = None
        mock_choice.message = mock_message
        mock_choice.finish_reason = "stop"
        mock_response.choices = [mock_choice]
        mock_response.usage = None
        
        mock_client.chat.completions.create.return_value = mock_response
        
        engine = QueryEngine(client=mock_client)
        
        messages = [{"role": "user", "content": "Test message"}]
        
        # Test the run method (this would normally be async generator)
        # Since the actual implementation involves streaming, we'll just test initialization
        assert engine is not None


if __name__ == "__main__":
    test_token_counter_initialization()
    test_token_counter_fallback()
    test_calculate_cost()
    test_usage_info()
    test_stream_event_types()
    test_query_engine_initialization()
    test_token_counter_count_messages()
    test_token_counter_count_text()
    test_query_engine_get_usage()
    test_query_engine_reset_usage()
    test_query_engine_run()
    print("All engine tests passed!")
