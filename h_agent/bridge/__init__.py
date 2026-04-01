"""
h_agent/bridge/ - IDE Bridge System

Provides HTTP server bridge for IDE integration.
"""

from .server import BridgeServer
from .protocol import BridgeMessage, MessageType
from .handlers import BridgeHandlers

__all__ = ["BridgeServer", "BridgeMessage", "MessageType", "BridgeHandlers"]
