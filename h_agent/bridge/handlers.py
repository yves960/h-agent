"""
h_agent/bridge/handlers.py - Bridge Request Handlers

Request handlers for the IDE bridge server.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Dict, Any

from .protocol import BridgeMessage, MessageType


class BridgeHandlers:
    """
    Central handlers for bridge requests.

    Provides registered handlers for each message type.
    """

    def __init__(self):
        self._handlers: Dict[str, Callable] = {}

    def register(self, msg_type: str, handler: Callable[[BridgeMessage], BridgeMessage]):
        """Register a handler for a message type."""
        self._handlers[msg_type] = handler

    def handle(self, msg: BridgeMessage) -> BridgeMessage:
        """Handle a message, dispatching to the appropriate handler."""
        handler = self._handlers.get(msg.type)
        if handler:
            try:
                return handler(msg)
            except Exception as e:
                return msg.error_response(str(e))
        return msg.error_response(f"No handler for message type: {msg.type}")


# Default handler implementations

def create_default_handlers() -> BridgeHandlers:
    """Create handlers with default implementations."""
    handlers = BridgeHandlers()

    # GET_CONTEXT - return current file context
    def handle_get_context(msg: BridgeMessage) -> BridgeMessage:
        payload = msg.payload
        # Return current editor context
        return msg.success({
            "file": payload.get("file", ""),
            "language": payload.get("language", "plaintext"),
            "content": "",
        })

    # GET_FILE - read file contents
    def handle_get_file(msg: BridgeMessage) -> BridgeMessage:
        file_path = msg.payload.get("path", "")
        try:
            path = Path(file_path)
            if path.exists() and path.is_file():
                content = path.read_text()
                return msg.success({"content": content})
            return msg.error_response(f"File not found: {file_path}")
        except Exception as e:
            return msg.error_response(str(e))

    # GET_SELECTION - get selected text
    def handle_get_selection(msg: BridgeMessage) -> BridgeMessage:
        return msg.success({"selection": msg.payload.get("selection", "")})

    # GET_CURSOR - get cursor position
    def handle_get_cursor(msg: BridgeMessage) -> BridgeMessage:
        return msg.success({
            "line": msg.payload.get("line", 1),
            "column": msg.payload.get("column", 1),
        })

    # PING - health check
    def handle_ping(msg: BridgeMessage) -> BridgeMessage:
        return BridgeMessage(id=msg.id, type=MessageType.PONG, payload={"status": "ok"})

    handlers.register(MessageType.GET_CONTEXT, handle_get_context)
    handlers.register(MessageType.GET_FILE, handle_get_file)
    handlers.register(MessageType.GET_SELECTION, handle_get_selection)
    handlers.register(MessageType.GET_CURSOR, handle_get_cursor)
    handlers.register(MessageType.PING, handle_ping)

    return handlers
