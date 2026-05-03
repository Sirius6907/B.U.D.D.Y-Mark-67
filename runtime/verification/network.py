from __future__ import annotations

from runtime.contracts.models import VerificationRecord


def verify_reachability(hostname: str, reachable: bool) -> VerificationRecord:
    status = "verified" if reachable else "failed"
    return VerificationRecord(status=status, observed_state={"hostname": hostname, "reachable": reachable})
