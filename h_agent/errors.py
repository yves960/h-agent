"""
h_agent/errors.py - Error Types and Classes

Enhanced error handling for h-agent with classification,
retry support, and recovery strategies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ErrorType(str, Enum):
    """Classification of error types for agent operations."""
    NETWORK = "network"           # Network errors (connection, timeout, etc.)
    TIMEOUT = "timeout"           # Operation timeout
    PERMISSION = "permission"     # Permission/authorization errors
    VALIDATION = "validation"     # Input validation errors
    EXECUTION = "execution"       # Execution/runtime errors
    RATE_LIMIT = "rate_limit"    # Rate limiting errors
    AUTH = "auth"                # Authentication errors
    NOT_FOUND = "not_found"       # Resource not found
    UNKNOWN = "unknown"           # Unknown/unclassified errors


@dataclass
class AgentError:
    """
    Structured error with classification and recovery info.
    
    Attributes:
        type: Error type classification
        message: Human-readable error message
        retryable: Whether this error can be retried
        suggestion: Suggested user action or fix
        details: Additional error details/context
        cause: Optional underlying cause
    """
    type: ErrorType
    message: str
    retryable: bool = False
    suggestion: str = ""
    details: Optional[dict] = None
    cause: Optional[Exception] = None

    def __str__(self) -> str:
        """String representation with suggestion if available."""
        result = f"[{self.type.value}] {self.message}"
        if self.suggestion:
            result += f"\nSuggestion: {self.suggestion}"
        return result

    @classmethod
    def network_error(
        cls,
        message: str,
        suggestion: str = "Check network connection and try again",
        **kwargs
    ) -> "AgentError":
        """Create a network error."""
        return cls(
            type=ErrorType.NETWORK,
            message=message,
            retryable=True,
            suggestion=suggestion,
            **kwargs
        )

    @classmethod
    def timeout_error(
        cls,
        message: str,
        suggestion: str = "Try again with a longer timeout or simplify the request",
        **kwargs
    ) -> "AgentError":
        """Create a timeout error."""
        return cls(
            type=ErrorType.TIMEOUT,
            message=message,
            retryable=True,
            suggestion=suggestion,
            **kwargs
        )

    @classmethod
    def permission_error(
        cls,
        message: str,
        suggestion: str = "Check permissions and try again",
        **kwargs
    ) -> "AgentError":
        """Create a permission error."""
        return cls(
            type=ErrorType.PERMISSION,
            message=message,
            retryable=False,
            suggestion=suggestion,
            **kwargs
        )

    @classmethod
    def validation_error(
        cls,
        message: str,
        suggestion: str = "Check input parameters",
        **kwargs
    ) -> "AgentError":
        """Create a validation error."""
        return cls(
            type=ErrorType.VALIDATION,
            message=message,
            retryable=False,
            suggestion=suggestion,
            **kwargs
        )

    @classmethod
    def execution_error(
        cls,
        message: str,
        suggestion: str = "Review the error and fix the underlying issue",
        **kwargs
    ) -> "AgentError":
        """Create an execution error."""
        return cls(
            type=ErrorType.EXECUTION,
            message=message,
            retryable=False,
            suggestion=suggestion,
            **kwargs
        )


class ErrorRecovery:
    """
    Error recovery strategies for different error types.
    
    Provides static methods for attempting to recover from
    various error conditions.
    """

    @staticmethod
    async def handle(
        error: AgentError,
        context: dict,
    ) -> Optional[str]:
        """
        Attempt to recover from an error.
        
        Args:
            error: The error to recover from
            context: Execution context (model, tools, messages, etc.)
            
        Returns:
            Recovery action string or None if unrecoverable
        """
        handlers = {
            ErrorType.NETWORK: ErrorRecovery._handle_network,
            ErrorType.TIMEOUT: ErrorRecovery._handle_timeout,
            ErrorType.RATE_LIMIT: ErrorRecovery._handle_rate_limit,
            ErrorType.PERMISSION: ErrorRecovery._handle_permission,
            ErrorType.VALIDATION: ErrorRecovery._handle_validation,
            ErrorType.EXECUTION: ErrorRecovery._handle_execution,
        }

        handler = handlers.get(error.type)
        if handler:
            return await handler(error, context)
        return None

    @staticmethod
    async def _handle_network(error: AgentError, context: dict) -> Optional[str]:
        """Handle network errors."""
        # Could implement retry with different endpoint
        # For now, just suggest checking connection
        return f"Network error: {error.message}. Check connection."

    @staticmethod
    async def _handle_timeout(error: AgentError, context: dict) -> Optional[str]:
        """Handle timeout errors."""
        # Could try simplifying the request
        return f"Timeout: {error.message}. Try a simpler request."

    @staticmethod
    async def _handle_rate_limit(error: AgentError, context: dict) -> Optional[str]:
        """Handle rate limit errors."""
        # Could implement backoff
        return f"Rate limited: {error.message}. Wait and retry."

    @staticmethod
    async def _handle_permission(error: AgentError, context: dict) -> Optional[str]:
        """Handle permission errors."""
        # Permission errors are not retryable
        return None

    @staticmethod
    async def _handle_validation(error: AgentError, context: dict) -> Optional[str]:
        """Handle validation errors."""
        # Validation errors need input fix
        return None

    @staticmethod
    async def _handle_execution(error: AgentError, context: dict) -> Optional[str]:
        """Handle execution errors."""
        # Execution errors need code fix
        return None


def classify_exception(exc: Exception) -> AgentError:
    """
    Classify an exception into an AgentError.
    
    Args:
        exc: The exception to classify
        
    Returns:
        AgentError with appropriate classification
    """
    exc_type = type(exc).__name__
    exc_msg = str(exc)

    # Import errors for classification
    import asyncio
    import httpx
    import openai

    # Check for timeout errors (built-in TimeoutError and asyncio.TimeoutError)
    if isinstance(exc, TimeoutError) or isinstance(exc, asyncio.TimeoutError):
        return AgentError.timeout_error(f"Timeout: {exc_msg}")

    if isinstance(exc, httpx.TimeoutException):
        return AgentError.timeout_error(f"HTTP timeout: {exc_msg}")

    if isinstance(exc, httpx.ConnectError):
        return AgentError.network_error(f"Connection failed: {exc_msg}")

    if isinstance(exc, httpx.HTTPStatusError):
        if exc.response.status_code == 401:
            return AgentError(
                type=ErrorType.AUTH,
                message=f"Authentication failed: {exc_msg}",
                retryable=False,
                suggestion="Check API key configuration",
            )
        if exc.response.status_code == 403:
            return AgentError.permission_error(
                f"Access forbidden: {exc_msg}",
                suggestion="Check API permissions",
            )
        if exc.response.status_code == 404:
            return AgentError(
                type=ErrorType.NOT_FOUND,
                message=f"Resource not found: {exc_msg}",
                retryable=False,
            )
        if exc.response.status_code == 429:
            return AgentError(
                type=ErrorType.RATE_LIMIT,
                message=f"Rate limited: {exc_msg}",
                retryable=True,
                suggestion="Wait before retrying",
            )
        return AgentError.execution_error(f"HTTP error {exc.response.status_code}: {exc_msg}")

    if isinstance(exc, openai.AuthenticationError):
        return AgentError(
            type=ErrorType.AUTH,
            message=f"Authentication error: {exc_msg}",
            retryable=False,
            suggestion="Check API key",
        )

    if isinstance(exc, openai.RateLimitError):
        return AgentError(
            type=ErrorType.RATE_LIMIT,
            message=f"Rate limit: {exc_msg}",
            retryable=True,
            suggestion="Wait before retrying",
        )

    if isinstance(exc, openai.APIError):
        return AgentError.execution_error(f"API error: {exc_msg}")

    # Default to unknown
    return AgentError(
        type=ErrorType.UNKNOWN,
        message=f"{exc_type}: {exc_msg}",
        retryable=False,
    )
