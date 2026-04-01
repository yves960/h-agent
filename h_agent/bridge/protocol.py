"""
h_agent/bridge/protocol.py - Bridge Message Protocol

Defines the message protocol for IDE bridge communication.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, Optional


class MessageType(str, Enum):
    """Bridge message types."""
    # Editor <-> Agent
    GET_CONTEXT = "get_context"
    GET_FILE = "get_file"
    GET_SELECTION = "get_selection"
    GET_CURSOR = "get_cursor"

    # Agent -> Editor
    NAVIGATE = "navigate"
    HIGHLIGHT = "highlight"
    SHOW_ERROR = "show_error"
    SHOW_WARNING = "show_warning"
    INSERT_TEXT = "insert_text"
    REPLACE_SELECTION = "replace_selection"

    # Editor -> Agent
    FILE_CHANGED = "file_changed"
    BUFFER_CHANGED = "buffer_changed"
    FOCUS_CHANGED = "focus_changed"

    # System
    PING = "ping"
    PONG = "pong"
    ERROR = "error"


@dataclass
class BridgeMessage:
    """
    Bridge message structure.

    All messages follow this format:
    - id: unique message identifier
    - type: message type (MessageType)
    - payload: message data
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str | bytes) -> "BridgeMessage":
        """Deserialize from JSON string."""
        if isinstance(data, bytes):
            data = data.decode()
        obj = json.loads(data)
        return cls(
            id=obj.get("id", ""),
            type=obj.get("type", ""),
            payload=obj.get("payload", {}),
            error=obj.get("error"),
        )

    def success(self, payload: Dict[str, Any] | None = None) -> "BridgeMessage":
        """Create a success response."""
        return BridgeMessage(id=self.id, type=self.type + "_response", payload=payload or {})

    def error_response(self, error: str) -> "BridgeMessage":
        """Create an error response."""
        return BridgeMessage(id=self.id, type=self.type + "_response", error=error)
