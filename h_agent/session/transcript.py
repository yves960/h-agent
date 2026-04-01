"""h_agent/session/transcript.py - Session Transcript

Records conversation messages for session persistence and recovery.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional
import json
from pathlib import Path


@dataclass
class Message:
    """A single message in a transcript."""
    role: str  # user/assistant/tool
    content: str
    timestamp: str
    tokens: int = 0
    tool_calls: Optional[list] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class Transcript:
    """A complete session transcript."""
    session_id: str
    created_at: str
    messages: List[Message]
    model: str
    total_tokens: int = 0

    def save(self, path: Path) -> None:
        """Save transcript to a JSON file."""
        data = {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "messages": [m.to_dict() if isinstance(m, Message) else m for m in self.messages],
            "model": self.model,
            "total_tokens": self.total_tokens,
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: Path) -> "Transcript":
        """Load transcript from a JSON file."""
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        
        messages = [Message(**m) if isinstance(m, dict) else m for m in data.get("messages", [])]
        return cls(
            session_id=data["session_id"],
            created_at=data["created_at"],
            messages=messages,
            model=data["model"],
            total_tokens=data.get("total_tokens", 0),
        )

    def add_message(self, message: Message) -> None:
        """Add a message to the transcript."""
        self.messages.append(message)
        self.total_tokens += message.tokens

    @classmethod
    def create(cls, session_id: str, model: str) -> "Transcript":
        """Create a new transcript."""
        return cls(
            session_id=session_id,
            created_at=datetime.now().isoformat(),
            messages=[],
            model=model,
            total_tokens=0,
        )
