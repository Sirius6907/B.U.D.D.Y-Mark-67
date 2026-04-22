from memory.policy import should_promote_memory
from memory.schema import MemoryRecord, MemorySensitivity, MemoryType


def test_high_confidence_preference_is_promoted():
    record = MemoryRecord(
        memory_type=MemoryType.SEMANTIC,
        category="preferences",
        key="preferred_browser",
        value="Chrome",
        source="user_direct",
        confidence=0.95,
        sensitivity=MemorySensitivity.NORMAL,
    )
    assert should_promote_memory(record) is True


def test_low_confidence_sensitive_memory_is_not_promoted():
    record = MemoryRecord(
        memory_type=MemoryType.SEMANTIC,
        category="notes",
        key="password_hint",
        value="secret",
        source="inference",
        confidence=0.45,
        sensitivity=MemorySensitivity.SENSITIVE,
    )
    assert should_promote_memory(record) is False
