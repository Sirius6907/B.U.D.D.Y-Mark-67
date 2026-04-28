from __future__ import annotations

import time

from agent.models import ActionResult, RiskTier, TaskNode
from agent.runtime import AgentRuntime


class _RetryExecutor:
    def __init__(self):
        self.calls = 0

    def execute_node(self, node):
        self.calls += 1
        if self.calls < 3:
            return ActionResult(status="error", summary="timeout contacting app", retryable=True)
        return ActionResult(status="success", summary="done")


class _TimeoutExecutor:
    def execute_node(self, node):
        time.sleep(0.2)
        return ActionResult(status="success", summary="finished too late")


def test_runtime_retries_retryable_failures_until_success():
    runtime = AgentRuntime(executor=_RetryExecutor())
    node = TaskNode(
        node_id="step-1",
        objective="Retry flaky step",
        tool="open_app",
        parameters={"app_name": "Chrome"},
        expected_outcome="Chrome opens",
        risk_tier=RiskTier.TIER_1,
        retry_limit=3,
    )

    results = runtime.run([node], goal="Open Chrome")

    assert len(results) == 1
    assert results[0].status == "success"


def test_runtime_enforces_node_timeout():
    runtime = AgentRuntime(executor=_TimeoutExecutor())
    node = TaskNode(
        node_id="step-1",
        objective="Slow step",
        tool="open_app",
        parameters={"app_name": "Chrome"},
        expected_outcome="Chrome opens",
        risk_tier=RiskTier.TIER_1,
        timeout=0.05,
    )

    results = runtime.run([node], goal="Open Chrome slowly")

    assert results[-1].status == "error"
    assert "timed out" in results[-1].summary.lower()
