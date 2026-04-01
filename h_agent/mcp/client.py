"""MCP client and registry."""

import asyncio
from typing import List, Optional, Dict, Any

from .protocol import MCPTool, MCPResource, MCPServerInfo
from .transport import StdioTransport, HTTPTransport


class MCPClient:
    """MCP client for connecting to external tool servers."""

    def __init__(self, name: str, transport):
        self.name = name
        self.transport = transport
        self.tools: List[MCPTool] = []
        self.resources: List[MCPResource] = []
        self.server_info: Optional[MCPServerInfo] = None
        self._request_id = 0

    async def connect(self) -> bool:
        """Connect to an MCP server."""
        if isinstance(self.transport, StdioTransport):
            await self.transport.start()

        result = await self._request("initialize", {
            "protocolVersion": "2024-11-05",
            "clientInfo": {
                "name": "h-agent",
                "version": "1.0.0",
            }
        })

        if result:
            self.server_info = MCPServerInfo(
                name=result.get("serverInfo", {}).get("name", "unknown"),
                version=result.get("serverInfo", {}).get("version", "0.0.0"),
            )

            tools_result = await self._request("tools/list")
            if tools_result:
                for tool in tools_result.get("tools", []):
                    self.tools.append(MCPTool(
                        name=tool["name"],
                        description=tool.get("description", ""),
                        input_schema=tool.get("inputSchema", {}),
                    ))

            resources_result = await self._request("resources/list")
            if resources_result:
                for res in resources_result.get("resources", []):
                    self.resources.append(MCPResource(
                        uri=res["uri"],
                        name=res["name"],
                        description=res.get("description"),
                        mime_type=res.get("mimeType"),
                    ))

            return True

        return False

    async def call_tool(self, name: str, arguments: dict) -> Any:
        """Call an MCP tool."""
        result = await self._request("tools/call", {
            "name": name,
            "arguments": arguments,
        })
        if result:
            return result.get("content", [])
        return None

    async def read_resource(self, uri: str) -> Any:
        """Read an MCP resource."""
        result = await self._request("resources/read", {
            "uri": uri,
        })
        return result

    async def _request(self, method: str, params: dict = None) -> Optional[dict]:
        """Send a JSON-RPC request."""
        self._request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params,
        }

        await self.transport.send(request)
        response = await self.transport.receive()

        if response and "result" in response:
            return response["result"]
        elif response and "error" in response:
            raise Exception(f"MCP error: {response['error']}")

        return None

    async def close(self):
        """Close the connection."""
        await self.transport.close()


class MCPRegistry:
    """MCP server registry."""

    def __init__(self):
        self.clients: Dict[str, MCPClient] = {}

    async def connect(self, name: str, config: dict) -> MCPClient:
        """Connect to an MCP server."""
        if config.get("type") == "stdio":
            transport = StdioTransport(
                command=config["command"],
                args=config.get("args", []),
                env=config.get("env"),
            )
        elif config.get("type") == "http":
            transport = HTTPTransport(
                url=config["url"],
                headers=config.get("headers"),
            )
        else:
            raise ValueError(f"Unknown MCP transport type: {config.get('type')}")

        client = MCPClient(name, transport)
        if await client.connect():
            self.clients[name] = client
            return client

        raise Exception(f"Failed to connect to MCP server: {name}")

    def get_client(self, name: str) -> Optional[MCPClient]:
        return self.clients.get(name)

    def list_tools(self) -> List[MCPTool]:
        """List all MCP tools."""
        tools = []
        for client in self.clients.values():
            tools.extend(client.tools)
        return tools

    async def close_all(self):
        """Close all connections."""
        for client in self.clients.values():
            await client.close()
        self.clients.clear()


# Global registry
_mcp_registry: Optional[MCPRegistry] = None


def get_mcp_registry() -> MCPRegistry:
    global _mcp_registry
    if _mcp_registry is None:
        _mcp_registry = MCPRegistry()
    return _mcp_registry
