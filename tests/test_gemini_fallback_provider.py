from __future__ import annotations

from types import SimpleNamespace

from voice.providers.base import VoiceProviderError


class FakeModels:
    def __init__(self, response):
        self.response = response
        self.calls: list[dict] = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


class FakeClient:
    def __init__(self, response):
        self.models = FakeModels(response)


def test_gemini_fallback_transcribe_uses_audio_part():
    from voice.providers.gemini_fallback import GeminiFallbackSpeechProvider

    provider = GeminiFallbackSpeechProvider(
        api_key="gemini-key",
        client=FakeClient(SimpleNamespace(text="hello world")),
    )

    transcript = provider.transcribe(b"pcm-bytes", "audio/pcm")

    assert transcript == "hello world"
    call = provider.client.models.calls[0]
    assert call["model"] == "gemini-2.5-flash"
    assert "Return only the literal spoken words" in call["contents"][0]
    assert call["contents"][1].inline_data.mime_type == "audio/pcm"


def test_gemini_fallback_synthesize_collects_audio_parts():
    from voice.providers.gemini_fallback import GeminiFallbackSpeechProvider

    response = SimpleNamespace(
        candidates=[
            SimpleNamespace(
                content=SimpleNamespace(
                    parts=[
                        SimpleNamespace(inline_data=SimpleNamespace(data=b"one")),
                        SimpleNamespace(inline_data=SimpleNamespace(data=b"two")),
                    ]
                )
            )
        ]
    )
    provider = GeminiFallbackSpeechProvider(
        api_key="gemini-key",
        client=FakeClient(response),
    )

    audio = provider.synthesize("hello")

    assert audio == b"onetwo"
    call = provider.client.models.calls[0]
    assert call["model"] == "gemini-2.5-flash-preview-tts"
    assert call["config"].response_modalities == ["AUDIO"]


def test_gemini_fallback_raises_when_tts_has_no_audio():
    from voice.providers.gemini_fallback import GeminiFallbackSpeechProvider

    response = SimpleNamespace(candidates=[])
    provider = GeminiFallbackSpeechProvider(
        api_key="gemini-key",
        client=FakeClient(response),
    )

    try:
        provider.synthesize("hello")
    except VoiceProviderError as exc:
        assert "missing audio" in str(exc).lower()
    else:
        raise AssertionError("Expected VoiceProviderError")
