from __future__ import annotations

from typing import Protocol


class SpeechProvider(Protocol):
    def transcribe(self, audio_bytes: bytes, mime_type: str) -> str: ...

    def synthesize(self, text: str) -> bytes: ...


class VoiceProviderError(Exception):
    pass


class VoiceRoutingError(RuntimeError):
    pass
