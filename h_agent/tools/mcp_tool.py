"""MCP tool - call tools from MCP servers."""

from h_agent.tools.base import Tool, ToolResult
from h_agent.mcp import get_mcp_registry


class MCPTool(Tool):
    """Call a tool from an MCP server."""

    name = "mcp"
    description = "Call a tool from an MCP server"
    input_schema = {
        "type": "object",
        "properties": {
            "server": {"type": "string", "description": "MCP server name"},
            "tool": {"type": "string", "description": "Tool name to call"},
            "arguments": {"type": "object", "description": "Tool arguments"},
        },
        "required": ["server", "tool"],
    }

    async def execute(self, args: dict, progress_callback=None) -> ToolResult:
        registry = get_mcp_registry()

        server_name = args["server"]
        tool_name = args["tool"]
        arguments = args.get("arguments", {})

        client = registry.get_client(server_name)
        if not client:
            return ToolResult(
                success=False,
                error=f"MCP server not found: {server_name}",
            )

        try:
            result = await client.call_tool(tool_name, arguments)
            return ToolResult(
                success=True,
                output=str(result),
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
            )
