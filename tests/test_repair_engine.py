from agent.repair_engine import RepairEngine


def test_repair_engine_uses_locator_chain_in_order():
    calls = []

    engine = RepairEngine(
        exact_locator=lambda error, context: None,
        landmark_matcher=lambda error, context: calls.append("landmark") or None,
        ocr_search=lambda error, context: calls.append("ocr") or {"action": "screen_click", "target": "send"},
        semantic_guesser=lambda error, context: calls.append("semantic") or None,
        replanner=lambda error, context: calls.append("replan") or {"action": "replan"},
    )

    repair = engine.repair("button not found", {"semantic_selectors": ["send"]})

    assert repair["strategy"] == "ocr_text_search"
    assert calls == ["landmark", "ocr"]
