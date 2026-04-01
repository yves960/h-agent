"""MCP transport layer - stdio and HTTP."""

import asyncio
import json
import os
from typing import Optional, List


class StdioTransport:
    """Communicate with MCP server over stdio."""

    def __init__(self, command: str, args: List[str] = None, env: dict = None):
        self.command = command
        self.args = args or []
        self.env = env or {}
        self.process: Optional[asyncio.subprocess.Process] = None

    async def start(self):
        """Start the MCP server process."""
        self.process = await asyncio.create_subprocess_exec(
            self.command,
            *self.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, **self.env},
        )

    async def send(self, request: dict) -> None:
        """Send a JSON-RPC request."""
        line = json.dumps(request) + "\n"
        self.process.stdin.write(line.encode())
        await self.process.stdin.drain()

    async def receive(self) -> Optional[dict]:
        """Receive a JSON-RPC response."""
        line = await self.process.stdout.readline()
        if not line:
            return None
        return json.loads(line.decode().strip())

    async def close(self):
        """Close the connection."""
        if self.process:
            self.process.terminate()
            await self.process.wait()


class HTTPTransport:
    """Communicate with MCP server over HTTP/SSE."""

    def __init__(self, url: str, headers: dict = None):
        self.url = url
        self.headers = headers or {}

    async def send(self, request: dict) -> dict:
        """Send an HTTP request."""
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.url,
                json=request,
                headers=self.headers,
            ) as response:
                return await response.json()
