"""
h_agent/commands/voice.py - Voice Input Command

Voice recording and transcription command.
"""

from __future__ import annotations

import asyncio
from h_agent.commands.base import Command, CommandContext, CommandResult
from h_agent.voice.recorder import AudioRecorder
from h_agent.voice.stt import SpeechToText


# Global recorder and stt
_recorder: AudioRecorder | None = None
_stt: SpeechToText | None = None


def get_recorder() -> AudioRecorder:
    """Get or create the global audio recorder."""
    global _recorder
    if _recorder is None:
        _recorder = AudioRecorder()
    return _recorder


def get_stt() -> SpeechToText:
    """Get or create the global speech-to-text instance."""
    global _stt
    if _stt is None:
        _stt = SpeechToText()
    return _stt


class VoiceCommand(Command):
    """Voice input command for recording and transcription."""

    name = "voice"
    description = "Voice input: record and transcribe audio"
    aliases = []

    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute voice command."""
        recorder = get_recorder()
        stt = get_stt()

        if args == "start":
            if recorder.recording:
                return CommandResult.err("Already recording")

            success = await recorder.start_recording()
            if success:
                context.set("voice_recording", True)
                return CommandResult.ok("Recording started. Use /voice stop to finish.")
            return CommandResult.err("Failed to start recording. Is PyAudio installed?")

        elif args == "stop":
            if not recorder.recording:
                return CommandResult.err("Not recording")

            audio_path = await recorder.stop_recording()
            context.set("voice_recording", False)

            # Try to transcribe
            try:
                text = await stt.transcribe(audio_path)
                if text.strip():
                    return CommandResult.ok(f"Transcription: {text}")
                return CommandResult.ok("No speech detected.")
            except Exception as e:
                return CommandResult.ok(f"Audio saved but transcription failed: {e}")

        elif args == "status":
            if recorder.recording:
                return CommandResult.ok("Recording in progress")
            return CommandResult.ok("Not recording")

        else:
            return CommandResult.ok(
                "Voice commands:\n"
                "  /voice start - Start recording\n"
                "  /voice stop  - Stop and transcribe\n"
                "  /voice status - Check recording status"
            )
