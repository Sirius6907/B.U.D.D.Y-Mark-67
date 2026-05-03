from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TypedDict


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class VerificationStatus(str, Enum):
    NOT_APPLICABLE = "not_applicable"


@dataclass
class VerificationRecord:
    status: VerificationStatus = VerificationStatus.NOT_APPLICABLE
    observed_state: dict[str, Any] = field(default_factory=dict)


class VerificationRecordData(TypedDict):
    status: VerificationStatus
    observed_state: dict[str, Any]


class ToolResult(TypedDict):
    tool_name: str
    operation: str
    risk_level: RiskLevel
    status: str
    summary: str
    structured_data: dict[str, Any]
    idempotent: bool
    preconditions: list[str]
    postconditions: list[str]
    verification: VerificationRecordData
