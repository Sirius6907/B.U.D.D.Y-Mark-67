from __future__ import annotations

import asyncio
import json
import socket
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any, Callable

from buddy_logging import get_logger


logger = get_logger("dashboard.bridge")


@dataclass(slots=True)
class DashboardState:
    phase: str = "boot"
    status: str = "BOOTING"
    muted: bool = False
    connected: bool = True
    quality_tier: str = "high"

    def to_payload(self) -> dict[str, Any]:
        return {
            "phase": self.phase,
            "status": self.status,
            "muted": self.muted,
            "connected": self.connected,
            "qualityTier": self.quality_tier,
        }


@dataclass(slots=True)
class TelemetrySnapshot:
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    network_in_kbps: float = 0.0
    network_out_kbps: float = 0.0
    disk_percent: float = 0.0

    def to_payload(self) -> dict[str, Any]:
        return {
            "cpuPercent": self.cpu_percent,
            "memoryPercent": self.memory_percent,
            "networkInKbps": self.network_in_kbps,
            "networkOutKbps": self.network_out_kbps,
            "diskPercent": self.disk_percent,
        }


@dataclass(slots=True)
class LogEntry:
    message: str
    level: str = "info"
    timestamp: float = field(default_factory=time.time)

    def to_payload(self) -> dict[str, Any]:
        return {"message": self.message, "level": self.level, "timestamp": self.timestamp}


@dataclass(slots=True)
class ApprovalRequest:
    id: str
    message: str

    def to_payload(self) -> dict[str, str]:
        return {"id": self.id, "message": self.message}


class DashboardBridge:
    def __init__(self, host: str = "127.0.0.1", port: int = 8765) -> None:
        self.host = host
        self.port = port
        self.state = DashboardState()
        self.logs: list[LogEntry] = []
        self.runtime_status: dict[str, Any] = {}
        self.telemetry = TelemetrySnapshot()
        self.voice_activity: dict[str, Any] = {"level": 0.0}
        self.approval_request: ApprovalRequest | None = None
        self._pending_events: list[dict[str, Any]] = []
        self._clients: set[Any] = set()
        self._command_callback: Callable[[str], None] | None = None
        self._config_callback: Callable[[dict[str, Any]], dict[str, Any] | None] | None = None
        self._boot_complete_callback: Callable[[], None] | None = None
        self._approval_events: dict[str, tuple[threading.Event, dict[str, bool]]] = {}
        self._last_command: tuple[str, float] | None = None
        self._last_log: tuple[str, str, float] | None = None
        self._lock = threading.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._started = threading.Event()
        self._shutdown_signal: asyncio.Event | None = None

    def _ensure_available_port(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind((self.host, self.port))
            except OSError:
                probe.bind((self.host, 0))
                chosen_port = int(probe.getsockname()[1])
                logger.warning(
                    "Dashboard websocket port %s was busy. Reassigned to %s for this run.",
                    self.port,
                    chosen_port,
                )
                self.port = chosen_port

    def set_command_callback(self, callback: Callable[[str], None] | None) -> None:
        self._command_callback = callback

    def set_config_callback(self, callback: Callable[[dict[str, Any]], dict[str, Any] | None] | None) -> None:
        self._config_callback = callback

    def set_boot_complete_callback(self, callback: Callable[[], None] | None) -> None:
        self._boot_complete_callback = callback

    def drain_pending_events(self) -> list[dict[str, Any]]:
        with self._lock:
            drained = list(self._pending_events)
            self._pending_events.clear()
            return drained

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "state": self.state.to_payload(),
                "logs": [entry.to_payload() for entry in self.logs[-100:]],
                "runtimeStatus": dict(self.runtime_status),
                "telemetry": self.telemetry.to_payload(),
                "voiceActivity": dict(self.voice_activity),
                "approvalRequest": self.approval_request.to_payload() if self.approval_request else None,
            }

    def publish_state(self, status: str, *, phase: str | None = None, connected: bool | None = None) -> None:
        phase_map = {
            "BOOTING": "boot",
            "LISTENING": "idle",
            "PROCESSING": "execution",
            "THINKING": "thinking",
            "SPEAKING": "speaking",
            "MUTED": "idle",
        }
        with self._lock:
            self.state.status = status
            self.state.phase = phase or phase_map.get(status, "idle")
            self.state.muted = status == "MUTED"
            if connected is not None:
                self.state.connected = connected
            payload = self.state.to_payload()
        self._queue_event("ui.state.changed", payload)

    def publish_runtime_status(self, status: Any) -> None:
        if is_dataclass(status):
            payload = asdict(status)
        elif isinstance(status, dict):
            payload = dict(status)
        else:
            payload = {"value": str(status)}
        with self._lock:
            self.runtime_status = {**self.runtime_status, **payload}
            merged = dict(self.runtime_status)
        self._queue_event("ui.runtime.status", merged)

    def publish_voice_level(self, level: float) -> None:
        payload = {"level": float(level)}
        with self._lock:
            self.voice_activity = payload
        self._queue_event("ui.voice.level", payload)

    def publish_telemetry(self, snapshot: TelemetrySnapshot) -> None:
        payload = snapshot.to_payload()
        with self._lock:
            self.telemetry = snapshot
        self._queue_event("ui.telemetry.snapshot", payload)

    def append_log(self, message: str, *, level: str = "info") -> None:
        now = time.monotonic()
        with self._lock:
            if self._last_log is not None:
                last_message, last_level, last_time = self._last_log
                if last_message == message and last_level == level and (now - last_time) <= 10.0:
                    return
            self._last_log = (message, level, now)
        entry = LogEntry(message=message, level=level)
        with self._lock:
            self.logs.append(entry)
            self.logs = self.logs[-400:]
        self._queue_event("ui.log.append", entry.to_payload())

    def publish_approval_request(self, request: ApprovalRequest) -> None:
        with self._lock:
            self.approval_request = request
        self._queue_event("ui.approval.requested", request.to_payload())

    def publish_shutdown_requested(self, farewell: str) -> None:
        self._queue_event("ui.shutdown.requested", {"farewell": farewell})

    def request_approval(self, message: str, timeout: float | None = None) -> bool:
        request_id = f"approval-{uuid.uuid4().hex[:10]}"
        event = threading.Event()
        result = {"approved": False}
        with self._lock:
            self._approval_events[request_id] = (event, result)
        self.publish_approval_request(ApprovalRequest(id=request_id, message=message))
        event.wait(timeout=timeout)
        with self._lock:
            self.approval_request = None
            self._approval_events.pop(request_id, None)
        self._queue_event("ui.approval.cleared", {"id": request_id})
        return result["approved"]

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._ensure_available_port()
        self._thread = threading.Thread(target=self._run_server_thread, daemon=True)
        self._thread.start()
        self._started.wait(timeout=3)

    def stop(self) -> None:
        shutdown_signal = self._shutdown_signal
        loop = self._loop
        if shutdown_signal is not None and loop is not None and loop.is_running():
            loop.call_soon_threadsafe(shutdown_signal.set)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def _run_server_thread(self) -> None:
        try:
            asyncio.run(self._serve())
        except Exception as exc:
            logger.exception("Dashboard websocket server failed to start: %s", exc)
            # The UI can still operate in degraded mode without the socket server.
            self._started.set()

    async def _serve(self) -> None:
        try:
            from websockets.asyncio.server import serve
        except Exception:
            self._started.set()
            return

        self._loop = asyncio.get_running_loop()
        self._shutdown_signal = asyncio.Event()

        async def handler(websocket: Any) -> None:
            self._clients.add(websocket)
            try:
                await websocket.send(json.dumps({"type": "ui.snapshot", "payload": self.snapshot()}))
                async for raw_message in websocket:
                    await self._handle_client_message(raw_message)
            finally:
                self._clients.discard(websocket)

        async with serve(handler, self.host, self.port):
            logger.info("Dashboard websocket server listening on ws://%s:%s", self.host, self.port)
            self._started.set()
            await self._shutdown_signal.wait()

    async def _handle_client_message(self, raw_message: str) -> None:
        data = json.loads(raw_message)
        event_type = data.get("type")
        payload = data.get("payload", {})
        if event_type == "ui.command.submitted":
            command = str(payload.get("command", "")).strip()
            if command and self._is_duplicate_command(command):
                self.append_log(f"Duplicate command suppressed: {command}", level="warning")
                return
            if command:
                self.append_log(f"CMD: {command}", level="debug")
            if command and self._command_callback:
                threading.Thread(target=self._command_callback, args=(command,), daemon=True).start()
            elif command:
                self.append_log("Command ignored because runtime callback is not ready.", level="warning")
        elif event_type == "ui.approval.resolved":
            request_id = payload.get("id")
            approved = bool(payload.get("approved"))
            with self._lock:
                wait_state = self._approval_events.get(request_id)
            if wait_state:
                event, result = wait_state
                result["approved"] = approved
                event.set()
        elif event_type == "ui.config.submit":
            if self._config_callback is not None:
                response = self._config_callback(dict(payload)) or {}
                if response:
                    self.publish_runtime_status(response)
        elif event_type == "ui.quality.changed":
            quality = str(payload.get("qualityTier", "high"))
            with self._lock:
                self.state.quality_tier = quality
            self._queue_event("ui.state.changed", self.state.to_payload())
        elif event_type == "ui.boot.completed":
            if self._boot_complete_callback is not None:
                threading.Thread(target=self._boot_complete_callback, daemon=True).start()

    def _queue_event(self, event_type: str, payload: dict[str, Any]) -> None:
        event = {"type": event_type, "payload": payload}
        with self._lock:
            self._pending_events.append(event)
        if self._loop and self._clients:
            asyncio.run_coroutine_threadsafe(self._broadcast(event), self._loop)

    async def _broadcast(self, event: dict[str, Any]) -> None:
        if not self._clients:
            return
        message = json.dumps(event)
        stale: list[Any] = []
        for websocket in list(self._clients):
            try:
                await websocket.send(message)
            except Exception:
                stale.append(websocket)
        for websocket in stale:
            self._clients.discard(websocket)

    def _is_duplicate_command(self, command: str, *, threshold_seconds: float = 0.6) -> bool:
        now = time.monotonic()
        with self._lock:
            if self._last_command is None:
                self._last_command = (command, now)
                return False
            previous_command, previous_time = self._last_command
            self._last_command = (command, now)
        return previous_command == command and (now - previous_time) <= threshold_seconds
