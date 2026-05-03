from __future__ import annotations

from pathlib import Path

from runtime.validation.common import ensure_not_empty


def validate_existing_path(path: str | Path) -> Path:
    candidate = Path(ensure_not_empty(str(path), "path")).expanduser()
    if not candidate.exists():
        raise FileNotFoundError(f"Path does not exist: {candidate}")
    return candidate
