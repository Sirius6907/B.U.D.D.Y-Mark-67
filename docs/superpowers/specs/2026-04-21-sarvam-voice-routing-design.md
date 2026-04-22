## Sarvam Voice Routing Design

### Goal

Replace Gemini as the primary speech input/output layer while keeping the existing task-performing agent, planner, runtime coordinator, and tool execution flow intact.

Sarvam will handle:

- Speech-to-text input
- Text-to-speech output
- Request-scoped API-key rotation across multiple Sarvam accounts

Gemini will remain available only as an automatic fallback voice provider after all configured Sarvam keys are exhausted for the current STT or TTS request.

### Requirements

- Sarvam is the default voice provider for both STT and TTS
- Gemini is not removed from the project, only demoted to fallback voice I/O
- The main agent logic remains unchanged
- Sarvam keys are stored in a project-root `.env`
- Multiple Sarvam keys are supported
- The app tries Sarvam keys one by one for each request until one succeeds
- Fallback to Gemini happens automatically only after all Sarvam keys fail for the current request
- TTS stays fixed to Bulbul v3 with female `Ritu` voice
- Voice settings must stay stable across keys:
  - same endpoint family
  - same model
  - same speaker
  - same tone/pitch/language defaults
- TTS must support English and Hinglish text input

### Architecture

Add a voice-provider abstraction between the UI/audio loop and the assistant runtime:

- `voice/providers/base.py`
  - common STT/TTS provider interface
- `voice/providers/sarvam.py`
  - Sarvam STT/TTS implementation
- `voice/providers/gemini_fallback.py`
  - fallback voice implementation using the existing Gemini-based path
- `voice/router.py`
  - request-scoped key rotation and fallback control
- `voice/config.py`
  - `.env` loading and validation for Sarvam/Gemini voice settings

The existing agent runtime remains responsible for intent handling, planning, and tool execution. The new voice layer only converts:

- microphone audio -> transcript
- assistant response text -> playable audio

### Data Flow

1. Microphone captures PCM frames.
2. Voice router sends the audio request to Sarvam STT using the first available key.
3. If the key fails due to auth/rate-limit/provider failure, the router retries the next Sarvam key.
4. If all Sarvam keys fail, the router falls back to Gemini STT for that request.
5. The transcript is passed into the existing orchestrator/runtime.
6. Assistant text response is passed to the voice router for TTS.
7. Sarvam Bulbul v3 with speaker `Ritu` is used first.
8. If all Sarvam keys fail for that TTS request, Gemini TTS fallback is used automatically.
9. Audio is played through the existing local output stream.

### Configuration

Add `.env` support with variables like:

- `SARVAM_API_KEYS`
- `SARVAM_TTS_MODEL`
- `SARVAM_TTS_SPEAKER`
- `SARVAM_TTS_LANGUAGE`
- `SARVAM_TTS_PITCH`
- `SARVAM_TTS_PACE`
- `SARVAM_TTS_TEMPERATURE`
- `SARVAM_STT_LANGUAGE_HINT`
- `VOICE_PROVIDER_PRIMARY`
- `VOICE_PROVIDER_FALLBACK`

`SARVAM_API_KEYS` will be a delimited string parsed into a list.

`.env` must be ignored by git.

### Failure Handling

- Empty Sarvam key list: use Gemini fallback immediately and log a warning
- One Sarvam key rate-limited: continue to the next key without user interruption
- Non-retryable request errors: fail that key and continue to next key
- Total Sarvam exhaustion: fallback automatically to Gemini
- Gemini fallback failure: surface an actionable runtime error to the UI/log

### Testing

Add tests for:

- `.env` parsing into ordered Sarvam key list
- request-scoped key rotation
- fallback only after full Sarvam exhaustion
- fixed TTS config enforcing `Bulbul v3` + `Ritu`
- stable provider behavior when Sarvam is unavailable
- regression coverage for existing startup/runtime checks

### Implementation Notes

- Keep the current Gemini code path isolated as fallback rather than deleting it
- Avoid embedding provider logic directly in `main.py`; use the router abstraction
- Minimize changes to the planner/runtime/tool stack
- Preserve the working startup fixes already added during stabilization
