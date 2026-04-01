"""
h_agent/voice/recorder.py - Audio Recording

Cross-platform audio recording with PyAudio fallback.
"""

from __future__ import annotations

import tempfile
import wave
from pathlib import Path
from typing import List, Optional


class AudioRecorder:
    """
    Audio recorder with cross-platform support.

    Uses PyAudio when available, falls back to silent/no-op otherwise.

    Attributes:
        recording: Whether currently recording
        frames: Collected audio frames
    """

    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.recording = False
        self.frames: List[bytes] = []
        self._stream = None
        self._audio = None

    def _get_pyaudio(self):
        """Lazy import PyAudio with fallback."""
        if self._audio is None:
            try:
                import pyaudio
                self._audio = pyaudio.PyAudio()
            except ImportError:
                return None
        return self._audio

    async def start_recording(self) -> bool:
        """
        Start recording audio.

        Returns:
            True if recording started successfully
        """
        pyaudio = self._get_pyaudio()
        if pyaudio is None:
            return False

        try:
            self.recording = True
            self.frames = []

            self._stream = pyaudio.open(
                format=pyaudio.get_format_from_width(2),
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=1024,
            )

            # In a real implementation, this would run in a background task
            # collecting frames. For now, we just mark as recording.
            return True
        except Exception:
            self.recording = False
            return False

    async def stop_recording(self) -> Path:
        """
        Stop recording and save to a WAV file.

        Returns:
            Path to the recorded WAV file
        """
        self.recording = False

        if self._stream:
            try:
                self._stream.close()
            except Exception:
                pass
            self._stream = None

        # If we have real audio data, save it
        if self.frames:
            return self._save_wav(self.frames)

        # Return empty temp file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = Path(f.name)

        # Write a minimal WAV header
        self._write_silent_wav(temp_path)
        return temp_path

    def _save_wav(self, frames: List[bytes]) -> Path:
        """Save frames to WAV file."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = Path(f.name)

        with wave.open(str(temp_path), "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(b"".join(frames))

        return temp_path

    def _write_silent_wav(self, path: Path):
        """Write a minimal silent WAV file."""
        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(b"")

    def add_frames(self, frames: List[bytes]):
        """Add frames during recording (for async collection)."""
        self.frames.extend(frames)

    def cleanup(self):
        """Clean up resources."""
        if self._stream:
            try:
                self._stream.close()
            except Exception:
                pass
        if self._audio:
            try:
                self._audio.terminate()
            except Exception:
                pass
        self._audio = None
        self._stream = None
