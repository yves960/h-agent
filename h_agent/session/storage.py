"""h_agent/session/storage.py - Session Storage Management

Handles saving, loading, and listing session transcripts.
"""

import json
from pathlib import Path
from typing import List, Optional
import uuid

from h_agent.session.transcript import Transcript, Message


class SessionStorage:
    """Manages session transcript storage on disk."""

    def __init__(self, base_dir: Path = None):
        """
        Initialize session storage.
        
        Args:
            base_dir: Directory to store sessions. Defaults to ~/.h-agent/sessions
        """
        self.base_dir = base_dir or Path.home() / ".h-agent" / "sessions"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _session_path(self, session_id: str) -> Path:
        """Get the file path for a session."""
        return self.base_dir / f"{session_id}.json"

    def save_session(self, transcript: Transcript) -> Path:
        """
        Save a session transcript to disk.
        
        Args:
            transcript: The transcript to save
            
        Returns:
            Path where the transcript was saved
        """
        path = self._session_path(transcript.session_id)
        transcript.save(path)
        return path

    def load_session(self, session_id: str) -> Optional[Transcript]:
        """
        Load a session transcript from disk.
        
        Args:
            session_id: The session ID to load
            
        Returns:
            Transcript if found, None otherwise
        """
        path = self._session_path(session_id)
        if path.exists():
            return Transcript.load(path)
        return None

    def list_sessions(self) -> List[dict]:
        """
        List all saved sessions.
        
        Returns:
            List of session info dicts sorted by creation date (newest first)
        """
        sessions = []
        for path in self.base_dir.glob("*.json"):
            try:
                t = Transcript.load(path)
                sessions.append({
                    "id": t.session_id,
                    "created": t.created_at,
                    "messages": len(t.messages),
                    "tokens": t.total_tokens,
                    "model": t.model,
                })
            except (json.JSONDecodeError, KeyError, ValueError):
                # Skip invalid session files (e.g., old format or corrupt)
                continue
        
        return sorted(sessions, key=lambda x: x["created"], reverse=True)

    def get_latest_session(self) -> Optional[Transcript]:
        """
        Get the most recently created session.
        
        Returns:
            Latest transcript if any exist, None otherwise
        """
        sessions = self.list_sessions()
        if sessions:
            return self.load_session(sessions[0]["id"])
        return None

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session from disk.
        
        Args:
            session_id: The session ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        path = self._session_path(session_id)
        if path.exists():
            path.unlink()
            return True
        return False

    def generate_session_id(self) -> str:
        """
        Generate a new unique session ID.
        
        Returns:
            A new session ID in format 'sess-xxxxxxxx'
        """
        return f"sess-{uuid.uuid4().hex[:8]}"
