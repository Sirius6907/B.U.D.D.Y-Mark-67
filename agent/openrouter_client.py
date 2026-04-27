"""
agent/openrouter_client.py — OpenRouter Fallback Client
========================================================
Provides an OpenAI-compatible HTTP client for OpenRouter's free models.
Uses httpx for async-friendly requests with proper headers.

Preferred chain:
  1. google/gemini-2.5-flash:free
  2. google/gemma-4-31b-it:free
  3. deepseek/deepseek-r1:free
  4. openrouter/free
"""
from __future__ import annotations

import json
import os
import time
import threading
from dataclasses import dataclass
from typing import Optional

from buddy_logging import get_logger

logger = get_logger("agent.openrouter_client")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

# Free model fallback chain (ordered by preference)
FREE_MODELS = [
    "openrouter/free",
    "google/gemma-4-31b-it:free",
    "google/gemini-2.5-flash:free",
    "deepseek/deepseek-r1:free",
]


@dataclass(slots=True)
class OpenRouterResponse:
    """Normalized response from OpenRouter."""
    text: str
    model_used: str
    latency_ms: float
    tokens_used: int = 0


class OpenRouterKeyRotator:
    """Thread-safe round-robin rotator for OpenRouter API keys."""

    def __init__(self, keys_str: str):
        self._keys = [k.strip() for k in keys_str.split(",") if k.strip()]
        self._index = 0
        self._lock = threading.Lock()

    def set_keys(self, keys_str: str) -> None:
        with self._lock:
            clean_keys = [k.strip() for k in keys_str.split(",") if k.strip()]
            if clean_keys != self._keys:
                self._keys = clean_keys
                self._index = 0

    def get_next_key(self) -> str | None:
        with self._lock:
            if not self._keys:
                return None
            key = self._keys[self._index]
            self._index = (self._index + 1) % len(self._keys)
            return key


class OpenRouterClient:
    """
    Stateless HTTP client for OpenRouter's free-tier models.
    Falls through the FREE_MODELS chain on failure.
    
    Thread-safe: uses a module-level session lock for lazy init.
    """

    def __init__(self, api_key: str | None = None):
        keys_str = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        self._rotator = OpenRouterKeyRotator(keys_str)
        self._session = None
        self._session_lock = threading.Lock()

    @property
    def is_configured(self) -> bool:
        return bool(self._rotator._keys)

    def set_api_key(self, key: str) -> None:
        self._rotator.set_keys(key)

    def _get_session(self):
        """Lazy-init httpx client (import-time safe)."""
        if self._session is None:
            with self._session_lock:
                if self._session is None:
                    import httpx
                    self._session = httpx.Client(
                        timeout=120.0,
                        headers={
                            "HTTP-Referer": "https://buddy-mk67.local",
                            "X-Title": "BUDDY MARK LXVII",
                            "Content-Type": "application/json",
                        },
                    )
        return self._session

    def generate(
        self,
        prompt: str,
        system: str = "",
        model: str | None = None,
        max_tokens: int = 4096,
    ) -> OpenRouterResponse:
        """
        Generate a completion using OpenRouter.
        If `model` is None, tries the full FREE_MODELS chain.
        """
        if not self.is_configured:
            raise RuntimeError(
                "OpenRouter API key not configured. "
                "Set OPENROUTER_API_KEY in .env or environment (comma-separated for rotation)."
            )

        models_to_try = [model] if model else list(FREE_MODELS)
        last_error: Exception | None = None

        for m in models_to_try:
            try:
                return self._call(m, prompt, system, max_tokens)
            except Exception as exc:
                logger.warning(
                    "OpenRouter model %s failed: %s — trying next...", m, exc
                )
                last_error = exc

        raise RuntimeError(
            f"All OpenRouter models failed. Last error: {last_error}"
        )

    def _call(
        self,
        model: str,
        prompt: str,
        system: str,
        max_tokens: int,
    ) -> OpenRouterResponse:
        """Make a single API call to OpenRouter."""
        session = self._get_session()
        key = self._rotator.get_next_key()
        if not key:
            raise RuntimeError("No OpenRouter API keys configured.")

        headers = {"Authorization": f"Bearer {key}"}

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
        }

        start = time.time()
        logger.info("Calling OpenRouter: %s ...", model)

        response = session.post(OPENROUTER_BASE_URL, json=payload, headers=headers)

        if response.status_code == 429:
            raise RuntimeError(f"OpenRouter rate limit (429) on {model}")

        if response.status_code != 200:
            body = response.text[:300]
            raise RuntimeError(
                f"OpenRouter HTTP {response.status_code} on {model}: {body}"
            )

        data = response.json()
        elapsed_ms = (time.time() - start) * 1000

        # Extract text from OpenAI-compatible response
        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError(f"OpenRouter returned empty choices for {model}")

        text = _extract_message_content(choices[0].get("message", {}).get("content", ""))
        if not text:
            raise RuntimeError(f"OpenRouter returned empty content for {model}")

        usage = data.get("usage", {})
        tokens = usage.get("total_tokens", 0)
        actual_model = data.get("model", model)

        logger.info(
            "OpenRouter %s responded in %.0fms (%d tokens)",
            actual_model, elapsed_ms, tokens,
        )

        return OpenRouterResponse(
            text=text,
            model_used=actual_model,
            latency_ms=elapsed_ms,
            tokens_used=tokens,
        )

    def close(self) -> None:
        """Close the HTTP session."""
        if self._session is not None:
            try:
                self._session.close()
            except Exception:
                pass
            self._session = None


# ── Singleton ─────────────────────────────────────────────────────────────────
_client: OpenRouterClient | None = None
_client_lock = threading.Lock()


def get_openrouter_client() -> OpenRouterClient:
    """Get or create the singleton OpenRouter client."""
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                from config.runtime import load_env_file, ENV_FILE
                env = load_env_file(ENV_FILE)
                api_key = os.environ.get(
                    "OPENROUTER_API_KEY",
                    env.get("OPENROUTER_API_KEY", ""),
                )
                _client = OpenRouterClient(api_key=api_key)
    return _client


def _extract_message_content(content) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                cleaned = item.strip()
                if cleaned:
                    parts.append(cleaned)
            elif isinstance(item, dict):
                text_value = item.get("text")
                if isinstance(text_value, str):
                    cleaned = text_value.strip()
                    if cleaned:
                        parts.append(cleaned)
        return "\n".join(parts).strip()
    return ""
