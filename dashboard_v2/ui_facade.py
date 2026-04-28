from __future__ import annotations

import os
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from config import get_api_key, get_os, update_config

from .bridge import DashboardBridge, TelemetrySnapshot


def resolve_ui_mode() -> str:
    return os.environ.get("BUDDY_UI_MODE", "web").strip().lower() or "web"


@dataclass
class _RootLoop:
    launcher: "ElectronLauncher | None"
    stop_event: threading.Event
    bridge: DashboardBridge | None = None

    def mainloop(self) -> None:
        if self.launcher and self.launcher.process is not None:
            try:
                self.launcher.process.wait()
            except KeyboardInterrupt:
                self.quit()
            return
        try:
            while not self.stop_event.is_set():
                time.sleep(0.25)
        except KeyboardInterrupt:
            self.quit()

    def quit(self) -> None:
        self.stop_event.set()
        if self.bridge is not None:
            try:
                self.bridge.stop()
            except Exception:
                pass
        if self.launcher is not None:
            self.launcher.close()


class ElectronLauncher:
    def __init__(self, app_dir: Path) -> None:
        self.app_dir = app_dir
        self.next_process: subprocess.Popen[str] | None = None
        self.electron_process: subprocess.Popen[str] | None = None
        self._stop_event = threading.Event()
        self._wait_thread: threading.Thread | None = None
        self._lock = threading.Lock()
        
        class ProcessGroup:
            def __init__(self, launcher):
                self._launcher = launcher
            def wait(self):
                while not self._launcher._stop_event.is_set():
                    p1 = self._launcher.next_process
                    p2 = self._launcher.electron_process
                    if p1 and p1.poll() is not None:
                        return
                    if p2 and p2.poll() is not None:
                        return
                    time.sleep(0.25)
            def poll(self):
                p1 = self._launcher.next_process
                p2 = self._launcher.electron_process
                if p1 and p1.poll() is not None:
                    return p1.poll()
                if p2 and p2.poll() is not None:
                    return p2.poll()
                return None
                
        self.process = ProcessGroup(self)

    def launch(self, bridge: DashboardBridge) -> None:
        if os.environ.get("BUDDY_DISABLE_WEB_UI_LAUNCH") == "1":
            return
        npm = "npm.cmd" if os.name == "nt" else "npm"
        env = os.environ.copy()
        env.setdefault("BUDDY_DASHBOARD_WS_URL", f"ws://{bridge.host}:{bridge.port}")
        
        # 1. Start Next.js dev server
        self.next_process = subprocess.Popen(
            f"{npm} run dev",
            cwd=self.app_dir,
            env=env,
            text=True,
            shell=True,
        )
        
        # 2. Start a thread to wait for port 3000 and launch Electron
        def wait_and_launch():
            import socket
            start_time = time.time()
            while not self._stop_event.is_set() and time.time() - start_time < 60:
                try:
                    with socket.create_connection(("127.0.0.1", 3000), timeout=1):
                        break
                except (socket.timeout, ConnectionRefusedError):
                    time.sleep(0.5)
                    continue
            
            with self._lock:
                if self._stop_event.is_set():
                    return
                    
                # Launch Electron
                self.electron_process = subprocess.Popen(
                    f"{npm} run electron",
                    cwd=self.app_dir,
                    env=env,
                    text=True,
                    shell=True,
                )
                
        self._wait_thread = threading.Thread(target=wait_and_launch, daemon=True)
        self._wait_thread.start()

    def close(self) -> None:
        self._stop_event.set()
        
        with self._lock:
            # Kill Electron
            if self.electron_process is not None:
                self._kill_process(self.electron_process)
                self.electron_process = None
                
            # Kill Next.js
            if self.next_process is not None:
                self._kill_process(self.next_process)
                self.next_process = None
                
            self.process = None

    def _kill_process(self, process: subprocess.Popen) -> None:
        if process.poll() is not None:
            return
        try:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
                process.wait(timeout=5)
            else:
                process.terminate()
                process.wait(timeout=2)
        except Exception:
            try:
                process.kill()
            except Exception:
                pass


class WebBuddyUI:
    def __init__(
        self,
        face_path: str,
        size: tuple[int, int] | None = None,
        *,
        bridge: DashboardBridge | None = None,
        launch_frontend: bool | None = None,
    ) -> None:
        self.face_path = face_path
        self.size = size
        self.bridge = bridge or DashboardBridge()
        self.speaking = False
        self.muted = False
        self._on_text_command_callback = None
        self._api_key_ready = self._api_keys_exist()
        self._last_log_message = ""
        self._stop_event = threading.Event()
        self._boot_complete_event = threading.Event()
        self.bridge.set_config_callback(self.submit_config)
        self.bridge.set_boot_complete_callback(self.mark_boot_complete)
        self.bridge.start()
        self._telemetry_thread = threading.Thread(target=self._publish_telemetry_loop, daemon=True)
        self._telemetry_thread.start()
        should_launch = launch_frontend if launch_frontend is not None else True
        app_dir = Path(__file__).resolve().parent.parent / "dashboard-v2"
        self.launcher = ElectronLauncher(app_dir) if should_launch else None
        if self.launcher:
            self.launcher.launch(self.bridge)
        self.root = _RootLoop(self.launcher, self._stop_event, self.bridge)
        if self._api_key_ready:
            self.bridge.publish_runtime_status(
                {"configReady": True, "setupRequired": False, "configError": "", "runtimeReady": False, "runtimeBooting": True}
            )
            self.bridge.publish_state("LISTENING", phase="idle")
        else:
            self.bridge.publish_runtime_status(
                {"configReady": False, "setupRequired": True, "configError": "", "runtimeReady": False, "runtimeBooting": False}
            )
            self.bridge.publish_state("BOOTING", phase="boot")

    @property
    def on_text_command(self):
        return self._on_text_command_callback

    @on_text_command.setter
    def on_text_command(self, value):
        self._on_text_command_callback = value
        self.bridge.set_command_callback(value)

    def _api_keys_exist(self) -> bool:
        try:
            return bool(get_api_key(required=False)) and bool(get_os())
        except Exception:
            return False

    def request_approval(self, message: str) -> bool:
        return self.bridge.request_approval(message)

    def submit_config(self, payload: dict[str, Any]) -> dict[str, Any]:
        gemini_api_key = str(payload.get("geminiApiKey", "")).strip()
        if not gemini_api_key:
            return {"configReady": False, "setupRequired": True, "configError": "Gemini API key is required."}

        update_config(
            gemini_api_key=gemini_api_key,
            telegram_bot_token=str(payload.get("telegramBotToken", "")).strip(),
            telegram_username=str(payload.get("telegramUsername", "")).strip(),
            telegram_user_id=str(payload.get("telegramUserId", "")).strip(),
            os_system=str(payload.get("osSystem", "windows")).strip().lower() or "windows",
        )
        self._api_key_ready = True
        self.bridge.publish_state("BOOTING", phase="boot")
        return {
            "configReady": True,
            "setupRequired": False,
            "configError": "",
            "runtimeReady": False,
            "runtimeBooting": True,
        }

    def set_state(self, state: str) -> None:
        self.bridge.publish_state(state)
        self.speaking = state == "SPEAKING"

    def set_muted(self, muted: bool) -> None:
        self.muted = muted
        self.speaking = False
        self.bridge.publish_state("MUTED" if muted else "LISTENING")

    def write_log(self, text: str) -> None:
        if text == "SYS: BUDDY online." and self._last_log_message == text:
            return
        lowered = text.lower()
        if lowered.startswith("you:"):
            self.set_state("PROCESSING")
        elif lowered.startswith("buddy:") or lowered.startswith("ai:"):
            self.set_state("SPEAKING")
        self._last_log_message = text
        self.bridge.append_log(text)

    def update_runtime_status(self, status: Any) -> None:
        self.bridge.publish_runtime_status(status)

    def start_speaking(self) -> None:
        self.set_state("SPEAKING")

    def stop_speaking(self) -> None:
        if not self.muted:
            self.set_state("LISTENING")

    def wait_for_api_key(self) -> None:
        while not self._api_key_ready:
            time.sleep(0.5)

    def wait_for_boot_sequence(self, timeout: float | None = None) -> bool:
        return self._boot_complete_event.wait(timeout=timeout)

    def mark_boot_complete(self) -> None:
        self._boot_complete_event.set()

    def _publish_telemetry_loop(self) -> None:
        try:
            import psutil
        except Exception:
            return

        disk_path = "C:\\" if os.name == "nt" else "/"
        counters = psutil.net_io_counters()
        prev_recv = counters.bytes_recv
        prev_sent = counters.bytes_sent
        time.sleep(1.0)

        while not self._stop_event.is_set():
            counters = psutil.net_io_counters()
            delta_recv = max(0.0, (counters.bytes_recv - prev_recv) / 1024.0)
            delta_sent = max(0.0, (counters.bytes_sent - prev_sent) / 1024.0)
            prev_recv = counters.bytes_recv
            prev_sent = counters.bytes_sent
            snapshot = TelemetrySnapshot(
                cpu_percent=psutil.cpu_percent(interval=None),
                memory_percent=psutil.virtual_memory().percent,
                network_in_kbps=round(delta_recv, 1),
                network_out_kbps=round(delta_sent, 1),
                disk_percent=psutil.disk_usage(disk_path).percent,
            )
            self.bridge.publish_telemetry(snapshot)
            time.sleep(1.0)


class LegacyBuddyUI:
    def __new__(cls, face_path: str, size: tuple[int, int] | None = None):
        from ui import BuddyUI as _LegacyBuddyUI

        return _LegacyBuddyUI(face_path, size=size)


class BuddyUI:
    def __new__(cls, face_path: str, size: tuple[int, int] | None = None):
        return WebBuddyUI(face_path, size=size)
