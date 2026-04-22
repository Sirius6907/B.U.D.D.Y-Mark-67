import base64

import pytest

from voice.config import VoiceSettings


class DummyResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")


class DummySession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response


def build_settings(**overrides):
    values = {
        "sarvam_api_keys": ["key-1"],
        "sarvam_tts_model": "bulbul:v3",
        "sarvam_tts_speaker": "Ritu",
        "sarvam_tts_language": "en-IN",
        "sarvam_tts_pitch": 0.0,
        "sarvam_tts_pace": 1.0,
        "sarvam_tts_temperature": 0.2,
        "sarvam_stt_language_hint": "unknown",
        "primary_provider": "sarvam",
        "fallback_provider": "gemini",
    }
    values.update(overrides)
    return VoiceSettings(**values)


def test_sarvam_provider_builds_bulbul_v3_payload_with_supported_fields_only():
    from voice.providers.sarvam import SarvamSpeechProvider

    provider = SarvamSpeechProvider(
        api_key="key-1",
        settings=build_settings(
            sarvam_tts_speaker="Ritu",
            sarvam_tts_pitch=0.5,
            sarvam_tts_pace=1.5,
            sarvam_tts_temperature=0.7,
        ),
        session=DummySession(DummyResponse({"audios": []})),
    )

    payload = provider._build_tts_payload("Hello")

    assert payload == {
        "text": "Hello",
        "model": "bulbul:v3",
        "speaker": "ritu",
        "target_language_code": "en-IN",
        "pace": 1.5,
        "temperature": 0.7,
    }


def test_sarvam_provider_transcribe_uses_saaras_v3_and_requested_mode():
    from voice.providers.sarvam import SarvamSpeechProvider

    session = DummySession(DummyResponse({"transcript": "mixed transcript"}))
    provider = SarvamSpeechProvider(
        api_key="key-1",
        settings=build_settings(sarvam_stt_language_hint="en-IN"),
        session=session,
    )

    transcript = provider.transcribe(b"pcm-bytes", "audio/pcm", mode="codemix")

    assert transcript == "mixed transcript"
    assert len(session.calls) == 1
    url, kwargs = session.calls[0]
    assert url == "https://api.sarvam.ai/speech-to-text"
    assert kwargs["headers"]["api-subscription-key"] == "key-1"
    assert kwargs["data"] == {
        "model": "saaras:v3",
        "mode": "codemix",
        "language_code": "en-IN",
        "input_audio_codec": "pcm_s16le",
    }
    assert kwargs["files"]["file"] == ("audio.pcm", b"pcm-bytes", "audio/pcm")
    assert kwargs["timeout"] == 30


def test_sarvam_provider_names_wav_uploads_with_wav_extension():
    from voice.providers.sarvam import SarvamSpeechProvider

    session = DummySession(DummyResponse({"transcript": "open chrome"}))
    provider = SarvamSpeechProvider(
        api_key="key-1",
        settings=build_settings(),
        session=session,
    )

    provider.transcribe(b"wav-bytes", "audio/wav")

    _, kwargs = session.calls[0]
    assert kwargs["files"]["file"] == ("audio.wav", b"wav-bytes", "audio/wav")
    assert "input_audio_codec" not in kwargs["data"]


def test_sarvam_provider_synthesize_decodes_first_audio():
    from voice.providers.sarvam import SarvamSpeechProvider

    expected_audio = b"wav-bytes"
    session = DummySession(
        DummyResponse({"audios": [base64.b64encode(expected_audio).decode("ascii")]})
    )
    provider = SarvamSpeechProvider(
        api_key="key-1",
        settings=build_settings(),
        session=session,
    )

    audio = provider.synthesize("Hello")

    assert audio == expected_audio
    assert len(session.calls) == 1
    url, kwargs = session.calls[0]
    assert url == "https://api.sarvam.ai/text-to-speech"
    assert kwargs["headers"] == {
        "api-subscription-key": "key-1",
        "Content-Type": "application/json",
    }
    assert kwargs["json"]["speaker"] == "ritu"
    assert "pitch" not in kwargs["json"]
    assert kwargs["timeout"] == 30


def test_sarvam_provider_allows_empty_transcript():
    from voice.providers.sarvam import SarvamSpeechProvider

    session = DummySession(DummyResponse({"transcript": ""}))
    provider = SarvamSpeechProvider(
        api_key="key-1",
        settings=build_settings(),
        session=session,
    )

    assert provider.transcribe(b"audio", "audio/wav") == ""


def test_sarvam_provider_rejects_unknown_stt_mode():
    from voice.providers.sarvam import SarvamSpeechProvider
    from voice.providers.base import VoiceProviderError

    provider = SarvamSpeechProvider(
        api_key="key-1",
        settings=build_settings(),
        session=DummySession(DummyResponse({"transcript": "unused"})),
    )

    with pytest.raises(VoiceProviderError, match="Unsupported STT mode"):
        provider.transcribe(b"audio", "audio/wav", mode="invalid")


def test_sarvam_provider_rejects_missing_transcript():
    from voice.providers.sarvam import SarvamSpeechProvider
    from voice.providers.base import VoiceProviderError

    provider = SarvamSpeechProvider(
        api_key="key-1",
        settings=build_settings(),
        session=DummySession(DummyResponse({"language_code": "en-IN"})),
    )

    with pytest.raises(VoiceProviderError, match="missing transcript"):
        provider.transcribe(b"audio", "audio/wav")


def test_sarvam_provider_requires_bulbul_v3_for_tts():
    from voice.providers.sarvam import SarvamSpeechProvider
    from voice.providers.base import VoiceProviderError

    provider = SarvamSpeechProvider(
        api_key="key-1",
        settings=build_settings(sarvam_tts_model="bulbul:v2"),
        session=DummySession(DummyResponse({"audios": []})),
    )

    with pytest.raises(VoiceProviderError, match="bulbul:v3"):
        provider._build_tts_payload("Hello")
