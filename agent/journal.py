from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(slots=True)
class JournalEntry:
    node_id: str
    status: str
    summary: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class ExecutionJournal:
    entries: list[JournalEntry] = field(default_factory=list)

    def record(self, node_id: str, status: str, summary: str) -> None:
        self.entries.append(JournalEntry(node_id=node_id, status=status, summary=summary))
