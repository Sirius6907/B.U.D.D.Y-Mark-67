"""
agent/metrics.py — Operational Telemetry System
================================================
Structured event recording with persistence, querying, and aggregation.
Replaces the simple Counter-based tracker with a production telemetry pipeline.
"""
from __future__ import annotations

import uuid
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any, List, Optional


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class TelemetryEvent:
    """A single telemetry event emitted during execution."""
    event_id: str
    event_type: str           # step_executed, approval_requested, verification_result, scope_violation, budget_check
    timestamp: str
    latency_ms: float = 0.0
    tool: str = ""
    node_id: str = ""
    goal: str = ""
    status: str = ""          # success | failure | timeout | blocked | approved | denied
    retry_count: int = 0
    scope_violations: list[str] = field(default_factory=list)
    safety_flags: list[str] = field(default_factory=list)
    payload: dict[str, Any] = field(default_factory=dict)


# Ring buffer size for in-memory events
_MAX_RING_BUFFER = 500


class MetricsTracker:
    """Production telemetry tracker with persistence and query API.

    Features:
    - Thread-safe event recording
    - In-memory ring buffer for fast queries
    - Optional DPStore persistence
    - Typed recording methods for common event types
    - Aggregation/summary for dashboards
    """

    def __init__(self, store=None):
        self.store = store
        self._lock = Lock()
        self._counts = Counter()
        self._events: list[TelemetryEvent] = []

    # ── Core recording ───────────────────────────────────────────────────

    def _emit(self, event: TelemetryEvent) -> None:
        """Thread-safe event emission to ring buffer + optional persistence."""
        with self._lock:
            self._counts["events_recorded"] += 1
            self._counts[f"event:{event.event_type}"] += 1
            if event.status:
                self._counts[f"status:{event.status}"] += 1
            if event.tool:
                self._counts[f"tool:{event.tool}"] += 1

            # Ring buffer
            self._events.append(event)
            if len(self._events) > _MAX_RING_BUFFER:
                self._events = self._events[-_MAX_RING_BUFFER:]

        # Persist to store (outside lock to avoid blocking)
        if self.store is not None:
            try:
                self.store.record_metric_event(
                    event.event_type,
                    {
                        "event_id": event.event_id,
                        "tool": event.tool,
                        "node_id": event.node_id,
                        "goal": event.goal,
                        "status": event.status,
                        "latency_ms": event.latency_ms,
                        "retry_count": event.retry_count,
                        "scope_violations": event.scope_violations,
                        "safety_flags": event.safety_flags,
                        **event.payload,
                    },
                    event.timestamp,
                )
            except Exception:
                pass

    # ── Legacy compatibility ─────────────────────────────────────────────

    def record(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """Legacy record method — wraps into TelemetryEvent for backward compat."""
        payload = payload or {}
        event = TelemetryEvent(
            event_id=uuid.uuid4().hex[:12],
            event_type=event_type,
            timestamp=_utc_now(),
            tool=payload.get("tool", ""),
            node_id=payload.get("node_id", ""),
            goal=payload.get("goal", ""),
            status=payload.get("status", ""),
            latency_ms=float(payload.get("latency_ms", 0.0)),
            payload={k: v for k, v in payload.items()
                     if k not in ("tool", "node_id", "goal", "status", "latency_ms")},
        )
        self._emit(event)

    # ── Typed recording methods ──────────────────────────────────────────

    def record_step(
        self,
        node_id: str,
        tool: str,
        status: str,
        latency_ms: float,
        goal: str = "",
        retry_count: int = 0,
        **extra: Any,
    ) -> None:
        """Record a step execution event."""
        self._emit(TelemetryEvent(
            event_id=uuid.uuid4().hex[:12],
            event_type="step_executed",
            timestamp=_utc_now(),
            node_id=node_id,
            tool=tool,
            status=status,
            latency_ms=latency_ms,
            goal=goal,
            retry_count=retry_count,
            payload=extra,
        ))

    def record_approval(
        self,
        node_id: str,
        tool: str,
        approved: bool,
        wait_ms: float = 0.0,
    ) -> None:
        """Record an approval request and its outcome."""
        self._emit(TelemetryEvent(
            event_id=uuid.uuid4().hex[:12],
            event_type="approval_requested",
            timestamp=_utc_now(),
            node_id=node_id,
            tool=tool,
            status="approved" if approved else "denied",
            latency_ms=wait_ms,
        ))

    def record_verification(
        self,
        node_id: str,
        verified: bool,
        method: str = "",
        latency_ms: float = 0.0,
    ) -> None:
        """Record a verification result."""
        self._emit(TelemetryEvent(
            event_id=uuid.uuid4().hex[:12],
            event_type="verification_result",
            timestamp=_utc_now(),
            node_id=node_id,
            status="verified" if verified else "failed",
            latency_ms=latency_ms,
            payload={"method": method},
        ))

    def record_scope_violation(
        self,
        node_id: str,
        tool: str,
        missing_scopes: list[str],
    ) -> None:
        """Record a scope violation (blocked by permission check)."""
        self._emit(TelemetryEvent(
            event_id=uuid.uuid4().hex[:12],
            event_type="scope_violation",
            timestamp=_utc_now(),
            node_id=node_id,
            tool=tool,
            status="blocked",
            scope_violations=missing_scopes,
        ))

    def record_safety_flag(
        self,
        node_id: str,
        tool: str,
        threats: list[str],
        blocked: bool = False,
    ) -> None:
        """Record a safety scanner flag."""
        self._emit(TelemetryEvent(
            event_id=uuid.uuid4().hex[:12],
            event_type="safety_flagged",
            timestamp=_utc_now(),
            node_id=node_id,
            tool=tool,
            status="blocked" if blocked else "flagged",
            safety_flags=threats,
        ))

    def record_budget_check(
        self,
        exceeded: bool,
        reason: str = "",
        remaining: dict[str, Any] | None = None,
    ) -> None:
        """Record a budget check event."""
        self._emit(TelemetryEvent(
            event_id=uuid.uuid4().hex[:12],
            event_type="budget_check",
            timestamp=_utc_now(),
            status="exceeded" if exceeded else "ok",
            payload={"reason": reason, "remaining": remaining or {}},
        ))

    # ── Query API ────────────────────────────────────────────────────────

    def query(
        self,
        event_type: str | None = None,
        tool: str | None = None,
        status: str | None = None,
        since: str | None = None,
        limit: int = 50,
    ) -> list[TelemetryEvent]:
        """Query in-memory events with optional filters."""
        with self._lock:
            results = list(self._events)

        if event_type:
            results = [e for e in results if e.event_type == event_type]
        if tool:
            results = [e for e in results if e.tool == tool]
        if status:
            results = [e for e in results if e.status == status]
        if since:
            results = [e for e in results if e.timestamp >= since]

        return results[-limit:]

    # ── Aggregation ──────────────────────────────────────────────────────

    def snapshot(self) -> dict[str, int]:
        """Return raw counter snapshot (backward-compatible)."""
        with self._lock:
            return dict(self._counts)

    def summary(self) -> dict[str, Any]:
        """Aggregated dashboard data."""
        with self._lock:
            events = list(self._events)
            counts = dict(self._counts)

        total_steps = sum(1 for e in events if e.event_type == "step_executed")
        successes = sum(1 for e in events if e.event_type == "step_executed" and e.status == "success")
        failures = sum(1 for e in events if e.event_type == "step_executed" and e.status != "success")
        approvals = sum(1 for e in events if e.event_type == "approval_requested")
        scope_violations = sum(1 for e in events if e.event_type == "scope_violation")
        safety_flags = sum(1 for e in events if e.event_type == "safety_flagged")

        step_latencies = [e.latency_ms for e in events if e.event_type == "step_executed" and e.latency_ms > 0]
        avg_latency = sum(step_latencies) / len(step_latencies) if step_latencies else 0.0
        p95_latency = sorted(step_latencies)[int(len(step_latencies) * 0.95)] if step_latencies else 0.0

        # Per-tool breakdown
        tool_stats: dict[str, dict[str, int]] = {}
        for e in events:
            if e.event_type == "step_executed" and e.tool:
                if e.tool not in tool_stats:
                    tool_stats[e.tool] = {"total": 0, "success": 0, "failure": 0}
                tool_stats[e.tool]["total"] += 1
                if e.status == "success":
                    tool_stats[e.tool]["success"] += 1
                else:
                    tool_stats[e.tool]["failure"] += 1

        return {
            "total_events": counts.get("events_recorded", 0),
            "total_steps": total_steps,
            "successes": successes,
            "failures": failures,
            "success_rate": round(successes / total_steps, 3) if total_steps else 0.0,
            "approvals_requested": approvals,
            "scope_violations": scope_violations,
            "safety_flags": safety_flags,
            "avg_latency_ms": round(avg_latency, 2),
            "p95_latency_ms": round(p95_latency, 2),
            "tool_breakdown": tool_stats,
        }
