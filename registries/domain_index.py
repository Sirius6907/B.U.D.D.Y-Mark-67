from __future__ import annotations

from collections import defaultdict

DOMAIN_TARGET_COUNTS = {
    "files": 45,
    "storage": 25,
    "process": 26,
    "apps": 10,
    "services": 10,
    "windows": 8,
    "input": 5,
    "clipboard": 3,
    "screen": 4,
    "printers": 4,
    "network": 30,
    "wifi": 8,
    "bluetooth": 8,
    "usb": 6,
    "serial": 4,
    "shares": 4,
    "browser_nav": 30,
    "browser_dom": 40,
    "browser_auth": 20,
    "browser_tabs": 20,
    "browser_cookies": 20,
    "browser_history": 20,
    "browser_media": 20,
    "browser_downloads": 15,
    "browser_extensions": 15,
}


class DomainIndex:
    def __init__(self) -> None:
        self._entries: dict[str, list[str]] = defaultdict(list)

    def add(self, domain: str, tool_name: str) -> None:
        self._entries[domain].append(tool_name)

    def remove(self, domain: str, tool_name: str) -> None:
        entries = self._entries.get(domain)
        if not entries:
            return
        self._entries[domain] = [entry for entry in entries if entry != tool_name]
        if not self._entries[domain]:
            del self._entries[domain]

    def get(self, domain: str) -> list[str]:
        return list(self._entries.get(domain, ()))
