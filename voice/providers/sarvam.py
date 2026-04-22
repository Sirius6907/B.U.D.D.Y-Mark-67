from __future__ import annotations

import base64
from typing import Any

import requests

from voice.config import VoiceSettings
from voice.providers.base import VoiceProviderError

SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"
SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"
SARVAM_STT_MODEL = "saaras:v3"
SARVAM_REQUEST_TIMEOUT_SECONDS = 30
SUPPORTED_STT_MODES = {"transcribe", "translate", "verbatim", "translit", "codemix"}


def _upload_filename_for_mime_type(mime_type: str) -> str:
    return {
        "audio/wav": "audio.wav",
        "audio/x-wav": "audio.wav",
        "audio/pcm": "audio.pcm",
    }.get(mime_type, "audio")


class SarvamSpeechProvider:
    def __init__(
        self,
        api_key: str,
        settings: VoiceSettings,
        session: requests.Session | None = None,
    ):
        self.api_key = api_key
        self.settings = settings
        self.session = session or requests.Session()

    def _build_tts_payload(self, text: str) -> dict[str, Any]:
        if self.settings.sarvam_tts_model != "bulbul:v3":
            raise VoiceProviderError(
                f"Sarvam TTS payloads require bulbul:v3, got {self.settings.sarvam_tts_model}"
            )

        payload: dict[str, Any] = {
            "text": text,
            "model": self.settings.sarvam_tts_model,
            "speaker": self.settings.sarvam_tts_speaker.lower(),
            "target_language_code": self.settings.sarvam_tts_language,
            "pace": self.settings.sarvam_tts_pace,
            "temperature": self.settings.sarvam_tts_temperature,
        }

        return payload

    def transcribe(self, audio_bytes: bytes, mime_type: str, mode: str = "transcribe") -> str:
        if mode not in SUPPORTED_STT_MODES:
            raise VoiceProviderError(f"Unsupported STT mode: {mode}")

        data = {
            "model": SARVAM_STT_MODEL,
            "mode": mode,
            "language_code": self.settings.sarvam_stt_language_hint,
        }
        if mime_type == "audio/pcm":
            data["input_audio_codec"] = "pcm_s16le"

        try:
            response = self.session.post(
                SARVAM_STT_URL,
                headers={"api-subscription-key": self.api_key},
                data=data,
                files={"file": (_upload_filename_for_mime_type(mime_type), audio_bytes, mime_type)},
                timeout=SARVAM_REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            raise VoiceProviderError(f"Sarvam STT request failed: {exc}") from exc

        if "transcript" not in payload or payload["transcript"] is None:
            raise VoiceProviderError("Sarvam STT response missing transcript")
        return payload["transcript"]

    def synthesize(self, text: str) -> bytes:
        try:
            response = self.session.post(
                SARVAM_TTS_URL,
                headers={
                    "api-subscription-key": self.api_key,
                    "Content-Type": "application/json",
                },
                json=self._build_tts_payload(text),
                timeout=SARVAM_REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json()
            audios = payload.get("audios") or []
            if not audios:
                raise VoiceProviderError("Sarvam TTS response missing audios")
            return base64.b64decode(audios[0])
        except VoiceProviderError:
            raise
        except Exception as exc:
            raise VoiceProviderError(f"Sarvam TTS request failed: {exc}") from exc
