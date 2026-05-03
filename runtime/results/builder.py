from __future__ import annotations

from typing import Any

from runtime.contracts.models import (
    RiskLevel,
    ToolResult,
    VerificationRecordData,
    VerificationStatus,
)


def build_tool_result(
    *,
    tool_name: str,
    operation: str,
    risk_level: RiskLevel,
    status: str,
    summary: str,
    structured_data: dict[str, Any],
    idempotent: bool = False,
    preconditions: list[str] | None = None,
    postconditions: list[str] | None = None,
) -> ToolResult:
    verification: VerificationRecordData = {
        "status": VerificationStatus.NOT_APPLICABLE,
        "observed_state": {},
    }
    return ToolResult(
        tool_name=tool_name,
        operation=operation,
        risk_level=risk_level,
        status=status,
        summary=summary,
        structured_data=structured_data,
        idempotent=idempotent,
        preconditions=list(preconditions or []),
        postconditions=list(postconditions or []),
        verification=verification,
    )
