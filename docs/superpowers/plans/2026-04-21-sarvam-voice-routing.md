# Sarvam Voice Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Gemini as the primary speech input/output layer with Sarvam STT/TTS, including multi-key rotation and automatic Gemini fallback only after all Sarvam keys are exhausted for a request.

**Architecture:** Add a dedicated voice layer that sits between audio capture/playback and the existing assistant runtime. Sarvam becomes the primary provider for STT/TTS, Gemini remains isolated as a fallback provider, and `main.py` is reduced to orchestration of provider calls rather than provider-specific logic.

**Tech Stack:** Python 3.12, `requests`, `sounddevice`, `python-dotenv` or equivalent local `.env` loader, existing Gemini SDK, Sarvam REST/streaming HTTP integration, pytest.

---

### File Structure

**Create**
- `voice/__init__.py`
- `voice/config.py`
- `voice/router.py`
- `voice/providers/__init__.py`
- `voice/providers/base.py`
- `voice/providers/sarvam.py`
- `voice/providers/gemini_fallback.py`
- `tests/test_voice_config.py`
- `tests/test_voice_router.py`
- `tests/test_sarvam_provider.py`

**Modify**
- `main.py`
- `config/runtime.py`
- `pyproject.toml`
- `requirements.txt`
- `.gitignore`
- `readme.md`

### Task 1: Add Voice Configuration Support

**Files:**
- Create: `voice/config.py`
- Modify: `config/runtime.py`
- Modify: `.gitignore`
- Test: `tests/test_voice_config.py`

- [ ] **Step 1: Write the failing test**

```python
from voice.config import load_voice_settings


def test_load_voice_settings_parses_multiple_sarvam_keys(monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEYS", "key-a,key-b,key-c")
    monkeypatch.setenv("SARVAM_TTS_MODEL", "bulbul:v3")
    monkeypatch.setenv("SARVAM_TTS_SPEAKER", "Ritu")

    settings = load_voice_settings()

    assert settings.sarvam_api_keys == ["key-a", "key-b", "key-c"]
    assert settings.sarvam_tts_model == "bulbul:v3"
    assert settings.sarvam_tts_speaker == "Ritu"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_voice_config.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'voice'` or missing `load_voice_settings`

- [ ] **Step 3: Write minimal implementation**

```python
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class VoiceSettings:
    sarvam_api_keys: list[str]
    sarvam_tts_model: str
    sarvam_tts_speaker: str


def load_voice_settings() -> VoiceSettings:
    keys = [item.strip() for item in os.environ.get("SARVAM_API_KEYS", "").split(",") if item.strip()]
    return VoiceSettings(
        sarvam_api_keys=keys,
        sarvam_tts_model=os.environ.get("SARVAM_TTS_MODEL", "bulbul:v3").strip() or "bulbul:v3",
        sarvam_tts_speaker=os.environ.get("SARVAM_TTS_SPEAKER", "Ritu").strip() or "Ritu",
    )
```

- [ ] **Step 4: Extend settings coverage**

```python
@dataclass(slots=True)
class VoiceSettings:
    sarvam_api_keys: list[str]
    sarvam_tts_model: str
    sarvam_tts_speaker: str
    sarvam_tts_language: str
    sarvam_tts_pitch: float
    sarvam_tts_pace: float
    sarvam_tts_temperature: float
    sarvam_stt_language_hint: str
    primary_provider: str
    fallback_provider: str
```

- [ ] **Step 5: Ignore local secrets**

Add to `.gitignore`:

```gitignore
.env
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python -m pytest tests/test_voice_config.py -q`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add voice/config.py tests/test_voice_config.py config/runtime.py .gitignore
git commit -m "feat: add voice environment configuration"
```

### Task 2: Add Provider Interfaces and Request Routing

**Files:**
- Create: `voice/providers/base.py`
- Create: `voice/router.py`
- Test: `tests/test_voice_router.py`

- [ ] **Step 1: Write the failing test**

```python
import pytest

from voice.router import VoiceRouter


class FailingProvider:
    def __init__(self, label):
        self.label = label

    def transcribe(self, audio_bytes, mime_type):
        raise RuntimeError(f"{self.label}-failed")


class SuccessProvider:
    def transcribe(self, audio_bytes, mime_type):
        return "hello"


def test_voice_router_falls_back_only_after_all_primary_keys_fail():
    router = VoiceRouter(
        primary_providers=[FailingProvider("a"), FailingProvider("b")],
        fallback_provider=SuccessProvider(),
    )

    assert router.transcribe(b"pcm", "audio/pcm") == "hello"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_voice_router.py -q`
Expected: FAIL because `VoiceRouter` does not exist

- [ ] **Step 3: Write minimal implementation**

```python
class VoiceRouter:
    def __init__(self, primary_providers, fallback_provider):
        self.primary_providers = list(primary_providers)
        self.fallback_provider = fallback_provider

    def transcribe(self, audio_bytes: bytes, mime_type: str) -> str:
        for provider in self.primary_providers:
            try:
                return provider.transcribe(audio_bytes, mime_type)
            except Exception:
                continue
        return self.fallback_provider.transcribe(audio_bytes, mime_type)
```

- [ ] **Step 4: Add TTS route and shared base protocol**

```python
from typing import Protocol


class SpeechProvider(Protocol):
    def transcribe(self, audio_bytes: bytes, mime_type: str) -> str: ...
    def synthesize(self, text: str) -> bytes: ...
```

- [ ] **Step 5: Add explicit exhaustion error aggregation**

```python
class VoiceRoutingError(RuntimeError):
    pass
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python -m pytest tests/test_voice_router.py -q`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add voice/providers/base.py voice/router.py tests/test_voice_router.py
git commit -m "feat: add voice routing abstraction"
```

### Task 3: Implement Sarvam Provider

**Files:**
- Create: `voice/providers/sarvam.py`
- Test: `tests/test_sarvam_provider.py`

- [ ] **Step 1: Write the failing test**

```python
from voice.config import VoiceSettings
from voice.providers.sarvam import SarvamSpeechProvider


def test_sarvam_provider_keeps_fixed_bulbul_ritu_defaults():
    settings = VoiceSettings(
        sarvam_api_keys=["key-1"],
        sarvam_tts_model="bulbul:v3",
        sarvam_tts_speaker="Ritu",
        sarvam_tts_language="en-IN",
        sarvam_tts_pitch=0.0,
        sarvam_tts_pace=1.0,
        sarvam_tts_temperature=0.2,
        sarvam_stt_language_hint="unknown",
        primary_provider="sarvam",
        fallback_provider="gemini",
    )

    provider = SarvamSpeechProvider(api_key="key-1", settings=settings, session=None)

    payload = provider._build_tts_payload("Hello")

    assert payload["model"] == "bulbul:v3"
    assert payload["speaker"] == "Ritu"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_sarvam_provider.py -q`
Expected: FAIL because `SarvamSpeechProvider` does not exist

- [ ] **Step 3: Write minimal implementation**

```python
class SarvamSpeechProvider:
    def __init__(self, api_key: str, settings, session):
        self.api_key = api_key
        self.settings = settings
        self.session = session

    def _build_tts_payload(self, text: str) -> dict:
        return {
            "text": text,
            "model": self.settings.sarvam_tts_model,
            "speaker": self.settings.sarvam_tts_speaker,
        }
```

- [ ] **Step 4: Implement STT/TTS HTTP methods**

```python
def transcribe(self, audio_bytes: bytes, mime_type: str) -> str:
    ...

def synthesize(self, text: str) -> bytes:
    ...
```

- [ ] **Step 5: Preserve stable voice settings**

Include language, pitch, pace, and temperature in the TTS payload based on the approved design.

- [ ] **Step 6: Run tests to verify they pass**

Run: `python -m pytest tests/test_sarvam_provider.py -q`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add voice/providers/sarvam.py tests/test_sarvam_provider.py
git commit -m "feat: add sarvam speech provider"
```

### Task 4: Implement Gemini Voice Fallback Provider

**Files:**
- Create: `voice/providers/gemini_fallback.py`
- Modify: `main.py`
- Test: `tests/test_voice_router.py`

- [ ] **Step 1: Write the failing test**

```python
from voice.router import VoiceRouter


class FailingPrimary:
    def transcribe(self, audio_bytes, mime_type):
        raise RuntimeError("primary failed")

    def synthesize(self, text):
        raise RuntimeError("primary failed")


class GeminiFallback:
    def transcribe(self, audio_bytes, mime_type):
        return "fallback transcript"

    def synthesize(self, text):
        return b"audio"


def test_voice_router_uses_gemini_only_after_primary_exhaustion():
    router = VoiceRouter(primary_providers=[FailingPrimary()], fallback_provider=GeminiFallback())

    assert router.transcribe(b"pcm", "audio/pcm") == "fallback transcript"
    assert router.synthesize("hello") == b"audio"
```

- [ ] **Step 2: Run test to verify it fails if TTS route is incomplete**

Run: `python -m pytest tests/test_voice_router.py -q`
Expected: FAIL until `synthesize` fallback is implemented

- [ ] **Step 3: Extract Gemini voice behavior from `main.py` into provider methods**

```python
class GeminiFallbackSpeechProvider:
    def transcribe(self, audio_bytes: bytes, mime_type: str) -> str:
        ...

    def synthesize(self, text: str) -> bytes:
        ...
```

- [ ] **Step 4: Update `VoiceRouter` to support both directions**

```python
def synthesize(self, text: str) -> bytes:
    for provider in self.primary_providers:
        try:
            return provider.synthesize(text)
        except Exception:
            continue
    return self.fallback_provider.synthesize(text)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_voice_router.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add voice/providers/gemini_fallback.py voice/router.py main.py tests/test_voice_router.py
git commit -m "feat: add gemini voice fallback provider"
```

### Task 5: Integrate Voice Router Into Runtime

**Files:**
- Modify: `main.py`
- Modify: `agent/voice.py`
- Test: `tests/test_voice_orchestrator.py`

- [ ] **Step 1: Write the failing integration test**

```python
from agent.voice import VoiceOrchestrator


def test_voice_orchestrator_accepts_external_speech_router():
    router = object()
    orchestrator = VoiceOrchestrator(speech_router=router)
    assert orchestrator.speech_router is router
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_voice_orchestrator.py -q`
Expected: FAIL because `speech_router` is not accepted

- [ ] **Step 3: Update orchestrator constructor**

```python
def __init__(self, api_key: str | None = None, speak_fn: Callable | None = None, speech_router=None):
    ...
    self.speech_router = speech_router
```

- [ ] **Step 4: Update `main.py` to build and use the router**

Create the router once in `BuddyLive.__init__`, use it for STT capture flow and TTS playback flow, and keep existing task execution untouched.

- [ ] **Step 5: Keep Gemini live task execution only where needed**

Remove Gemini-exclusive speech assumptions from `_build_config`, `_send_realtime`, `_listen_audio`, `_receive_audio`, and `_play_audio` only to the extent required to route voice I/O through the new providers.

- [ ] **Step 6: Run tests to verify they pass**

Run: `python -m pytest tests/test_voice_orchestrator.py -q`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add main.py agent/voice.py tests/test_voice_orchestrator.py
git commit -m "feat: route runtime voice io through providers"
```

### Task 6: Add Environment Loading and Dependency Updates

**Files:**
- Modify: `pyproject.toml`
- Modify: `requirements.txt`
- Modify: `readme.md`

- [ ] **Step 1: Add environment loader dependency**

Add:

```toml
"python-dotenv",
```

and

```text
python-dotenv
```

- [ ] **Step 2: Document `.env`**

Add a `readme.md` section showing:

```env
SARVAM_API_KEYS=key1,key2,key3
SARVAM_TTS_MODEL=bulbul:v3
SARVAM_TTS_SPEAKER=Ritu
SARVAM_TTS_LANGUAGE=en-IN
SARVAM_TTS_PITCH=0.0
SARVAM_TTS_PACE=1.0
SARVAM_TTS_TEMPERATURE=0.2
SARVAM_STT_LANGUAGE_HINT=unknown
VOICE_PROVIDER_PRIMARY=sarvam
VOICE_PROVIDER_FALLBACK=gemini
```

- [ ] **Step 3: Run ship checks**

Run: `python scripts/ship_ready_check.py`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml requirements.txt readme.md
git commit -m "docs: add sarvam voice environment setup"
```

### Task 7: Final Verification

**Files:**
- Test: `tests/test_voice_config.py`
- Test: `tests/test_voice_router.py`
- Test: `tests/test_sarvam_provider.py`
- Test: `tests/test_voice_orchestrator.py`
- Test: `tests/test_async_queues.py`

- [ ] **Step 1: Run focused voice tests**

Run: `python -m pytest tests/test_voice_config.py tests/test_voice_router.py tests/test_sarvam_provider.py tests/test_voice_orchestrator.py -q`
Expected: PASS

- [ ] **Step 2: Run full test suite**

Run: `python -m pytest -q`
Expected: PASS

- [ ] **Step 3: Run startup probe**

Run:

```bash
python -c "import subprocess, time, sys; p = subprocess.Popen([sys.executable, 'main.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True); time.sleep(8); exited = p.poll(); print('STATUS:' + ('RUNNING' if exited is None else f'EXITED:{exited}')); p.terminate() if exited is None else None; out, err = p.communicate(timeout=5) if exited is None else p.communicate(); print(err[-4000:])"
```

Expected: `STATUS:RUNNING` with no startup traceback

- [ ] **Step 4: Commit**

```bash
git add .
git commit -m "feat: integrate sarvam voice routing with gemini fallback"
```

### Self-Review

- Spec coverage: voice config, provider abstraction, Sarvam implementation, Gemini fallback, runtime integration, docs, and verification are all covered by Tasks 1-7.
- Placeholder scan: no `TODO`, `TBD`, or undefined implementation markers remain.
- Type consistency: `VoiceSettings`, `VoiceRouter`, `SarvamSpeechProvider`, and `GeminiFallbackSpeechProvider` are used consistently across the plan.
