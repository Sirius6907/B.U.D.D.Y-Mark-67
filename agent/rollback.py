"""
agent/rollback.py — Undo / Rollback Registry
================================================
Captures snapshots before destructive actions and provides
undo capability for file operations and system state changes.
"""
from __future__ import annotations

import json
import shutil
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable


class RollbackType(str, Enum):
    FILE_CREATE  = "file_create"    # undo = delete the file
    FILE_MODIFY  = "file_modify"    # undo = restore backup
    FILE_DELETE  = "file_delete"    # undo = restore from backup
    SETTING      = "setting"        # undo = revert to previous value
    APP_LAUNCH   = "app_launch"     # undo = close the app
    CUSTOM       = "custom"         # undo = call provided callback


@dataclass(slots=True)
class RollbackEntry:
    """Captures state before a destructive action."""
    entry_id: str
    task_id: str
    rollback_type: RollbackType
    description: str
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)
    # For file ops: path to the backup copy
    backup_path: str = ""
    # For settings: the previous value
    previous_value: str = ""
    # Was this undo actually executed?
    undone: bool = False


class RollbackRegistry:
    """
    Maintains an ordered stack of rollback entries per task.
    Supports single-step undo, full-task undo, and inspection.

    The registry persists backups to a scratch directory so file
    restores survive process restarts within a session.
    """

    def __init__(self, backup_dir: Path | None = None):
        self._backup_dir = backup_dir or Path("./data/rollback_backups")
        self._backup_dir.mkdir(parents=True, exist_ok=True)
        self._entries: list[RollbackEntry] = []
        self._counter: int = 0

    # ── Snapshot capture ─────────────────────────────────
    def snapshot_file_create(self, task_id: str, file_path: str | Path) -> RollbackEntry:
        """Record that a file was created (undo = delete it)."""
        entry = self._make_entry(
            task_id=task_id,
            rollback_type=RollbackType.FILE_CREATE,
            description=f"Created: {file_path}",
            metadata={"file_path": str(file_path)},
        )
        self._entries.append(entry)
        return entry

    def snapshot_file_modify(self, task_id: str, file_path: str | Path) -> RollbackEntry | None:
        """Backup a file before modification."""
        fp = Path(file_path)
        if not fp.exists():
            return None

        backup = self._backup_dir / f"{self._counter}_{fp.name}.bak"
        shutil.copy2(fp, backup)

        entry = self._make_entry(
            task_id=task_id,
            rollback_type=RollbackType.FILE_MODIFY,
            description=f"Modified: {file_path}",
            metadata={"file_path": str(file_path)},
            backup_path=str(backup),
        )
        self._entries.append(entry)
        return entry

    def snapshot_file_delete(self, task_id: str, file_path: str | Path) -> RollbackEntry | None:
        """Backup a file before deletion."""
        fp = Path(file_path)
        if not fp.exists():
            return None

        backup = self._backup_dir / f"{self._counter}_{fp.name}.deleted"
        shutil.copy2(fp, backup)

        entry = self._make_entry(
            task_id=task_id,
            rollback_type=RollbackType.FILE_DELETE,
            description=f"Deleted: {file_path}",
            metadata={"file_path": str(file_path)},
            backup_path=str(backup),
        )
        self._entries.append(entry)
        return entry

    def snapshot_setting(self, task_id: str, key: str, previous_value: str) -> RollbackEntry:
        """Record a system setting change."""
        entry = self._make_entry(
            task_id=task_id,
            rollback_type=RollbackType.SETTING,
            description=f"Setting '{key}' changed",
            metadata={"setting_key": key},
            previous_value=previous_value,
        )
        self._entries.append(entry)
        return entry

    def snapshot_custom(self, task_id: str, description: str,
                        metadata: dict[str, Any] | None = None) -> RollbackEntry:
        """Record a custom rollback checkpoint."""
        entry = self._make_entry(
            task_id=task_id,
            rollback_type=RollbackType.CUSTOM,
            description=description,
            metadata=metadata or {},
        )
        self._entries.append(entry)
        return entry

    # ── Undo operations ──────────────────────────────────
    def undo_last(self, task_id: str | None = None) -> RollbackEntry | None:
        """
        Undo the most recent entry (optionally filtered by task).
        Returns the undone entry, or None if nothing to undo.
        """
        for i in range(len(self._entries) - 1, -1, -1):
            entry = self._entries[i]
            if entry.undone:
                continue
            if task_id and entry.task_id != task_id:
                continue
            self._execute_undo(entry)
            return entry
        return None

    def undo_task(self, task_id: str) -> list[RollbackEntry]:
        """Undo all entries for a task, in reverse order."""
        undone: list[RollbackEntry] = []
        for entry in reversed(self._entries):
            if entry.task_id != task_id or entry.undone:
                continue
            self._execute_undo(entry)
            undone.append(entry)
        return undone

    def _execute_undo(self, entry: RollbackEntry) -> bool:
        """Actually perform the undo for a single entry."""
        try:
            if entry.rollback_type == RollbackType.FILE_CREATE:
                fp = Path(entry.metadata["file_path"])
                if fp.exists():
                    fp.unlink()

            elif entry.rollback_type == RollbackType.FILE_MODIFY:
                if entry.backup_path:
                    backup = Path(entry.backup_path)
                    target = Path(entry.metadata["file_path"])
                    if backup.exists():
                        shutil.copy2(backup, target)

            elif entry.rollback_type == RollbackType.FILE_DELETE:
                if entry.backup_path:
                    backup = Path(entry.backup_path)
                    target = Path(entry.metadata["file_path"])
                    if backup.exists():
                        shutil.copy2(backup, target)

            # SETTING and CUSTOM need external handlers (logged only)

            entry.undone = True
            return True
        except Exception:
            return False

    # ── Query ────────────────────────────────────────────
    def get_entries(self, task_id: str | None = None) -> list[RollbackEntry]:
        if task_id:
            return [e for e in self._entries if e.task_id == task_id]
        return list(self._entries)

    def get_pending(self, task_id: str | None = None) -> list[RollbackEntry]:
        """Get entries that haven't been undone yet."""
        entries = self.get_entries(task_id)
        return [e for e in entries if not e.undone]

    def count(self, task_id: str | None = None) -> int:
        return len(self.get_entries(task_id))

    def clear(self) -> None:
        """Clear all entries and backup files."""
        self._entries.clear()
        if self._backup_dir.exists():
            for f in self._backup_dir.iterdir():
                if f.is_file():
                    f.unlink()

    # ── Internal ─────────────────────────────────────────
    def _make_entry(self, **kwargs: Any) -> RollbackEntry:
        self._counter += 1
        return RollbackEntry(entry_id=f"rb-{self._counter:04d}", **kwargs)
