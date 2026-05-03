from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ToolMetrics:
    calls: int = 0
    errors: int = 0
    verification_failures: int = 0
    total_latency_ms: float = 0.0
