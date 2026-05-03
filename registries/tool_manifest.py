from __future__ import annotations


class ToolManifest:
    def __init__(self) -> None:
        self._specs: dict[str, object] = {}

    def add(self, tool_name: str, spec: object) -> object | None:
        previous = self._specs.get(tool_name)
        self._specs[tool_name] = spec
        return previous

    def get(self, tool_name: str) -> object | None:
        return self._specs.get(tool_name)
