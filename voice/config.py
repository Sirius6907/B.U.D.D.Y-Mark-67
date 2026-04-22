from __future__ import annotations

import os
from dataclasses import dataclass

from config.runtime import load_env_file


@dataclass(slots=True)
class VoiceSettings:
    sarvam_api_keys: list[str]
    sarvam_tts_model: str = "bulbul:v3"
    sarvam_tts_speaker: str = "Ritu"
    sarvam_tts_language: str = "en-IN"
    sarvam_tts_pitch: float = 0.0
    sarvam_tts_pace: float = 1.0
    sarvam_tts_temperature: float = 0.2
    sarvam_stt_language_hint: str = "unknown"
    primary_provider: str = "sarvam"
    fallback_provider: str = "gemini"


def _setting(name: str, default: str, file_values: dict[str, str]) -> str:
    value = os.environ.get(name, file_values.get(name, default))
    return value.strip() if isinstance(value, str) else default


def _float_setting(name: str, default: float, file_values: dict[str, str]) -> float:
    raw = _setting(name, str(default), file_values)
    try:
        return float(raw)
    except ValueError:
        return default


def _parse_key_list(raw: str) -> list[str]:
    keys: list[str] = []
    for chunk in raw.replace("\n", ",").replace(";", ",").split(","):
        item = chunk.strip()
        if item:
            keys.append(item)
    return keys


def load_voice_settings() -> VoiceSettings:
    file_values = load_env_file()
    api_key_source = _setting("SARVAM_API_KEYS", "", file_values)

    return VoiceSettings(
        sarvam_api_keys=_parse_key_list(api_key_source),
        sarvam_tts_model=_setting("SARVAM_TTS_MODEL", "bulbul:v3", file_values) or "bulbul:v3",
        sarvam_tts_speaker=_setting("SARVAM_TTS_SPEAKER", "Ritu", file_values) or "Ritu",
        sarvam_tts_language=_setting("SARVAM_TTS_LANGUAGE", "en-IN", file_values) or "en-IN",
        sarvam_tts_pitch=_float_setting("SARVAM_TTS_PITCH", 0.0, file_values),
        sarvam_tts_pace=_float_setting("SARVAM_TTS_PACE", 1.0, file_values),
        sarvam_tts_temperature=_float_setting("SARVAM_TTS_TEMPERATURE", 0.2, file_values),
        sarvam_stt_language_hint=_setting("SARVAM_STT_LANGUAGE_HINT", "unknown", file_values) or "unknown",
        primary_provider=_setting("VOICE_PROVIDER_PRIMARY", "sarvam", file_values) or "sarvam",
        fallback_provider=_setting("VOICE_PROVIDER_FALLBACK", "gemini", file_values) or "gemini",
    )
