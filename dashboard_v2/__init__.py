"""Dashboard V2 bridge and UI facade."""

from .bridge import ApprovalRequest, DashboardBridge, DashboardState, LogEntry, TelemetrySnapshot
from .ui_facade import BuddyUI, WebBuddyUI, resolve_ui_mode

__all__ = [
    "ApprovalRequest",
    "BuddyUI",
    "DashboardBridge",
    "DashboardState",
    "LogEntry",
    "TelemetrySnapshot",
    "WebBuddyUI",
    "resolve_ui_mode",
]

