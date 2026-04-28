from __future__ import annotations

from typing import Any, Callable


RepairHandler = Callable[[str, dict[str, Any]], dict[str, Any] | None]


class RepairEngine:
    def __init__(
        self,
        *,
        exact_locator: RepairHandler | None = None,
        landmark_matcher: RepairHandler | None = None,
        ocr_search: RepairHandler | None = None,
        semantic_guesser: RepairHandler | None = None,
        replanner: RepairHandler | None = None,
    ):
        self.exact_locator = exact_locator or (lambda error, context: None)
        self.landmark_matcher = landmark_matcher or (lambda error, context: None)
        self.ocr_search = ocr_search or (lambda error, context: None)
        self.semantic_guesser = semantic_guesser or (lambda error, context: None)
        self.replanner = replanner or (lambda error, context: {"action": "replan", "error": error})

    def repair(self, error: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = context or {}
        chain = (
            ("exact_locator", self.exact_locator),
            ("landmark_match", self.landmark_matcher),
            ("ocr_text_search", self.ocr_search),
            ("semantic_ui_guess", self.semantic_guesser),
            ("replan", self.replanner),
        )
        for strategy, handler in chain:
            repair = handler(error, context)
            if repair:
                return {"strategy": strategy, **repair}
        return {"strategy": "replan", "action": "replan", "error": error}
