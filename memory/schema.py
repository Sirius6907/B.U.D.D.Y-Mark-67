"""
memory/schema.py — Tiered Memory Schema
========================================
Defines memory tiers, sensitivity levels, promotion rules,
and structured memory records for the B.U.D.D.Y memory system.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


# ── Memory Tier ──────────────────────────────────────────
class MemoryTier(str, Enum):
    """
    Four-tier memory hierarchy.

    SESSION    – In-memory only, dies when the process exits.
    PREFERENCE – Habitual patterns, auto-promoted after N confirmations.
    LONG_TERM  – Identity facts, career data, relationships.
    EPHEMERAL  – Secrets/tokens, auto-expire, never written to disk.
    """
    SESSION    = "session"
    PREFERENCE = "preference"
    LONG_TERM  = "long_term"
    EPHEMERAL  = "ephemeral"


# ── Sensitivity ──────────────────────────────────────────
class MemorySensitivity(str, Enum):
    NORMAL    = "normal"
    SENSITIVE = "sensitive"
    SECRET    = "secret"       # never logged, never persisted, redacted in prompts


# ── Existing memory type enum (backward compat) ─────────
class MemoryType(str, Enum):
    SEMANTIC    = "semantic"
    EPISODIC    = "episodic"
    WORKFLOW    = "workflow"
    ENVIRONMENT = "environment"


# ── Promotion Rule ───────────────────────────────────────
class PromotionRule(BaseModel):
    """Rule for auto-promoting a memory entry to a higher tier."""
    from_tier: MemoryTier
    to_tier: MemoryTier
    min_confirmations: int = 3
    min_age_hours: float = 24.0
    requires_categories: List[str] = Field(default_factory=list)


# ── Default Promotion Rules ─────────────────────────────
DEFAULT_PROMOTION_RULES: list[PromotionRule] = [
    PromotionRule(
        from_tier=MemoryTier.SESSION,
        to_tier=MemoryTier.PREFERENCE,
        min_confirmations=2,
        min_age_hours=1.0,
    ),
    PromotionRule(
        from_tier=MemoryTier.PREFERENCE,
        to_tier=MemoryTier.LONG_TERM,
        min_confirmations=3,
        min_age_hours=24.0,
        requires_categories=["identity", "preferences", "projects", "relationships"],
    ),
]


# ── Structured Memory Entry ─────────────────────────────
class MemoryEntry(BaseModel):
    """A single structured fact in memory."""
    category: str
    key: str
    value: str
    updated: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    tier: MemoryTier = MemoryTier.LONG_TERM
    sensitivity: MemorySensitivity = MemorySensitivity.NORMAL
    times_confirmed: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


# ── Full Memory Record (for advanced queries) ───────────
class MemoryRecord(BaseModel):
    memory_type: MemoryType
    category: str
    key: str
    value: str
    source: str
    confidence: float
    sensitivity: MemorySensitivity = MemorySensitivity.NORMAL
    tier: MemoryTier = MemoryTier.LONG_TERM
    last_used: Optional[str] = None
    times_confirmed: int = 0
    decay_score: float = 0.0


# ── Task Episode ────────────────────────────────────────
class TaskEpisode(BaseModel):
    """Episodic memory of a completed task plan."""
    plan_id: str
    goal: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    success: bool
    nodes_summary: List[Dict[str, Any]]  # Simplified summary of what happened
    final_observation: Optional[str] = None
    learned_lesson: Optional[str] = None


# ── Tier helpers ─────────────────────────────────────────
PERSIST_TIERS = {MemoryTier.PREFERENCE, MemoryTier.LONG_TERM}
"""Tiers that are written to SQLite/ChromaDB."""

PROFILE_TIERS = {MemoryTier.PREFERENCE, MemoryTier.LONG_TERM}
"""Tiers that are written to the user.md profile."""

NEVER_PERSIST_TIERS = {MemoryTier.SESSION, MemoryTier.EPHEMERAL}
"""Tiers that must never touch disk."""

SECRET_SENSITIVITY = MemorySensitivity.SECRET
"""Shortcut for SECRET sensitivity checks."""
