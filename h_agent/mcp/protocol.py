"""MCP protocol type definitions."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class MCPRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class MCPTool:
    name: str
    description: str
    input_schema: dict


@dataclass
class MCPResource:
    uri: str
    name: str
    description: Optional[str] = None
    mime_type: Optional[str] = None


@dataclass
class MCPServerInfo:
    name: str
    version: str


@dataclass
class JSONRPCRequest:
    jsonrpc: str = "2.0"
    id: Optional[int] = None
    method: str = ""
    params: Optional[dict] = None


@dataclass
class JSONRPCResponse:
    jsonrpc: str = "2.0"
    id: Optional[int] = None
    result: Optional[Any] = None
    error: Optional[dict] = None
