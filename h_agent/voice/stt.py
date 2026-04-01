"""
h_agent/voice/stt.py - Speech to Text

Whisper-based speech recognition via OpenAI API.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


class SpeechToText:
    """
    Speech-to-text using OpenAI Whisper API.

    Args:
        model: Whisper model name (default: "whisper-1")
        api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
    """

    def __init__(
        self,
        model: str = "whisper-1",
        api_key: Optional[str] = None,
    ):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")

    async def transcribe(self, audio_path: Path) -> str:
        """
        Transcribe an audio file.

        Args:
            audio_path: Path to audio file (WAV, MP3, etc.)

        Returns:
            Transcribed text

        Raises:
            RuntimeError: If API key is missing or transcription fails
        """
        if not self.api_key:
            raise RuntimeError("OpenAI API key not configured. Set OPENAI_API_KEY env var.")

        try:
            from openai import OpenAI
        except ImportError:
            raise RuntimeError("openai package not installed. Run: pip install openai")

        client = OpenAI(api_key=self.api_key)

        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        try:
            with open(audio_path, "rb") as f:
                transcript = client.audio.transcriptions.create(
                    model=self.model,
                    file=f,
                )
            return transcript.text
        except Exception as e:
            raise RuntimeError(f"Transcription failed: {e}")

    async def transcribe_stream(self, audio_data: bytes) -> str:
        """
        Transcribe audio from a stream/bytes.

        Args:
            audio_data: Raw audio bytes

        Returns:
            Transcribed text
        """
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_data)
            temp_path = Path(f.name)

        try:
            return await self.transcribe(temp_path)
        finally:
            try:
                temp_path.unlink()
            except Exception:
                pass
