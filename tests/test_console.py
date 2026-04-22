from __future__ import annotations

from core.console import configure_console_output


class FakeStream:
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def reconfigure(self, **kwargs) -> None:
        self.calls.append(kwargs)


def test_configure_console_output_reconfigures_stdout_and_stderr(monkeypatch):
    stdout = FakeStream()
    stderr = FakeStream()

    monkeypatch.setattr("sys.stdout", stdout)
    monkeypatch.setattr("sys.stderr", stderr)

    configure_console_output()

    assert stdout.calls == [{"encoding": "utf-8", "errors": "backslashreplace"}]
    assert stderr.calls == [{"encoding": "utf-8", "errors": "backslashreplace"}]
