from __future__ import annotations

from runtime.contracts.models import VerificationRecord


def verify_process_running(pid: int, is_running: bool) -> VerificationRecord:
    status = "verified" if is_running else "failed"
    return VerificationRecord(status=status, observed_state={"pid": pid, "is_running": is_running})
