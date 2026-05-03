from __future__ import annotations

from runtime.validation.common import ensure_not_empty


def validate_hostname(hostname: str) -> str:
    return ensure_not_empty(hostname, "hostname")
