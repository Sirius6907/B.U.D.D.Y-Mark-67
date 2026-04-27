from types import SimpleNamespace

from agent import llm_gateway


def test_llm_generate_prefers_openrouter_first(monkeypatch):
    monkeypatch.setattr(
        llm_gateway,
        "_try_openrouter",
        lambda prompt, system, max_tokens: llm_gateway.LLMResponse(
            text="openrouter ok",
            model="google/gemini-2.5-flash:free",
            tier=0,
            latency_ms=10,
            fallback_used=False,
        ),
    )

    def fail_gemini(*args, **kwargs):
        raise AssertionError("Gemini should not be called when OpenRouter succeeds")

    monkeypatch.setattr(llm_gateway, "_try_gemini", fail_gemini)

    result = llm_gateway.llm_generate("hello")
    assert result.text == "openrouter ok"
    assert result.tier == 0
    assert result.fallback_used is False


def test_llm_generate_falls_back_to_gemini_when_openrouter_fails(monkeypatch):
    monkeypatch.setattr(llm_gateway, "_try_openrouter", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("openrouter failed")))
    monkeypatch.setattr(llm_gateway, "_is_gemini_available", lambda: True)
    monkeypatch.setattr(
        llm_gateway,
        "_try_gemini",
        lambda prompt, system, model, max_tokens: llm_gateway.LLMResponse(
            text="gemini ok",
            model=model,
            tier=1,
            latency_ms=20,
            fallback_used=True,
        ),
    )

    result = llm_gateway.llm_generate("hello")
    assert result.text == "gemini ok"
    assert result.tier == 1
    assert result.fallback_used is True
