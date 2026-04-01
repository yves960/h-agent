"""
h_agent/voice/ - Voice Input Module

Provides voice recording and speech-to-text capabilities.
"""

from .recorder import AudioRecorder
from .stt import SpeechToText

__all__ = ["AudioRecorder", "SpeechToText"]
