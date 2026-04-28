from __future__ import annotations

from memory.profiles import ProfileManager


class MemoryConsolidator:
    def __init__(self, profile_manager: ProfileManager):
        self.profile_manager = profile_manager

    def consolidate(self, facts: dict[str, dict[str, object]]) -> None:
        for category, entries in facts.items():
            if not isinstance(entries, dict):
                continue
            for key, value in entries.items():
                if isinstance(value, dict):
                    value = value.get("value")
                if value is None:
                    continue
                self.profile_manager.update_user(category, key, str(value))
