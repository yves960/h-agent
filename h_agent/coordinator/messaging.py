"""
h_agent/coordinator/messaging.py - Agent Messaging System

File-based message bus for agent-to-agent communication.
Inspired by Claude Code's inbox-based messaging pattern.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
import json
import time


@dataclass
class Message:
    """Represents a message between agents."""
    sender: str
    recipient: str
    content: str
    timestamp: float
    msg_type: str = "message"


class MessageBus:
    """
    Agent间消息总线 - File-based messaging.
    
    Uses JSON files in inbox directories for reliable message delivery.
    """
    
    def __init__(self, base_dir: Path = None):
        """
        Initialize the message bus.
        
        Args:
            base_dir: Base directory for inbox storage.
                     Defaults to ~/.h-agent/inbox
        """
        self.base_dir = base_dir or Path.home() / ".h-agent" / "inbox"
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def send(
        self,
        sender: str,
        recipient: str,
        content: str,
        msg_type: str = "message",
        **extra: str,
    ) -> str:
        """
        Send a message to an agent.
        
        Args:
            sender: Sender identifier
            recipient: Recipient identifier
            content: Message content
            msg_type: Message type (message, task, broadcast)
            **extra: Additional metadata
            
        Returns:
            Confirmation string
        """
        msg = Message(
            sender=sender,
            recipient=recipient,
            content=content,
            timestamp=time.time(),
            msg_type=msg_type,
        )
        
        # Store in recipient's inbox
        inbox_dir = self.base_dir / recipient
        inbox_dir.mkdir(parents=True, exist_ok=True)
        
        msg_file = inbox_dir / f"{int(time.time() * 1000)}.json"
        
        msg_data = {
            "sender": msg.sender,
            "recipient": msg.recipient,
            "content": msg.content,
            "timestamp": msg.timestamp,
            "type": msg.msg_type,
        }
        msg_data.update(extra)
        
        with open(msg_file, "w") as f:
            json.dump(msg_data, f)
        
        return f"Message sent to {recipient}"
    
    def read(self, recipient: str) -> List[Message]:
        """
        Read all messages from an inbox.
        
        Args:
            recipient: Inbox owner identifier
            
        Returns:
            List of messages
        """
        inbox_dir = self.base_dir / recipient
        if not inbox_dir.exists():
            return []
        
        messages = []
        for msg_file in sorted(inbox_dir.glob("*.json")):
            try:
                with open(msg_file) as f:
                    data = json.load(f)
                    messages.append(Message(
                        sender=data.get("sender", ""),
                        recipient=data.get("recipient", recipient),
                        content=data.get("content", ""),
                        timestamp=data.get("timestamp", 0),
                        msg_type=data.get("type", "message"),
                    ))
            except (json.JSONDecodeError, IOError):
                continue
        
        return messages
    
    def read_and_clear(self, recipient: str) -> List[Message]:
        """
        Read and clear all messages from an inbox.
        
        Args:
            recipient: Inbox owner identifier
            
        Returns:
            List of messages that were in the inbox
        """
        messages = self.read(recipient)
        self.clear(recipient)
        return messages
    
    def clear(self, recipient: str) -> None:
        """
        Clear all messages from an inbox.
        
        Args:
            recipient: Inbox owner identifier
        """
        inbox_dir = self.base_dir / recipient
        if inbox_dir.exists():
            for f in inbox_dir.glob("*.json"):
                f.unlink()
    
    def count(self, recipient: str) -> int:
        """
        Count messages in an inbox.
        
        Args:
            recipient: Inbox owner identifier
            
        Returns:
            Number of messages
        """
        inbox_dir = self.base_dir / recipient
        if not inbox_dir.exists():
            return 0
        return len(list(inbox_dir.glob("*.json")))
    
    def broadcast(self, sender: str, recipients: List[str], content: str) -> str:
        """
        Broadcast a message to multiple recipients.
        
        Args:
            sender: Sender identifier
            recipients: List of recipient identifiers
            content: Message content
            
        Returns:
            Confirmation string with count
        """
        count = 0
        for recipient in recipients:
            if recipient != sender:
                self.send(sender, recipient, content, msg_type="broadcast")
                count += 1
        return f"Broadcast to {count} recipients"
