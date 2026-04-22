from __future__ import annotations

from collections.abc import Iterable

from voice.providers.base import SpeechProvider, VoiceProviderError, VoiceRoutingError


class VoiceRouter:
    def __init__(self, primary_providers: Iterable[SpeechProvider], fallback_provider: SpeechProvider):
        self.primary_providers = list(primary_providers)
        self.fallback_provider = fallback_provider

    def transcribe(self, audio_bytes: bytes, mime_type: str) -> str:
        return self._route("transcribe", audio_bytes, mime_type)

    def synthesize(self, text: str) -> bytes:
        return self._route("synthesize", text)

    def _route(self, method_name: str, *args):
        errors: list[str] = []
        for provider in [*self.primary_providers, self.fallback_provider]:
            try:
                return getattr(provider, method_name)(*args)
            except VoiceProviderError as exc:  # pragma: no cover - aggregated into message
                errors.append(str(exc))
        raise VoiceRoutingError("; ".join(errors))
