import asyncio
import socket

from dashboard_v2.bridge import (
    ApprovalRequest,
    DashboardBridge,
    DashboardState,
    LogEntry,
    TelemetrySnapshot,
)
from agent.runtime import RuntimeStatus


def test_dashboard_state_serializes_scene_and_flags():
    state = DashboardState(
        phase="speaking",
        status="SPEAKING",
        muted=True,
        connected=False,
        quality_tier="ultra",
    )

    assert state.to_payload() == {
        "phase": "speaking",
        "status": "SPEAKING",
        "muted": True,
        "connected": False,
        "qualityTier": "ultra",
    }


def test_bridge_records_pending_events_for_ui_updates():
    bridge = DashboardBridge()

    bridge.publish_state("THINKING")
    bridge.append_log("Buddy: Running diagnostics")
    bridge.publish_runtime_status({"mode": "autonomous"})
    bridge.publish_telemetry(
        TelemetrySnapshot(cpu_percent=42.5, memory_percent=58.0, network_in_kbps=12.0, network_out_kbps=8.0)
    )

    event_types = [event["type"] for event in bridge.drain_pending_events()]
    assert event_types == [
        "ui.state.changed",
        "ui.log.append",
        "ui.runtime.status",
        "ui.telemetry.snapshot",
    ]


def test_bridge_marks_muted_state_in_snapshot():
    bridge = DashboardBridge()

    bridge.publish_state("MUTED")

    assert bridge.snapshot()["state"]["muted"] is True
    assert bridge.snapshot()["state"]["status"] == "MUTED"


def test_bridge_tracks_latest_snapshot_for_new_clients():
    bridge = DashboardBridge()
    bridge.publish_state("LISTENING")
    bridge.append_log("SYS: online")
    bridge.publish_approval_request(ApprovalRequest(id="apr-1", message="Allow shutdown?"))

    snapshot = bridge.snapshot()

    assert snapshot["state"]["status"] == "LISTENING"
    assert len(snapshot["logs"]) == 1
    assert snapshot["logs"][0]["message"] == "SYS: online"
    assert snapshot["logs"][0]["level"] == "info"
    assert snapshot["approvalRequest"]["id"] == "apr-1"


def test_bridge_dispatches_submitted_command_to_callback():
    bridge = DashboardBridge()
    received: list[str] = []
    bridge.set_command_callback(received.append)

    asyncio.run(
        bridge._handle_client_message(
            '{"type":"ui.command.submitted","payload":{"command":"open notepad"}}'
        )
    )

    assert received == ["open notepad"]


def test_bridge_suppresses_duplicate_commands_inside_guard_window():
    bridge = DashboardBridge()
    received: list[str] = []
    bridge.set_command_callback(received.append)

    asyncio.run(
        bridge._handle_client_message(
            '{"type":"ui.command.submitted","payload":{"command":"hii"}}'
        )
    )
    asyncio.run(
        bridge._handle_client_message(
            '{"type":"ui.command.submitted","payload":{"command":"hii"}}'
        )
    )

    assert received == ["hii"]
    assert any("Duplicate command suppressed" in entry["payload"]["message"] for entry in bridge.drain_pending_events())


def test_bridge_merges_runtime_status_dataclass_fields():
    bridge = DashboardBridge()
    bridge.publish_runtime_status({"setupRequired": False, "runtimeReady": True})
    bridge.publish_runtime_status(RuntimeStatus(current_goal="test", current_step="step-1", total_steps=2))

    snapshot = bridge.snapshot()

    assert snapshot["runtimeStatus"]["setupRequired"] is False
    assert snapshot["runtimeStatus"]["runtimeReady"] is True
    assert snapshot["runtimeStatus"]["current_goal"] == "test"
    assert snapshot["runtimeStatus"]["current_step"] == "step-1"


def test_bridge_processes_config_submit_callback():
    bridge = DashboardBridge()
    submitted: list[dict] = []
    bridge.set_config_callback(lambda payload: submitted.append(payload) or {"configReady": True, "setupRequired": False})

    asyncio.run(
        bridge._handle_client_message(
            '{"type":"ui.config.submit","payload":{"geminiApiKey":"abc","osSystem":"windows"}}'
        )
    )

    assert submitted == [{"geminiApiKey": "abc", "osSystem": "windows"}]
    assert bridge.snapshot()["runtimeStatus"]["configReady"] is True


def test_bridge_suppresses_duplicate_logs_inside_window():
    bridge = DashboardBridge()

    bridge.append_log("SYS: BUDDY online.")
    bridge.append_log("SYS: BUDDY online.")

    snapshot = bridge.snapshot()
    assert len(snapshot["logs"]) == 1


def test_bridge_reassigns_port_when_default_is_busy():
    holder = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    holder.bind(("127.0.0.1", 0))
    holder.listen(1)
    busy_port = holder.getsockname()[1]

    try:
        bridge = DashboardBridge(port=busy_port)
        bridge._ensure_available_port()

        assert bridge.port != busy_port
        assert bridge.port > 0
    finally:
        holder.close()


def test_bridge_emits_shutdown_requested_event():
    bridge = DashboardBridge()

    bridge.publish_shutdown_requested("Bye Buddy, shutting down.")

    events = bridge.drain_pending_events()
    assert events[-1] == {
        "type": "ui.shutdown.requested",
        "payload": {"farewell": "Bye Buddy, shutting down."},
    }


def test_bridge_processes_boot_complete_callback():
    bridge = DashboardBridge()
    seen: list[str] = []
    bridge.set_boot_complete_callback(lambda: seen.append("done"))

    asyncio.run(
        bridge._handle_client_message(
            '{"type":"ui.boot.completed","payload":{}}'
        )
    )

    assert seen == ["done"]
