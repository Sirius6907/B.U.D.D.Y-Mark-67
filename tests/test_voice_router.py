import pytest

from voice.router import VoiceRouter, VoiceRoutingError
from voice.providers.base import VoiceProviderError


class FailingProvider:
    def __init__(self, label):
        self.label = label

    def transcribe(self, audio_bytes, mime_type):
        raise VoiceProviderError(f"{self.label}-failed")

    def synthesize(self, text):
        raise VoiceProviderError(f"{self.label}-failed")


class SuccessProvider:
    def transcribe(self, audio_bytes, mime_type):
        return "hello"

    def synthesize(self, text):
        return b"audio"


def test_voice_router_falls_back_only_after_all_primary_keys_fail():
    router = VoiceRouter(
        primary_providers=[FailingProvider("a"), FailingProvider("b")],
        fallback_provider=SuccessProvider(),
    )

    assert router.transcribe(b"pcm", "audio/pcm") == "hello"


def test_voice_router_routes_synthesize_through_the_same_fallback_chain():
    router = VoiceRouter(
        primary_providers=[FailingProvider("a"), FailingProvider("b")],
        fallback_provider=SuccessProvider(),
    )

    assert router.synthesize("hello") == b"audio"


def test_voice_router_raises_after_all_providers_fail():
    router = VoiceRouter(
        primary_providers=[FailingProvider("a"), FailingProvider("b")],
        fallback_provider=FailingProvider("fallback"),
    )

    with pytest.raises(VoiceRoutingError) as exc_info:
        router.transcribe(b"pcm", "audio/pcm")

    assert "a-failed" in str(exc_info.value)
    assert "b-failed" in str(exc_info.value)
    assert "fallback-failed" in str(exc_info.value)


def test_voice_router_does_not_swallow_non_provider_exceptions():
    class BuggyProvider:
        def transcribe(self, audio_bytes, mime_type):
            raise ValueError("bug")

        def synthesize(self, text):
            raise ValueError("bug")

    router = VoiceRouter(
        primary_providers=[BuggyProvider()],
        fallback_provider=SuccessProvider(),
    )

    with pytest.raises(ValueError, match="bug"):
        router.transcribe(b"pcm", "audio/pcm")
