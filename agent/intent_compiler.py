from __future__ import annotations

import re
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CommandShape(str, Enum):
    SINGLE_ACTION = "single_action"
    COMPOUND_ACTION = "compound_action"
    STATE_QUESTION = "state_question"
    HISTORY_QUESTION = "history_question"
    CAREER_WORKFLOW = "career_workflow"
    AMBIGUOUS = "ambiguous"


@dataclass
class CompiledCommand:
    original_text: str
    normalized_text: str
    confidence: float = 1.0
    split_reason: str = "single"
    duplicate_suppressed: bool = False
    ambiguity_markers: list[str] = field(default_factory=list)
    extracted_entities: dict[str, Any] = field(default_factory=dict)
    shape: CommandShape = CommandShape.SINGLE_ACTION


class IntentCompiler:
    _TYPO_MAP = {
        "opn": "open",
        "youutbe": "youtube",
        "youtbe": "youtube",
        "chrme": "chrome",
        "whhatsapp": "whatsapp",
        "whhats": "whats",
        "messsged": "messaged",
    }
    _SPLIT_PATTERNS = (
        " and then ",
        " then ",
        " after that ",
        " also ",
        " and ",
    )
    _STATE_MARKERS = ("what is on my screen", "who messaged me", "what apps are", "what video is playing")
    _HISTORY_MARKERS = ("last time", "history", "previously", "last video")
    _CAREER_MARKERS = ("job", "linkedin", "github", "resume", "cover letter", "referral", "application")
    _AMBIGUOUS_MARKERS = ("show the last", "apply there", "update it")

    def __init__(self) -> None:
        self._recent_commands: deque[tuple[str, float]] = deque(maxlen=5)

    def compile(self, raw_text: str) -> list[CompiledCommand]:
        normalized = self._normalize_whitespace(self._fix_typos(raw_text))
        parts = self._split_compound(normalized)
        compiled: list[CompiledCommand] = []
        split_reason = "compound" if len(parts) > 1 else "single"
        for part in parts:
            deduped = self._deduplicate(part)
            if deduped is None:
                continue
            compiled.append(
                CompiledCommand(
                    original_text=raw_text,
                    normalized_text=deduped,
                    confidence=0.95 if deduped != raw_text else 1.0,
                    split_reason=split_reason,
                    ambiguity_markers=self._ambiguity_markers(deduped),
                    extracted_entities=self._extract_entities(deduped),
                    shape=self._shape_for(deduped, len(parts)),
                )
            )
        return compiled

    def _fix_typos(self, text: str) -> str:
        tokens = text.split()
        corrected = [self._TYPO_MAP.get(token.lower(), token) for token in tokens]
        return " ".join(corrected)

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        text = re.sub(r"[!?.,;:]+$", "", text.strip())
        text = re.sub(r"\s+", " ", text)
        return text

    def _split_compound(self, text: str) -> list[str]:
        quoted_segments: dict[str, str] = {}

        def _stash(match: re.Match[str]) -> str:
            key = f"__QUOTE_{len(quoted_segments)}__"
            quoted_segments[key] = match.group(0)
            return key

        protected = re.sub(r'"[^"]+"', _stash, text)
        pattern = "|".join(re.escape(marker.strip()) for marker in self._SPLIT_PATTERNS)
        parts = [segment.strip() for segment in re.split(rf"\s(?:{pattern})\s", protected) if segment.strip()]
        if not parts:
            parts = [protected]
        return [self._restore_quotes(part, quoted_segments) for part in parts]

    @staticmethod
    def _restore_quotes(text: str, quoted_segments: dict[str, str]) -> str:
        for key, value in quoted_segments.items():
            text = text.replace(key, value)
        return text

    def _deduplicate(self, text: str) -> str | None:
        canonical = re.sub(r"[\W_]+", " ", text.lower()).strip()
        now = time.time()
        for previous, ts in self._recent_commands:
            if previous == canonical and now - ts <= 3:
                return None
        self._recent_commands.append((canonical, now))
        return text

    def _shape_for(self, text: str, part_count: int) -> CommandShape:
        lowered = text.lower()
        if any(marker in lowered for marker in self._CAREER_MARKERS):
            return CommandShape.CAREER_WORKFLOW
        if any(marker in lowered for marker in self._STATE_MARKERS):
            return CommandShape.STATE_QUESTION
        if any(marker in lowered for marker in self._HISTORY_MARKERS):
            return CommandShape.HISTORY_QUESTION
        if self._ambiguity_markers(text):
            return CommandShape.AMBIGUOUS
        if part_count > 1:
            return CommandShape.SINGLE_ACTION
        return CommandShape.SINGLE_ACTION

    def _ambiguity_markers(self, text: str) -> list[str]:
        lowered = text.lower()
        return [marker for marker in self._AMBIGUOUS_MARKERS if marker in lowered]

    @staticmethod
    def _extract_entities(text: str) -> dict[str, Any]:
        lowered = text.lower()
        entities: dict[str, Any] = {}
        if "youtube" in lowered:
            entities["platform"] = "youtube"
        if "whatsapp" in lowered:
            entities["platform"] = "whatsapp"
        if "chrome" in lowered:
            entities["browser"] = "chrome"
        return entities
