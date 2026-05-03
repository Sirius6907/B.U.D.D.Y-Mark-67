from __future__ import annotations

from collections import defaultdict


class AliasIndex:
    def __init__(self) -> None:
        self._entries: dict[str, list[str]] = defaultdict(list)

    def add(self, alias: str, tool_name: str) -> None:
        self._entries[alias].append(tool_name)

    def remove(self, alias: str, tool_name: str) -> None:
        entries = self._entries.get(alias)
        if not entries:
            return
        self._entries[alias] = [entry for entry in entries if entry != tool_name]
        if not self._entries[alias]:
            del self._entries[alias]

    def get(self, alias: str) -> list[str]:
        return list(self._entries.get(alias, ()))
