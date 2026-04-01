"""
Unit tests for h_agent.errors module.
"""

import pytest

# Import error types
from h_agent.errors import (
    AgentError,
    ErrorType,
    ErrorRecovery,
    classify_exception,
)


def test_error_type_enum():
    """Test ErrorType enum values."""
    assert ErrorType.NETWORK.value == "network"
    assert ErrorType.TIMEOUT.value == "timeout"
    assert ErrorType.PERMISSION.value == "permission"
    assert ErrorType.VALIDATION.value == "validation"
    assert ErrorType.EXECUTION.value == "execution"
    assert ErrorType.RATE_LIMIT.value == "rate_limit"
    assert ErrorType.AUTH.value == "auth"
    assert ErrorType.NOT_FOUND.value == "not_found"
    assert ErrorType.UNKNOWN.value == "unknown"


def test_agent_error_creation():
    """Test AgentError creation."""
    error = AgentError(
        type=ErrorType.NETWORK,
        message="Connection failed",
        retryable=True,
        suggestion="Check network",
    )
    
    assert error.type == ErrorType.NETWORK
    assert error.message == "Connection failed"
    assert error.retryable is True
    assert error.suggestion == "Check network"
    assert error.details is None
    assert error.cause is None


def test_agent_error_string_representation():
    """Test AgentError string representation."""
    error = AgentError(
        type=ErrorType.VALIDATION,
        message="Invalid input",
        suggestion="Check your input",
    )
    
    result = str(error)
    assert "[validation]" in result
    assert "Invalid input" in result
    assert "Suggestion:" in result


def test_agent_error_string_without_suggestion():
    """Test AgentError string without suggestion."""
    error = AgentError(
        type=ErrorType.UNKNOWN,
        message="Something went wrong",
    )
    
    result = str(error)
    assert "[unknown]" in result
    assert "Something went wrong" in result
    assert "Suggestion:" not in result


def test_agent_error_factory_network():
    """Test AgentError.network_error factory."""
    error = AgentError.network_error("Connection refused")
    
    assert error.type == ErrorType.NETWORK
    assert error.retryable is True
    assert "Connection refused" in error.message


def test_agent_error_factory_timeout():
    """Test AgentError.timeout_error factory."""
    error = AgentError.timeout_error("Request timed out")
    
    assert error.type == ErrorType.TIMEOUT
    assert error.retryable is True


def test_agent_error_factory_permission():
    """Test AgentError.permission_error factory."""
    error = AgentError.permission_error("Access denied")
    
    assert error.type == ErrorType.PERMISSION
    assert error.retryable is False


def test_agent_error_factory_validation():
    """Test AgentError.validation_error factory."""
    error = AgentError.validation_error("Invalid param")
    
    assert error.type == ErrorType.VALIDATION
    assert error.retryable is False


def test_agent_error_factory_execution():
    """Test AgentError.execution_error factory."""
    error = AgentError.execution_error("Runtime error")
    
    assert error.type == ErrorType.EXECUTION
    assert error.retryable is False


def test_classify_exception_timeout():
    """Test classifying TimeoutError."""
    error = classify_exception(TimeoutError("Operation timed out"))
    
    assert error.type == ErrorType.TIMEOUT
    assert error.retryable is True


def test_classify_exception_generic():
    """Test classifying generic Exception."""
    error = classify_exception(Exception("Something went wrong"))
    
    assert error.type == ErrorType.UNKNOWN
    assert error.retryable is False


def test_error_recovery_handle():
    """Test ErrorRecovery.handle with different error types."""
    import asyncio
    
    # Test network error recovery
    network_error = AgentError.network_error("Connection failed")
    result = asyncio.run(ErrorRecovery.handle(network_error, {}))
    assert result is not None
    
    # Test permission error (not recoverable)
    perm_error = AgentError.permission_error("Access denied")
    result = asyncio.run(ErrorRecovery.handle(perm_error, {}))
    assert result is None
    
    # Test validation error (not recoverable)
    val_error = AgentError.validation_error("Invalid input")
    result = asyncio.run(ErrorRecovery.handle(val_error, {}))
    assert result is None


if __name__ == "__main__":
    test_error_type_enum()
    test_agent_error_creation()
    test_agent_error_string_representation()
    test_agent_error_string_without_suggestion()
    test_agent_error_factory_network()
    test_agent_error_factory_timeout()
    test_agent_error_factory_permission()
    test_agent_error_factory_validation()
    test_agent_error_factory_execution()
    test_classify_exception_timeout()
    test_classify_exception_generic()
    test_error_recovery_handle()
    print("All tests passed!")
