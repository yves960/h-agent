"""
h_agent/bridge/server.py - IDE Bridge HTTP Server

Local HTTP server that bridges IDE events to the agent.
"""

from __future__ import annotations

import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Callable, Dict, Optional

from .protocol import BridgeMessage, MessageType
from .handlers import BridgeHandlers, create_default_handlers
from .jwt_utils import JWTAuth


class BridgeServer:
    """
    IDE Bridge HTTP Server.

    Listens on localhost for HTTP POST requests from IDE plugins.
    Handles message protocol with optional JWT authentication.

    Example:
        server = BridgeServer(port=9527)
        server.start()
        # Server running in background thread
        server.stop()
    """

    def __init__(
        self,
        port: int = 9527,
        auth_enabled: bool = False,
        auth_secret: str = "h-agent-bridge-secret",
    ):
        self.port = port
        self.auth_enabled = auth_enabled
        self.auth = JWTAuth(secret=auth_secret) if auth_enabled else None
        self.server: Optional[HTTPServer] = None
        self.handlers: BridgeHandlers = create_default_handlers()
        self._running = False

    def register_handler(self, msg_type: str, handler: Callable[[BridgeMessage], BridgeMessage]):
        """Register a handler for a message type."""
        self.handlers.register(msg_type, handler)

    def start(self) -> bool:
        """
        Start the bridge server in a background thread.

        Returns:
            True if started successfully
        """
        if self._running:
            return False

        server = self

        class BridgeHandler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def do_POST(self):
                # Auth check
                if server.auth_enabled:
                    auth_header = self.headers.get("Authorization", "")
                    if not auth_header.startswith("Bearer "):
                        self.send_error(401, "Missing authorization")
                        return
                    token = auth_header[7:]
                    if server.auth.verify_token(token) is None:
                        self.send_error(401, "Invalid token")
                        return

                # Read body
                content_length = int(self.headers.get("Content-Length", 0))
                if content_length == 0:
                    self.send_error(400, "Empty body")
                    return

                body = self.rfile.read(content_length)

                # Parse message
                try:
                    bridge_msg = BridgeMessage.from_json(body)
                except Exception as e:
                    self.send_error(400, f"Invalid message: {e}")
                    return

                # Handle message
                result = server.handlers.handle(bridge_msg)

                # Send response
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(result.to_json().encode())

            def do_GET(self):
                # Health check endpoint
                if self.path == "/health":
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "ok"}).encode())
                else:
                    self.send_error(404)

            def log_message(self, format, *args):
                pass  # Silent logging

        self.server = HTTPServer(("localhost", self.port), BridgeHandler)
        self._running = True
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        return True

    def stop(self):
        """Stop the bridge server."""
        if self.server:
            self.server.shutdown()
            self.server = None
            self._running = False

    @property
    def running(self) -> bool:
        """Check if server is running."""
        return self._running
