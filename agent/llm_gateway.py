"""
agent/llm_gateway.py - Unified LLM Gateway with Fallback Chain
================================================================
Central entry point for ALL LLM calls in the BUDDY system.
Implements the preferred fallback strategy:

  Tier 0: OpenRouter preferred chain
  Tier 1: gemini-2.5-flash (Google direct API fallback)

Every module (kernel, planner, executor, voice, error_handler) should
call `llm_generate()` instead of hitting the Gemini SDK directly.
"""
from __future__ import annotations

import json
import re
import threading
import time
from dataclasses import dataclass

from buddy_logging import get_logger

logger = get_logger("agent.llm_gateway")


@dataclass(slots=True)
class LLMResponse:
    """Normalized response from any model tier."""

    text: str
    model: str
    tier: int  # 0=OpenRouter preferred, 1=Gemini fallback
    latency_ms: float
    fallback_used: bool  # True if we had to fall back from the preferred backend


_gemini_circuit_open = False
_gemini_circuit_until = 0.0
_circuit_lock = threading.Lock()
CIRCUIT_COOLDOWN_SECS = 60


def _open_gemini_circuit() -> None:
    """Mark Gemini as rate-limited for CIRCUIT_COOLDOWN_SECS seconds."""
    global _gemini_circuit_open, _gemini_circuit_until
    with _circuit_lock:
        _gemini_circuit_open = True
        _gemini_circuit_until = time.time() + CIRCUIT_COOLDOWN_SECS
        logger.warning("Gemini circuit OPEN - skipping for %ds", CIRCUIT_COOLDOWN_SECS)


def _is_gemini_available() -> bool:
    """Check whether we should attempt Gemini."""
    global _gemini_circuit_open
    if not _gemini_circuit_open:
        return True
    with _circuit_lock:
        if time.time() >= _gemini_circuit_until:
            _gemini_circuit_open = False
            logger.info("Gemini circuit CLOSED - retrying fallback model")
            return True
        return False


def _try_gemini(
    prompt: str,
    system: str,
    model: str,
    max_tokens: int,
) -> LLMResponse:
    """Attempt a Gemini API call. Raises on any error."""
    from google import genai
    from google.genai import types
    from config.runtime import get_api_key

    client = genai.Client(api_key=get_api_key(required=True))

    config_kwargs = {}
    if system:
        config_kwargs["system_instruction"] = system
    if max_tokens:
        config_kwargs["max_output_tokens"] = max_tokens

    start = time.time()
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(**config_kwargs) if config_kwargs else None,
    )
    elapsed_ms = (time.time() - start) * 1000

    text = (response.text or "").strip()
    if not text:
        raise RuntimeError("Gemini returned empty response")

    return LLMResponse(
        text=text,
        model=model,
        tier=1,
        latency_ms=elapsed_ms,
        fallback_used=True,
    )


def _try_openrouter(prompt: str, system: str, max_tokens: int) -> LLMResponse:
    """Attempt OpenRouter preferred chain. Raises if all models fail."""
    from agent.openrouter_client import get_openrouter_client

    client = get_openrouter_client()
    result = client.generate(
        prompt=prompt,
        system=system,
        max_tokens=max_tokens,
    )

    return LLMResponse(
        text=result.text,
        model=result.model_used,
        tier=0,
        latency_ms=result.latency_ms,
        fallback_used=False,
    )


def llm_generate(
    prompt: str,
    system: str = "",
    gemini_model: str = "gemini-2.5-flash",
    max_tokens: int = 4096,
    skip_gemini: bool = False,
) -> LLMResponse:
    """
    Central LLM call with automatic fallback.

    Args:
        prompt: The user/task prompt.
        system: System instruction (optional).
        gemini_model: Which Gemini model to use as fallback.
        max_tokens: Max output tokens.
        skip_gemini: Disable the Gemini fallback.
    """
    try:
        result = _try_openrouter(prompt, system, max_tokens)
        logger.info(
            "Preferred backend succeeded: %s (tier %d, %.0fms)",
            result.model,
            result.tier,
            result.latency_ms,
        )
        return result
    except Exception as exc:
        logger.warning("OpenRouter preferred chain failed: %s", exc)

    if not skip_gemini and _is_gemini_available():
        try:
            return _try_gemini(prompt, system, gemini_model, max_tokens)
        except Exception as exc:
            error_str = str(exc).lower()
            is_rate_limit = (
                "429" in error_str
                or "rate" in error_str
                or "quota" in error_str
                or "resource exhausted" in error_str
                or "resourceexhausted" in error_str
            )
            if is_rate_limit:
                _open_gemini_circuit()
                logger.warning("Gemini fallback rate-limited after OpenRouter failure")
            else:
                logger.warning("Gemini fallback error: %s", exc)

    raise RuntimeError("LLM gateway exhausted OpenRouter preferred path and Gemini fallback.")


def llm_generate_json(
    prompt: str,
    system: str = "",
    gemini_model: str = "gemini-2.5-flash",
    max_tokens: int = 4096,
) -> dict:
    """Generate and parse a JSON response from any model tier."""
    resp = llm_generate(prompt, system, gemini_model, max_tokens)
    text = re.sub(r"```(?:json)?", "", resp.text).strip().rstrip("`").strip()
    return json.loads(text)
