from config import runtime as runtime_config
from voice.config import load_voice_settings


def test_load_voice_settings_parses_multiple_sarvam_keys(monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEYS", "key-a,key-b,key-c")
    monkeypatch.setenv("SARVAM_TTS_MODEL", "bulbul:v3")
    monkeypatch.setenv("SARVAM_TTS_SPEAKER", "Ritu")

    settings = load_voice_settings()

    assert settings.sarvam_api_keys == ["key-a", "key-b", "key-c"]
    assert settings.sarvam_tts_model == "bulbul:v3"
    assert settings.sarvam_tts_speaker == "Ritu"


def test_load_voice_settings_uses_dotenv_and_keeps_stable_defaults(tmp_path, monkeypatch):
    for name in (
        "SARVAM_API_KEYS",
        "SARVAM_TTS_MODEL",
        "SARVAM_TTS_SPEAKER",
        "SARVAM_TTS_LANGUAGE",
        "SARVAM_TTS_PITCH",
        "SARVAM_TTS_PACE",
        "SARVAM_TTS_TEMPERATURE",
        "SARVAM_STT_LANGUAGE_HINT",
        "VOICE_PROVIDER_PRIMARY",
        "VOICE_PROVIDER_FALLBACK",
    ):
        monkeypatch.delenv(name, raising=False)

    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "SARVAM_API_KEYS=file-a,file-b",
                "SARVAM_TTS_LANGUAGE=en-IN",
                "SARVAM_TTS_PITCH=0.1",
                "SARVAM_TTS_PACE=0.9",
                "SARVAM_TTS_TEMPERATURE=0.3",
                "SARVAM_STT_LANGUAGE_HINT=unknown",
                "VOICE_PROVIDER_PRIMARY=sarvam",
                "VOICE_PROVIDER_FALLBACK=gemini",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(runtime_config, "ENV_FILE", env_file)

    settings = load_voice_settings()

    assert settings.sarvam_api_keys == ["file-a", "file-b"]
    assert settings.sarvam_tts_language == "en-IN"
    assert settings.sarvam_tts_pitch == 0.1
    assert settings.sarvam_tts_pace == 0.9
    assert settings.sarvam_tts_temperature == 0.3
    assert settings.sarvam_stt_language_hint == "unknown"
    assert settings.primary_provider == "sarvam"
    assert settings.fallback_provider == "gemini"
