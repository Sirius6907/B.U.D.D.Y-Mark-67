from __future__ import annotations

from pathlib import Path

from runtime.contracts.models import VerificationRecord


def verify_file_written(path: Path, expected_size: int) -> VerificationRecord:
    exists = path.exists()
    observed_size = path.stat().st_size if exists else None
    status = "verified" if exists and observed_size == expected_size else "failed"
    return VerificationRecord(status=status, observed_state={"size": observed_size})
