from __future__ import annotations

from google import genai
from google.genai import types

from voice.providers.base import VoiceProviderError

GEMINI_STT_MODEL = "gemini-2.5-flash"
GEMINI_TTS_MODEL = "gemini-2.5-flash-preview-tts"
GEMINI_TTS_VOICE = "Kore"


class GeminiFallbackSpeechProvider:
    def __init__(
        self,
        api_key: str,
        client: genai.Client | None = None,
        stt_model: str = GEMINI_STT_MODEL,
        tts_model: str = GEMINI_TTS_MODEL,
        voice_name: str = GEMINI_TTS_VOICE,
    ) -> None:
        self.api_key = api_key
        self.client = client or genai.Client(api_key=api_key)
        self.stt_model = stt_model
        self.tts_model = tts_model
        self.voice_name = voice_name

    def transcribe(self, audio_bytes: bytes, mime_type: str) -> str:
        try:
            response = self.client.models.generate_content(
                model=self.stt_model,
                contents=[
                    (
                        "Transcribe the user's spoken command from this audio. "
                        "Return only the literal spoken words. "
                        "If the audio is silence, breathing, noise, unclear, or non-speech, return an empty string. "
                        "Do not add labels, captions, markdown, explanations, guesses, or invented content."
                    ),
                    types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                ],
            )
        except Exception as exc:
            raise VoiceProviderError(f"Gemini STT request failed: {exc}") from exc

        transcript = (getattr(response, "text", "") or "").strip()
        if transcript == "":
            raise VoiceProviderError("Gemini STT response missing transcript")
        return transcript

    def synthesize(self, text: str) -> bytes:
        try:
            response = self.client.models.generate_content(
                model=self.tts_model,
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=self.voice_name
                            )
                        )
                    ),
                ),
            )
        except Exception as exc:
            raise VoiceProviderError(f"Gemini TTS request failed: {exc}") from exc

        audio_parts: list[bytes] = []
        for candidate in getattr(response, "candidates", []) or []:
            content = getattr(candidate, "content", None)
            for part in getattr(content, "parts", []) or []:
                inline_data = getattr(part, "inline_data", None)
                data = getattr(inline_data, "data", None)
                if data:
                    audio_parts.append(data)

        if not audio_parts:
            raise VoiceProviderError("Gemini TTS response missing audio")
        return b"".join(audio_parts)
