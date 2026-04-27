"""
core/memory/context_manager.py — Deterministic Context Window Packer
=====================================================================
Inspired by OpenClaw's context-engine/registry.ts pattern of deterministic
context assembly. This module replaces ad-hoc prompt building with a
priority-ranked, budget-aware context window system.

Architecture:
    ContextSlot     — A named, prioritized block of context text
    ContextWindow   — Ordered assembly of slots within a token budget
    ContextManager  — Singleton that ingests, ranks, and packs context

Design Principles (from OpenClaw reverse-engineering):
    1. Deterministic ordering — slots are packed by priority, not insertion order.
    2. Budget-aware — total context is capped to avoid overflowing the model window.
    3. Freshness decay — older context is weighted lower than recent context.
    4. Category isolation — system prompt, memory, history, RAG are separate slots.
"""
from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional

from buddy_logging import get_logger

logger = get_logger("core.memory.context")


# ── Priority Levels ───────────────────────────────────────────────────────────

class SlotPriority(IntEnum):
    """Higher value = packed first (closer to system instruction)."""
    SYSTEM_PROMPT = 100      # Core identity & behavior rules
    TIME_CONTEXT = 90        # Current date/time
    LONG_TERM_MEMORY = 80    # Persistent user facts
    RAG_CONTEXT = 70         # Semantically retrieved documents
    CONVERSATION_HISTORY = 60  # Rolling session history
    TASK_CONTEXT = 50        # Current task plan / active execution state
    EPISODIC_MEMORY = 40     # Past task episodes
    SUPPLEMENTARY = 20       # Low-priority extras


# ── Data Models ───────────────────────────────────────────────────────────────

@dataclass(slots=True)
class ContextSlot:
    """A single block of context with priority and metadata."""
    name: str
    content: str
    priority: SlotPriority
    char_count: int = 0
    created_at: float = field(default_factory=time.time)
    ttl_seconds: float = 0.0  # 0 = never expires
    compressible: bool = True  # Can be truncated if budget is tight

    def __post_init__(self):
        self.char_count = len(self.content)

    @property
    def is_expired(self) -> bool:
        if self.ttl_seconds <= 0:
            return False
        return (time.time() - self.created_at) > self.ttl_seconds

    @property
    def freshness_score(self) -> float:
        """Returns 1.0 for brand-new, decays toward 0.0 over time."""
        age = time.time() - self.created_at
        # Decay over 1 hour — older context gets lower weight
        return max(0.0, 1.0 - (age / 3600.0))


@dataclass
class ContextWindow:
    """Assembled context ready for prompt injection."""
    system_instruction: str
    total_chars: int
    slot_count: int
    slots_included: list[str]  # names of slots that made it in
    slots_dropped: list[str]   # names of slots that were cut for budget
    assembled_at: float = field(default_factory=time.time)


# ── Context Manager ──────────────────────────────────────────────────────────

class ContextManager:
    """
    Deterministic context window assembler.

    Usage:
        ctx = ContextManager(max_chars=8000)
        ctx.upsert("system_prompt", prompt_text, SlotPriority.SYSTEM_PROMPT)
        ctx.upsert("memory", memory_text, SlotPriority.LONG_TERM_MEMORY)
        ctx.upsert("history", history_text, SlotPriority.CONVERSATION_HISTORY)

        window = ctx.assemble()
        # window.system_instruction is the packed prompt
    """

    # 8000 chars ≈ 2000 tokens, safe for Gemini context window
    DEFAULT_MAX_CHARS = 12000

    def __init__(self, max_chars: int = DEFAULT_MAX_CHARS):
        self._slots: dict[str, ContextSlot] = {}
        self._max_chars = max_chars
        self._lock = threading.Lock()
        self._assembly_count = 0

    # ── Slot Management ───────────────────────────────────────────────────

    def upsert(
        self,
        name: str,
        content: str,
        priority: SlotPriority,
        ttl_seconds: float = 0.0,
        compressible: bool = True,
    ) -> None:
        """Insert or update a context slot."""
        if not content or not content.strip():
            # Remove empty slots
            with self._lock:
                self._slots.pop(name, None)
            return

        slot = ContextSlot(
            name=name,
            content=content.strip(),
            priority=priority,
            ttl_seconds=ttl_seconds,
            compressible=compressible,
        )
        with self._lock:
            self._slots[name] = slot

        logger.debug(
            "Context slot upserted: %s (priority=%d, chars=%d)",
            name, priority, slot.char_count,
        )

    def remove(self, name: str) -> bool:
        """Remove a context slot by name."""
        with self._lock:
            removed = self._slots.pop(name, None)
        return removed is not None

    def clear(self) -> None:
        """Remove all context slots."""
        with self._lock:
            self._slots.clear()

    # ── Assembly ──────────────────────────────────────────────────────────

    def assemble(self) -> ContextWindow:
        """
        Pack all active slots into a single system instruction string.

        Strategy (inspired by OpenClaw's deterministic assembly):
        1. Evict expired slots.
        2. Sort by priority (descending), then freshness.
        3. Pack greedily until budget is exhausted.
        4. Truncate the last slot if it overflows (only if compressible).
        """
        with self._lock:
            # Step 1: Evict expired
            expired = [n for n, s in self._slots.items() if s.is_expired]
            for name in expired:
                del self._slots[name]
                logger.debug("Evicted expired slot: %s", name)

            # Step 2: Sort by (priority DESC, freshness DESC)
            sorted_slots = sorted(
                self._slots.values(),
                key=lambda s: (s.priority, s.freshness_score),
                reverse=True,
            )

        # Step 3: Greedy packing
        packed_parts: list[str] = []
        included: list[str] = []
        dropped: list[str] = []
        budget = self._max_chars

        for slot in sorted_slots:
            if budget <= 0:
                dropped.append(slot.name)
                continue

            if slot.char_count <= budget:
                packed_parts.append(slot.content)
                included.append(slot.name)
                budget -= slot.char_count
            elif slot.compressible:
                # Truncate to fit remaining budget
                truncated = slot.content[:budget - 3] + "…"
                packed_parts.append(truncated)
                included.append(f"{slot.name}(truncated)")
                budget = 0
            else:
                # Non-compressible slot that doesn't fit — drop it
                dropped.append(slot.name)

        system_instruction = "\n\n".join(packed_parts)
        self._assembly_count += 1

        window = ContextWindow(
            system_instruction=system_instruction,
            total_chars=len(system_instruction),
            slot_count=len(included),
            slots_included=included,
            slots_dropped=dropped,
        )

        logger.info(
            "Context assembled (#%d): %d chars, %d slots in, %d dropped",
            self._assembly_count,
            window.total_chars,
            window.slot_count,
            len(dropped),
        )

        return window

    # ── Introspection ─────────────────────────────────────────────────────

    def get_slot_names(self) -> list[str]:
        """Return names of all active slots."""
        with self._lock:
            return list(self._slots.keys())

    def get_slot(self, name: str) -> Optional[ContextSlot]:
        """Return a specific slot by name."""
        with self._lock:
            return self._slots.get(name)

    def get_stats(self) -> dict:
        """Return stats about the context manager state."""
        with self._lock:
            total_chars = sum(s.char_count for s in self._slots.values())
            return {
                "slot_count": len(self._slots),
                "total_chars": total_chars,
                "max_chars": self._max_chars,
                "utilization": total_chars / self._max_chars if self._max_chars else 0,
                "assembly_count": self._assembly_count,
                "slots": {
                    name: {
                        "priority": s.priority.name,
                        "chars": s.char_count,
                        "freshness": round(s.freshness_score, 2),
                    }
                    for name, s in self._slots.items()
                },
            }

    def __repr__(self) -> str:
        return f"<ContextManager slots={len(self._slots)} budget={self._max_chars}>"
