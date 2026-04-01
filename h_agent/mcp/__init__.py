"""MCP (Model Context Protocol) support for h-agent."""

from .protocol import MCPTool, MCPResource, MCPServerInfo, JSONRPCRequest, JSONRPCResponse, MCPRole
from .client import MCPClient, MCPRegistry, get_mcp_registry
from .transport import StdioTransport, HTTPTransport

__all__ = [
    "MCPTool",
    "MCPResource", 
    "MCPServerInfo",
    "JSONRPCRequest",
    "JSONRPCResponse",
    "MCPRole",
    "MCPClient",
    "MCPRegistry",
    "get_mcp_registry",
    "StdioTransport",
    "HTTPTransport",
]
