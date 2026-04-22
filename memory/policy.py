from __future__ import annotations

from memory.schema import MemoryRecord, MemorySensitivity


def should_promote_memory(record: MemoryRecord) -> bool:
    if record.sensitivity == MemorySensitivity.SENSITIVE and record.confidence < 0.9:
        return False
    return record.confidence >= 0.75
