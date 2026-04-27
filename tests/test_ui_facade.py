import threading
from types import SimpleNamespace

from dashboard_v2.bridge import DashboardBridge
from dashboard_v2.ui_facade import WebBuddyUI, _RootLoop, resolve_ui_mode


def test_resolve_ui_mode_defaults_to_web(monkeypatch):
    monkeypatch.delenv("BUDDY_UI_MODE", raising=False)

    assert resolve_ui_mode() == "web"


def test_web_buddy_ui_forwards_public_api_calls_to_bridge(monkeypatch):
    monkeypatch.setenv("BUDDY_DISABLE_WEB_UI_LAUNCH", "1")
    ui = WebBuddyUI("face.png", bridge=DashboardBridge(), launch_frontend=False)
    ui.bridge.drain_pending_events()

    ui.set_state("PROCESSING")
    ui.write_log("Buddy: compiling")
    ui.set_muted(True)
    ui.update_runtime_status({"health": "nominal"})

    events = ui.bridge.drain_pending_events()
    assert [event["type"] for event in events] == [
        "ui.state.changed",
        "ui.state.changed",
        "ui.log.append",
        "ui.state.changed",
        "ui.runtime.status",
    ]

    assert ui.muted is True
    assert ui.speaking is False


def test_web_buddy_ui_submit_config_unblocks_waiters(monkeypatch):
    monkeypatch.delenv("BUDDY_GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("BUDDY_DISABLE_WEB_UI_LAUNCH", "1")
    monkeypatch.setattr("dashboard_v2.ui_facade.update_config", lambda **kwargs: None)

    ui = WebBuddyUI("face.png", bridge=DashboardBridge(), launch_frontend=False)
    waiter = threading.Thread(target=ui.wait_for_api_key)
    waiter.start()

    result = ui.submit_config({"geminiApiKey": "new-key", "osSystem": "windows"})
    waiter.join(timeout=2)

    assert result["configReady"] is True
    assert ui._api_key_ready is True
    assert not waiter.is_alive()


def test_web_buddy_ui_suppresses_duplicate_online_log(monkeypatch):
    monkeypatch.setenv("BUDDY_DISABLE_WEB_UI_LAUNCH", "1")
    ui = WebBuddyUI("face.png", bridge=DashboardBridge(), launch_frontend=False)
    ui.bridge.drain_pending_events()

    ui.write_log("SYS: BUDDY online.")
    ui.write_log("SYS: BUDDY online.")

    events = ui.bridge.drain_pending_events()
    assert [event["type"] for event in events] == ["ui.log.append"]


def test_root_loop_quit_stops_bridge_and_launcher():
    stop_event = threading.Event()
    bridge = SimpleNamespace(stop_called=False)
    launcher = SimpleNamespace(close_called=False)

    def stop() -> None:
        bridge.stop_called = True

    def close() -> None:
        launcher.close_called = True

    bridge.stop = stop
    launcher.close = close
    root = _RootLoop(launcher=launcher, stop_event=stop_event, bridge=bridge)

    root.quit()

    assert stop_event.is_set()
    assert bridge.stop_called is True
    assert launcher.close_called is True


def test_web_buddy_ui_mark_boot_complete_unblocks_waiters(monkeypatch):
    monkeypatch.setenv("BUDDY_DISABLE_WEB_UI_LAUNCH", "1")
    ui = WebBuddyUI("face.png", bridge=DashboardBridge(), launch_frontend=False)

    assert ui.wait_for_boot_sequence(timeout=0.01) is False

    ui.mark_boot_complete()

    assert ui.wait_for_boot_sequence(timeout=0.01) is True
