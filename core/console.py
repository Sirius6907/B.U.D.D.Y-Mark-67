from __future__ import annotations

import sys


def _configure_stream(stream: object) -> None:
    reconfigure = getattr(stream, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8", errors="backslashreplace")


def configure_console_output() -> None:
    _configure_stream(sys.stdout)
    _configure_stream(sys.stderr)
