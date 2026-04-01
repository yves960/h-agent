"""h_agent/session/resume.py - Session Resume Logic

Handles session recovery and context restoration.
"""

from typing import Optional

from h_agent.session.storage import SessionStorage
from h_agent.session.transcript import Transcript


class SessionResumer:
    """Handles resuming sessions from saved transcripts."""

    def __init__(self, storage: SessionStorage = None):
        """
        Initialize session resumer.
        
        Args:
            storage: SessionStorage instance. Creates default if None.
        """
        self.storage = storage or SessionStorage()

    def find_session(self, session_id: Optional[str] = None) -> Optional[Transcript]:
        """
        Find a session to resume.
        
        Args:
            session_id: Specific session ID to resume, or None for latest
            
        Returns:
            Transcript if found, None otherwise
        """
        if session_id:
            return self.storage.load_session(session_id)
        else:
            return self.storage.get_latest_session()

    def restore_context(self, transcript: Transcript) -> dict:
        """
        Extract context from a transcript for restoration.
        
        Args:
            transcript: The transcript to restore from
            
        Returns:
            Dict with messages list and token count for context restoration
        """
        messages = [
            {"role": m.role, "content": m.content}
            for m in transcript.messages
        ]
        return {
            "messages": messages,
            "total_tokens": transcript.total_tokens,
            "session_id": transcript.session_id,
        }

    def can_resume(self, session_id: Optional[str] = None) -> bool:
        """
        Check if a session can be resumed.
        
        Args:
            session_id: Specific session ID, or None to check for any session
            
        Returns:
            True if a session exists that can be resumed
        """
        return self.find_session(session_id) is not None
