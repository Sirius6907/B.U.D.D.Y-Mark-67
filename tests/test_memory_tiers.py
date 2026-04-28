"""Tests for tiered memory: session, ephemeral, promotion, and SECRET blocking."""
import time
import pytest
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from memory.schema import (
    MemoryTier, MemorySensitivity, PromotionRule,
    PERSIST_TIERS, PROFILE_TIERS, NEVER_PERSIST_TIERS,
    SECRET_SENSITIVITY, DEFAULT_PROMOTION_RULES,
)
from memory.memory_manager import SessionMemory, EphemeralStore


# ── Schema enum tests ────────────────────────────────────
class TestMemoryTierEnum:
    def test_tier_values(self):
        assert MemoryTier.SESSION.value == "session"
        assert MemoryTier.PREFERENCE.value == "preference"
        assert MemoryTier.LONG_TERM.value == "long_term"
        assert MemoryTier.EPHEMERAL.value == "ephemeral"

    def test_sensitivity_values(self):
        assert MemorySensitivity.NORMAL.value == "normal"
        assert MemorySensitivity.SENSITIVE.value == "sensitive"
        assert MemorySensitivity.SECRET.value == "secret"

    def test_persist_tiers(self):
        assert MemoryTier.PREFERENCE in PERSIST_TIERS
        assert MemoryTier.LONG_TERM in PERSIST_TIERS
        assert MemoryTier.SESSION not in PERSIST_TIERS
        assert MemoryTier.EPHEMERAL not in PERSIST_TIERS

    def test_profile_tiers(self):
        assert MemoryTier.PREFERENCE in PROFILE_TIERS
        assert MemoryTier.LONG_TERM in PROFILE_TIERS
        assert MemoryTier.SESSION not in PROFILE_TIERS

    def test_never_persist_tiers(self):
        assert MemoryTier.SESSION in NEVER_PERSIST_TIERS
        assert MemoryTier.EPHEMERAL in NEVER_PERSIST_TIERS

    def test_secret_sensitivity_constant(self):
        assert SECRET_SENSITIVITY == MemorySensitivity.SECRET


# ── SessionMemory tests ──────────────────────────────────
class TestSessionMemory:
    def test_set_and_get(self):
        sm = SessionMemory()
        sm.set("identity", "name", "Alice")
        assert sm.get("identity", "name") == "Alice"

    def test_get_missing(self):
        sm = SessionMemory()
        assert sm.get("identity", "nonexistent") is None

    def test_get_all(self):
        sm = SessionMemory()
        sm.set("identity", "name", "Alice")
        sm.set("preferences", "theme", "dark")
        all_data = sm.get_all()
        assert all_data["identity"]["name"] == "Alice"
        assert all_data["preferences"]["theme"] == "dark"

    def test_delete(self):
        sm = SessionMemory()
        sm.set("identity", "name", "Alice")
        assert sm.delete("identity", "name") is True
        assert sm.get("identity", "name") is None

    def test_delete_missing(self):
        sm = SessionMemory()
        assert sm.delete("identity", "nope") is False

    def test_clear(self):
        sm = SessionMemory()
        sm.set("identity", "name", "Alice")
        sm.set("preferences", "theme", "dark")
        sm.clear()
        assert sm.get_all() == {}

    def test_isolation(self):
        """Session memory instances are independent."""
        sm1 = SessionMemory()
        sm2 = SessionMemory()
        sm1.set("identity", "name", "Alice")
        assert sm2.get("identity", "name") is None


# ── EphemeralStore tests ──────────────────────────────────
class TestEphemeralStore:
    def test_set_and_get(self):
        es = EphemeralStore()
        es.set("api_key", "sk-123", ttl_seconds=10.0)
        assert es.get("api_key") == "sk-123"

    def test_expiration(self):
        es = EphemeralStore()
        es.set("token", "abc", ttl_seconds=0.05)  # 50ms TTL
        time.sleep(0.1)
        assert es.get("token") is None

    def test_delete(self):
        es = EphemeralStore()
        es.set("key", "val", ttl_seconds=60.0)
        assert es.delete("key") is True
        assert es.get("key") is None

    def test_delete_missing(self):
        es = EphemeralStore()
        assert es.delete("nope") is False

    def test_clear(self):
        es = EphemeralStore()
        es.set("a", "1", ttl_seconds=60.0)
        es.set("b", "2", ttl_seconds=60.0)
        es.clear()
        assert es.get("a") is None
        assert es.get("b") is None

    def test_purge_expired(self):
        es = EphemeralStore()
        es.set("short", "val", ttl_seconds=0.05)
        es.set("long", "val", ttl_seconds=60.0)
        time.sleep(0.1)
        purged = es.purge_expired()
        assert purged == 1
        assert es.get("long") == "val"


# ── PromotionRule tests ───────────────────────────────────
class TestPromotionRules:
    def test_default_rules_exist(self):
        assert len(DEFAULT_PROMOTION_RULES) >= 2

    def test_session_to_preference_rule(self):
        rule = DEFAULT_PROMOTION_RULES[0]
        assert rule.from_tier == MemoryTier.SESSION
        assert rule.to_tier == MemoryTier.PREFERENCE

    def test_preference_to_long_term_rule(self):
        rule = DEFAULT_PROMOTION_RULES[1]
        assert rule.from_tier == MemoryTier.PREFERENCE
        assert rule.to_tier == MemoryTier.LONG_TERM
        assert rule.min_confirmations == 3
        assert rule.min_age_hours == 24.0

    def test_custom_rule(self):
        rule = PromotionRule(
            from_tier=MemoryTier.SESSION,
            to_tier=MemoryTier.LONG_TERM,
            min_confirmations=5,
            min_age_hours=48.0,
            requires_categories=["identity"],
        )
        assert rule.from_tier == MemoryTier.SESSION
        assert rule.requires_categories == ["identity"]


# ── ProfileManager tier-gating tests ─────────────────────
class TestProfileTierGating:
    def test_session_tier_skips_profile_write(self):
        """SESSION tier entries should not be written to user.md."""
        from memory.profiles import ProfileManager
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = ProfileManager(Path(tmpdir))
            original = pm.load_user_context()
            pm.update_user("identity", "temp_session", "value",
                           tier=MemoryTier.SESSION)
            after = pm.load_user_context()
            assert original == after  # No change

    def test_long_term_writes_to_profile(self):
        """LONG_TERM tier entries should be written to user.md."""
        from memory.profiles import ProfileManager
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = ProfileManager(Path(tmpdir))
            pm.update_user("identity", "name", "Alice",
                           tier=MemoryTier.LONG_TERM)
            content = pm.load_user_context()
            assert "Alice" in content

    def test_secret_sensitivity_blocks_profile(self):
        """SECRET sensitivity entries should never reach user.md."""
        from memory.profiles import ProfileManager
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = ProfileManager(Path(tmpdir))
            pm.update_user("identity", "api_key", "sk-secret-123",
                           sensitivity=MemorySensitivity.SECRET)
            content = pm.load_user_context()
            assert "sk-secret-123" not in content

    def test_redaction_of_suspicious_values(self):
        """Values that look like API keys should be redacted."""
        from memory.profiles import ProfileManager
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = ProfileManager(Path(tmpdir))
            pm.update_user("identity", "token", "sk-abc123xyz",
                           tier=MemoryTier.LONG_TERM)
            content = pm.load_user_context()
            assert "sk-abc123xyz" not in content
            assert "[REDACTED]" in content
