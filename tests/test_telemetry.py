"""Tests for MetricsTracker telemetry: recording, querying, and summary stats."""
import pytest
from agent.metrics import MetricsTracker, TelemetryEvent


# ── Recording & basic query ───────────────────────────────────────
def test_record_step_creates_event():
    mt = MetricsTracker()
    mt.record_step("n1", "open_app", "success", 120.5, goal="test")
    events = mt.query(event_type="step_executed")
    assert len(events) == 1
    assert events[0].tool == "open_app"
    assert events[0].latency_ms == 120.5


def test_record_approval():
    mt = MetricsTracker()
    mt.record_approval("n1", "run_command", True, 500.0)
    events = mt.query(event_type="approval_requested")
    assert len(events) == 1
    assert events[0].status == "approved"


def test_record_verification():
    mt = MetricsTracker()
    mt.record_verification("n1", True, "vision", 80.0)
    events = mt.query(event_type="verification_result")
    assert len(events) == 1
    assert events[0].payload["method"] == "vision"


def test_record_scope_violation():
    mt = MetricsTracker()
    mt.record_scope_violation("n1", "delete_file", ["can_write_files"])
    events = mt.query(event_type="scope_violation")
    assert len(events) == 1
    assert "can_write_files" in events[0].scope_violations


def test_record_safety_flag():
    mt = MetricsTracker()
    mt.record_safety_flag("n1", "shell_command", ["injection"], blocked=True)
    events = mt.query(event_type="safety_flagged")
    assert len(events) == 1
    assert "injection" in events[0].safety_flags


# ── Summary statistics ─────────────────────────────────────────────
def test_summary_empty():
    mt = MetricsTracker()
    s = mt.summary()
    assert s["total_events"] == 0


def test_summary_with_mixed_events():
    mt = MetricsTracker()
    mt.record_step("n1", "open_app", "success", 100.0)
    mt.record_step("n2", "type_text", "error", 200.0)
    mt.record_step("n3", "open_app", "success", 50.0)
    mt.record_approval("n4", "run_cmd", False, 300.0)

    s = mt.summary()
    assert s["total_events"] == 4
    assert s["success_rate"] > 0
    assert s["p95_latency_ms"] > 0
    assert "open_app" in s["tool_breakdown"]
    assert s["tool_breakdown"]["open_app"]["total"] == 2


# ── Ring buffer limit ──────────────────────────────────────────────
def test_ring_buffer_limit():
    """Default buffer is 500; filling beyond should trim oldest."""
    mt = MetricsTracker()
    for i in range(600):
        mt.record_step(f"n{i}", "tool", "success", 10.0)
    # query with no limit returns last 50 by default
    all_events = mt.query(limit=9999)
    assert len(all_events) <= 500


# ── Query filters ─────────────────────────────────────────────────
def test_query_filter_by_tool():
    mt = MetricsTracker()
    mt.record_step("n1", "open_app", "success", 50.0)
    mt.record_step("n2", "type_text", "success", 60.0)
    results = mt.query(tool="type_text")
    assert all(e.tool == "type_text" for e in results)


def test_query_filter_by_status():
    mt = MetricsTracker()
    mt.record_step("n1", "open_app", "success", 50.0)
    mt.record_step("n2", "open_app", "error", 60.0)
    results = mt.query(status="error")
    assert len(results) == 1
    assert results[0].status == "error"
