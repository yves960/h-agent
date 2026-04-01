"""
h_agent/core/engine.py - Query Engine

Core LLM loop with streaming, tool calling, and cost tracking.
Inspired by Claude Code's QueryEngine.ts architecture.
"""

from __future__ import annotations

import asyncio
import os
import time
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Union,
)

# Optional: tiktoken for accurate token counting
try:
    import tiktoken
    HAS_TIKTOKEN = True
except ImportError:
    tiktoken = None
    HAS_TIKTOKEN = False

from openai import OpenAI

# Try to import newer OpenAI types, fall back to older
try:
    from openai.types.chat import ChatCompletionMessage
    from openai.types.chat.chat_completion_message_tool_call import (
        ChatCompletionMessageToolCall,
    )
except ImportError:
    ChatCompletionMessage = None
    ChatCompletionMessageToolCall = None

try:
    from openai.types.chat.chat_completion import ChatCompletion, Choice
except ImportError:
    ChatCompletion = None
    Choice = None


# ============================================================
# Types
# ============================================================

class StreamEventType(Enum):
    """Types of events yielded by the streaming run."""
    CONTENT = "content"           # Text content chunk
    TOOL_CALL = "tool_call"      # Tool call detected
    TOOL_RESULT = "tool_result"  # Tool execution result
    THINKING = "thinking"        # Thinking/reasoning content
    COMPLETE = "complete"        # Response complete
    ERROR = "error"              # Error occurred
    USAGE = "usage"              # Token usage info


@dataclass
class StreamEvent:
    """An event from the streaming response."""
    type: StreamEventType
    content: Any = None
    tool_call_id: Optional[str] = None
    tool_name: Optional[str] = None
    tool_args: Optional[dict] = None
    error: Optional[str] = None
    usage: Optional[dict] = None


@dataclass
class ToolCallResult:
    """Result of a tool execution during streaming."""
    tool_call_id: str
    tool_name: str
    args: dict
    result: Any
    success: bool
    error: Optional[str] = None


@dataclass
class UsageInfo:
    """Token usage information."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0


# ============================================================
# Cost Calculation
# ============================================================

# Default pricing (per 1M tokens) - OpenAI GPT-4
DEFAULT_PRICING = {
    "gpt-4o": {"input": 5.0, "output": 15.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
}

# Default model
DEFAULT_MODEL = os.getenv("MODEL_ID", "gpt-4o")


def calculate_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    pricing: Optional[dict] = None,
) -> float:
    """Calculate API cost in USD."""
    if pricing is None:
        pricing = DEFAULT_PRICING
    
    # Find pricing tier
    tier = pricing.get(model, pricing.get("gpt-4o", {"input": 5.0, "output": 15.0}))
    
    input_cost = (prompt_tokens / 1_000_000) * tier["input"]
    output_cost = (completion_tokens / 1_000_000) * tier["output"]
    
    return input_cost + output_cost


# ============================================================
# Token Counting
# ============================================================

class TokenCounter:
    """
    Token counter using tiktoken.
    
    Supports:
    - cl100k_base (GPT-4, Claude, etc.)
    - o200k_base (GPT-4o)
    - Fallback estimation
    """

    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        self._encoder = None
        self._init_encoder()

    def _init_encoder(self):
        """Initialize tiktoken encoder."""
        if not HAS_TIKTOKEN or tiktoken is None:
            self._encoder = None
            return
        
        try:
            # Try to get encoder for the model
            if "o1" in self.model.lower():
                # o1 models don't use tiktoken the same way
                self._encoder = None
            elif "gpt-4o" in self.model.lower():
                self._encoder = tiktoken.get_encoding("o200k_base")
            else:
                self._encoder = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self._encoder = None

    def count_messages(self, messages: List[dict]) -> int:
        """Count tokens in a message list."""
        if self._encoder is None:
            # Fallback: estimate ~4 chars per token
            total = 0
            for msg in messages:
                content = msg.get("content", "")
                if isinstance(content, str):
                    total += len(content) // 4
                elif isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict):
                            total += len(str(part.get("text", ""))) // 4
            return total + 4  # Add overhead

        total = 4  # Base overhead
        for msg in messages:
            total += 4  # Role overhead
            content = msg.get("content", "")
            
            if isinstance(content, str):
                total += len(self._encoder.encode(content))
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict):
                        if part.get("type") == "text":
                            text = part.get("text", "")
                            total += len(self._encoder.encode(text))
                        elif part.get("type") == "image_url":
                            # Images are expensive - estimate high
                            total += 85  # Base image cost
                    else:
                        total += 1
            
            total += 1  # Message terminator
        
        return total

    def count_text(self, text: str) -> int:
        """Count tokens in text."""
        if self._encoder is None:
            return len(text) // 4
        
        return len(self._encoder.encode(text))


# ============================================================
# Message Helpers
# ============================================================

def build_messages(
    system_prompt: Optional[str] = None,
    messages: Optional[List[dict]] = None,
    tools: Optional[List[dict]] = None,
) -> List[dict]:
    """
    Build messages list for API call.
    
    Args:
        system_prompt: System prompt to prepend
        messages: Conversation messages
        tools: Tool definitions
    
    Returns:
        Messages list ready for API
    """
    result = []
    
    if system_prompt:
        result.append({"role": "system", "content": system_prompt})
    
    if messages:
        result.extend(messages)
    
    return result


def build_tool_result_message(
    tool_call_id: str,
    content: str,
) -> dict:
    """Build a tool result message."""
    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "content": content,
    }


def parse_tool_calls(
    message: ChatCompletionMessage,
) -> List[ChatCompletionMessageToolCall]:
    """Parse tool calls from a response message."""
    if message.tool_calls:
        return message.tool_calls
    return []


# ============================================================
# Query Engine
# ============================================================

class QueryEngine:
    """
    Core LLM query engine with streaming and tool calling.
    
    Features:
    - Streaming responses
    - Automatic tool call execution loop
    - Token counting and cost tracking
    - Thinking mode support (reasoning_content)
    - Configurable model and parameters
    
    Inspired by Claude Code's QueryEngine.ts.
    """

    def __init__(
        self,
        client: Optional[OpenAI] = None,
        model: str = DEFAULT_MODEL,
        tools: Optional[List[dict]] = None,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        timeout: int = 120,
        max_turns: int = 100,
        pricing: Optional[dict] = None,
        tool_registry=None,
    ):
        """
        Initialize the QueryEngine.
        
        Args:
            client: OpenAI client (creates default if None)
            model: Model ID to use
            tools: List of OpenAI tool definitions
            system_prompt: System prompt
            max_tokens: Max tokens in response
            temperature: Temperature for generation
            timeout: Request timeout in seconds
            max_turns: Max tool call iterations
            pricing: Custom pricing dict
            tool_registry: ToolRegistry instance for dispatch
        """
        self.client = client or self._create_client()
        self.model = model
        self.tools = tools or []
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self.max_turns = max_turns
        self.pricing = pricing or DEFAULT_PRICING
        self.tool_registry = tool_registry
        
        self.token_counter = TokenCounter(model)
        self.total_usage = UsageInfo()

    def _create_client(self) -> OpenAI:
        """Create default OpenAI client."""
        from dotenv import load_dotenv
        load_dotenv(override=True)
        
        return OpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "sk-dummy"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        )

    async def run(
        self,
        messages: List[dict],
        tools: Optional[List[dict]] = None,
        system_prompt: Optional[str] = None,
        stream: bool = True,
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Run the query with streaming.
        
        Args:
            messages: Conversation messages (modified in place)
            tools: Override tools
            system_prompt: Override system prompt
            stream: Whether to stream the response
            
        Yields:
            StreamEvent objects
        """
        # Build API messages
        api_messages = build_messages(
            system_prompt=system_prompt or self.system_prompt,
            messages=messages,
            tools=tools or self.tools,
        )
        
        # Count prompt tokens
        prompt_tokens = self.token_counter.count_messages(api_messages)
        
        # Run the API call
        tool_calls = []
        content_parts = []
        thinking_parts = []
        current_tool_call = None
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=api_messages,
                tools=tools or self.tools or None,
                tool_choice="auto" if (tools or self.tools) else None,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=self.timeout,
                stream=stream,
            )
            
            if stream:
                async for chunk in self._stream_response(response):
                    event = chunk
                    
                    if event.type == StreamEventType.THINKING:
                        thinking_parts.append(event.content)
                        yield event
                    elif event.type == StreamEventType.CONTENT:
                        content_parts.append(event.content)
                        yield event
                    elif event.type == StreamEventType.TOOL_CALL:
                        tool_calls.append(event)
                        yield event
                    elif event.type == StreamEventType.USAGE:
                        self.total_usage.prompt_tokens += event.usage.get("prompt_tokens", 0)
                        self.total_usage.completion_tokens += event.usage.get("completion_tokens", 0)
                        self.total_usage.total_tokens += event.usage.get("total_tokens", 0)
                        yield event
                    elif event.type == StreamEventType.COMPLETE:
                        yield event
            else:
                # Non-streaming
                message = response.choices[0].message
                
                # Extract content
                if message.content:
                    yield StreamEvent(
                        type=StreamEventType.CONTENT,
                        content=message.content,
                    )
                    content_parts.append(message.content)
                
                # Extract tool calls
                if message.tool_calls:
                    for tc in message.tool_calls:
                        yield StreamEvent(
                            type=StreamEventType.TOOL_CALL,
                            tool_call_id=tc.id,
                            tool_name=tc.function.name,
                            tool_args=json.loads(tc.function.arguments),
                        )
                        tool_calls.append(tc)
                
                # Usage
                if response.usage:
                    yield StreamEvent(
                        type=StreamEventType.USAGE,
                        usage={
                            "prompt_tokens": response.usage.prompt_tokens,
                            "completion_tokens": response.usage.completion_tokens,
                            "total_tokens": response.usage.total_tokens,
                        }
                    )
                
                yield StreamEvent(type=StreamEventType.COMPLETE)
        
        except Exception as e:
            yield StreamEvent(type=StreamEventType.ERROR, error=str(e))

    async def _stream_response(
        self,
        response,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Stream the response chunks."""
        content_buffer = ""
        tool_call_buffer = None
        thinking_buffer = ""
        
        for chunk in response:
            if not chunk.choices:
                continue
            
            choice = chunk.choices[0]
            delta = choice.delta
            
            if not delta:
                continue
            
            # Handle content delta
            if delta.content:
                content_buffer += delta.content
                yield StreamEvent(type=StreamEventType.CONTENT, content=delta.content)
            
            # Handle tool calls
            if delta.tool_calls:
                for tool_call_delta in delta.tool_calls:
                    if tool_call_delta.id:
                        if tool_call_buffer and tool_call_buffer.get("id") != tool_call_delta.id:
                            # Finish previous tool call
                            yield self._finish_tool_call(tool_call_buffer)
                            tool_call_buffer = None
                        
                        if tool_call_buffer is None:
                            tool_call_buffer = {
                                "id": tool_call_delta.id,
                                "name": "",
                                "arguments": "",
                            }
                    
                    if tool_call_delta.function:
                        if tool_call_delta.function.name:
                            tool_call_buffer["name"] += tool_call_delta.function.name
                        if tool_call_delta.function.arguments:
                            tool_call_buffer["arguments"] += tool_call_delta.function.arguments
                    
                    if tool_call_delta.type == "reasoning":
                        # Thinking content (for models that support it)
                        reasoning = tool_call_delta.get("reasoning_content", "")
                        if reasoning:
                            yield StreamEvent(
                                type=StreamEventType.THINKING,
                                content=reasoning,
                            )
                            thinking_buffer += reasoning
                
                continue  # Don't set finish_reason yet
            
            # Check for completion
            if choice.finish_reason:
                # Finish any pending tool call
                if tool_call_buffer:
                    yield self._finish_tool_call(tool_call_buffer)
                    tool_call_buffer = None
                
                # Usage info
                if hasattr(chunk, 'usage') and chunk.usage:
                    yield StreamEvent(
                        type=StreamEventType.USAGE,
                        usage={
                            "prompt_tokens": chunk.usage.prompt_tokens,
                            "completion_tokens": chunk.usage.completion_tokens,
                            "total_tokens": chunk.usage.total_tokens,
                        }
                    )
                
                yield StreamEvent(type=StreamEventType.COMPLETE)
        
        # Flush any remaining content
        if content_buffer:
            yield StreamEvent(type=StreamEventType.CONTENT, content="")

    def _finish_tool_call(self, buffer: dict) -> StreamEvent:
        """Finish a tool call from buffer."""
        try:
            args = json.loads(buffer["arguments"]) if buffer["arguments"] else {}
        except json.JSONDecodeError:
            args = {"_raw": buffer["arguments"]}
        
        return StreamEvent(
            type=StreamEventType.TOOL_CALL,
            tool_call_id=buffer["id"],
            tool_name=buffer["name"],
            tool_args=args,
        )

    async def run_tool_loop(
        self,
        messages: List[dict],
        tools: Optional[List[dict]] = None,
        system_prompt: Optional[str] = None,
        tool_handler: Optional[Callable] = None,
    ) -> str:
        """
        Run the full tool call loop until completion.
        
        Args:
            messages: Conversation messages (modified in place)
            tools: Override tools
            system_prompt: Override system prompt
            tool_handler: Function(name, args) -> str, or ToolRegistry
            
        Returns:
            Final assistant message content
        """
        if tools is None:
            tools = self.tools
        
        if tool_handler is None and self.tool_registry:
            tool_handler = self.tool_registry.dispatch
        
        turns = 0
        final_content = ""
        
        while turns < self.max_turns:
            turns += 1
            
            # Run streaming response
            content_parts = []
            tool_calls = []
            thinking_content = []
            
            async for event in self.run(
                messages=messages,
                tools=tools,
                system_prompt=system_prompt,
                stream=True,
            ):
                if event.type == StreamEventType.CONTENT:
                    content_parts.append(event.content)
                elif event.type == StreamEventType.TOOL_CALL:
                    tool_calls.append(event)
                elif event.type == StreamEventType.THINKING:
                    thinking_content.append(event.content)
                elif event.type == StreamEventType.COMPLETE:
                    # Add assistant message
                    content = "".join(content_parts)
                    assistant_msg = {"role": "assistant", "content": content}
                    
                    if tool_calls:
                        assistant_msg["tool_calls"] = [
                            {
                                "id": tc.tool_call_id,
                                "type": "function",
                                "function": {
                                    "name": tc.tool_name,
                                    "arguments": json.dumps(tc.tool_args),
                                }
                            }
                            for tc in tool_calls
                        ]
                    
                    messages.append(assistant_msg)
                    final_content = content
                    
                    # Execute tools if any
                    if tool_calls:
                        for tc in tool_calls:
                            # Execute tool
                            if tool_handler:
                                result = await tool_handler(tc.tool_name, tc.tool_args)
                            else:
                                result = f"Error: No tool handler registered"
                            
                            if isinstance(result, dict) and hasattr(result, 'output'):
                                result_str = result.output
                            elif isinstance(result, dict):
                                result_str = json.dumps(result)
                            else:
                                result_str = str(result)
                            
                            # Add tool result message
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tc.tool_call_id,
                                "content": result_str,
                            })
                        
                        # Continue loop for next response
                        break
                    else:
                        # No tool calls, we're done
                        return final_content
                elif event.type == StreamEventType.ERROR:
                    return f"Error: {event.error}"
            
            # If we broke from the loop without hitting COMPLETE with tool calls,
            # check if we should continue
            if not tool_calls:
                break
        
        return final_content

    def get_usage(self) -> UsageInfo:
        """Get total token usage."""
        self.total_usage.cost_usd = calculate_cost(
            self.model,
            self.total_usage.prompt_tokens,
            self.total_usage.completion_tokens,
            self.pricing,
        )
        return self.total_usage

    def reset_usage(self) -> None:
        """Reset usage counters."""
        self.total_usage = UsageInfo()


# ============================================================
# Convenience Functions
# ============================================================

async def run_query(
    messages: List[dict],
    model: str = DEFAULT_MODEL,
    tools: Optional[List[dict]] = None,
    system_prompt: Optional[str] = None,
    tool_handler: Optional[Callable] = None,
) -> str:
    """
    Run a query with automatic tool calling.
    
    Convenience function that creates an engine and runs the tool loop.
    """
    engine = QueryEngine(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
    )
    
    return await engine.run_tool_loop(
        messages=messages,
        tool_handler=tool_handler,
    )
