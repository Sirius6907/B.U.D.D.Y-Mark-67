"""
agent/journal.py — Structured Execution Journal
=================================================
Rich per-step journal entries with scope checks, safety scans,
budget state, and rollback availability.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(slots=True)
class JournalEntry:
    node_id: str
    status: str
    summary: str
    tool: str = ""
    latency_ms: float = 0.0
    scope_check: str = ""           # "passed" | "blocked" | "approved"
    verification_method: str = ""   # "rule" | "vision" | "hybrid" | ""
    safety_scan: str = ""           # "clean" | "flagged:{category}"
    budget_remaining: str = ""      # "15/20 steps, 45s left" or ""
    rollback_available: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class ExecutionJournal:
    entries: list[JournalEntry] = field(default_factory=list)

    def record(
        self,
        node_id: str,
        status: str,
        summary: str,
        tool: str = "",
        latency_ms: float = 0.0,
        scope_check: str = "",
        verification_method: str = "",
        safety_scan: str = "",
        budget_remaining: str = "",
        rollback_available: bool = False,
    ) -> None:
        self.entries.append(JournalEntry(
            node_id=node_id,
            status=status,
            summary=summary,
            tool=tool,
            latency_ms=latency_ms,
            scope_check=scope_check,
            verification_method=verification_method,
            safety_scan=safety_scan,
            budget_remaining=budget_remaining,
            rollback_available=rollback_available,
        ))

    def to_dict(self) -> list[dict[str, Any]]:
        """JSON-serializable representation of all entries."""
        return [
            {
                "node_id": e.node_id,
                "status": e.status,
                "summary": e.summary,
                "tool": e.tool,
                "latency_ms": round(e.latency_ms, 2),
                "scope_check": e.scope_check,
                "verification_method": e.verification_method,
                "safety_scan": e.safety_scan,
                "budget_remaining": e.budget_remaining,
                "rollback_available": e.rollback_available,
                "timestamp": e.timestamp,
            }
            for e in self.entries
        ]

    def to_markdown(self) -> str:
        """Human-readable execution report."""
        if not self.entries:
            return "No journal entries recorded."

        lines = ["# Execution Journal", ""]
        lines.append(f"| # | Node | Tool | Status | Latency | Scope | Safety |")
        lines.append(f"|---|------|------|--------|---------|-------|--------|")
        for i, e in enumerate(self.entries, 1):
            lines.append(
                f"| {i} | {e.node_id} | {e.tool or '-'} | {e.status} | "
                f"{e.latency_ms:.0f}ms | {e.scope_check or '-'} | {e.safety_scan or '-'} |"
            )
        return "\n".join(lines)

    def summary_stats(self) -> dict[str, Any]:
        """Aggregated metrics from the journal."""
        total = len(self.entries)
        if total == 0:
            return {"total": 0}

        successes = sum(1 for e in self.entries if e.status == "success")
        failures = sum(1 for e in self.entries if e.status != "success")
        latencies = [e.latency_ms for e in self.entries if e.latency_ms > 0]
        avg_lat = sum(latencies) / len(latencies) if latencies else 0.0

        return {
            "total": total,
            "successes": successes,
            "failures": failures,
            "success_rate": round(successes / total, 3) if total else 0.0,
            "avg_latency_ms": round(avg_lat, 2),
            "scope_blocks": sum(1 for e in self.entries if e.scope_check == "blocked"),
            "safety_flags": sum(1 for e in self.entries if e.safety_scan.startswith("flagged")),
            "rollback_points": sum(1 for e in self.entries if e.rollback_available),
        }
