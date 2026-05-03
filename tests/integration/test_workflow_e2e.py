"""
End-to-end workflow integration tests.

Validates the full plan → act → verify → adapt loop:
  - Correct tool sequence
  - Verification success
  - No infinite loops
  - Recovery triggers when needed
  - Alias resolution
  - Quality-ranked selection
"""

import pytest
from unittest.mock import MagicMock

from runtime.browser.workflow import (
    WorkflowExecutor,
    WorkflowStep,
    StepStatus,
    WorkflowStatus,
)
from runtime.browser.planner_bridge import PlannerBridge, PlannedStep
from runtime.browser.recovery import RecoveryPolicy
from registries.capability_registry import CapabilityRegistry, CapabilitySpec
from registries.legacy_aliases import resolve_alias, is_legacy_name


# ── Fixtures ──

@pytest.fixture
def registry():
    reg = CapabilityRegistry()
    reg.register(CapabilitySpec(
        tool_name="browser_nav_navigate_to_url", domain="browser_nav",
        operation="navigate", reliability_score=0.95,
        verification_supported=True, maturity_level="core", latency_class="fast",
    ))
    reg.register(CapabilitySpec(
        tool_name="browser_input_type_text", domain="browser_input",
        operation="type", reliability_score=0.9,
        verification_supported=True, maturity_level="core", latency_class="fast",
    ))
    reg.register(CapabilitySpec(
        tool_name="browser_dom_click_element", domain="browser_dom",
        operation="click", reliability_score=0.85,
        verification_supported=True, maturity_level="core", latency_class="fast",
    ))
    reg.register(CapabilitySpec(
        tool_name="browser_dom_click_by_text", domain="browser_dom",
        operation="click", reliability_score=0.8,
        verification_supported=True, maturity_level="stable", latency_class="fast",
    ))
    reg.register(CapabilitySpec(
        tool_name="browser_extract_get_title", domain="browser_extract",
        operation="get_title", reliability_score=0.95,
        verification_supported=False, maturity_level="core", latency_class="fast",
        idempotent=True,
    ))
    reg.register(CapabilitySpec(
        tool_name="browser_auth_login_with_credentials", domain="browser_auth",
        operation="login", reliability_score=0.7,
        verification_supported=True, maturity_level="stable", latency_class="medium",
    ))
    return reg


def mock_success_executor(tool_name, params):
    """Mock executor that always succeeds."""
    return {
        "status": "success",
        "tool_name": tool_name,
        "summary": f"Executed {tool_name}",
        "structured_data": {},
        "postconditions": ["browser_session_active", "page_loaded", "user_authenticated"],
    }


def mock_failing_then_success_executor():
    """Mock executor that fails twice then succeeds."""
    call_count = {"n": 0}
    def executor(tool_name, params):
        call_count["n"] += 1
        if call_count["n"] <= 2:
            return {"status": "error", "error": "timeout: element not found"}
        return {
            "status": "success",
            "tool_name": tool_name,
            "summary": f"Executed {tool_name} on attempt {call_count['n']}",
            "structured_data": {},
            "postconditions": ["page_loaded"],
        }
    return executor


# ── Workflow Executor Tests ──

class TestWorkflowExecutor:

    def test_happy_path_navigate_fill_submit_verify(self, registry):
        """End-to-end: navigate → fill → submit → verify."""
        steps = [
            WorkflowStep(
                tool_name="browser_nav_navigate_to_url",
                parameters={"url": "https://example.com/login"},
                description="Navigate to login page",
                is_mutating=True,
                expected_postconditions=["page_loaded"],
            ),
            WorkflowStep(
                tool_name="browser_input_type_text",
                parameters={"selector": "#email", "text": "user@test.com"},
                description="Fill email field",
                is_mutating=True,
                preconditions=["page_loaded"],
                expected_postconditions=["page_loaded"],
            ),
            WorkflowStep(
                tool_name="browser_dom_click_element",
                parameters={"selector": "#submit"},
                description="Click submit button",
                is_mutating=True,
                preconditions=["page_loaded"],
                expected_postconditions=["user_authenticated"],
            ),
            WorkflowStep(
                tool_name="browser_extract_get_title",
                parameters={},
                description="Verify page title after login",
                is_mutating=False,
            ),
        ]

        executor = WorkflowExecutor(
            tool_executor=mock_success_executor,
            recovery_policy=RecoveryPolicy(),
            capability_registry=registry,
        )
        state = executor.execute("login_workflow", steps)

        assert state.status == WorkflowStatus.COMPLETED
        assert state.completed_steps == 4
        assert state.failed_steps == 0
        assert len(state.results) == 4
        # All steps verified
        for r in state.results:
            assert r.status == StepStatus.SUCCESS

    def test_max_steps_enforced(self, registry):
        """Workflow exceeding max steps is rejected."""
        steps = [
            WorkflowStep(tool_name=f"tool_{i}", parameters={})
            for i in range(20)
        ]
        executor = WorkflowExecutor(
            tool_executor=mock_success_executor,
            max_steps=15,
        )
        with pytest.raises(ValueError, match="exceeding max"):
            executor.execute("too_long", steps)

    def test_recovery_triggers_on_failure(self, registry):
        """Recovery retries and succeeds on third attempt."""
        import unittest.mock

        steps = [
            WorkflowStep(
                tool_name="browser_dom_click_element",
                parameters={"selector": "#btn"},
                description="Click button",
                is_mutating=True,
                expected_postconditions=["page_loaded"],
            ),
        ]

        executor = WorkflowExecutor(
            tool_executor=mock_failing_then_success_executor(),
            recovery_policy=RecoveryPolicy(),
            capability_registry=registry,
            max_retries=3,
        )
        # Patch time.sleep to skip recovery waits in tests
        with unittest.mock.patch("time.sleep"):
            state = executor.execute("recovery_test", steps)

        assert state.status == WorkflowStatus.COMPLETED
        assert state.results[0].retry_count > 0

    def test_no_infinite_loops(self, registry):
        """Workflow with always-failing tool does not loop forever."""
        def always_fail(tool_name, params):
            return {"status": "error", "error": "permission denied"}

        steps = [
            WorkflowStep(
                tool_name="browser_dom_click_element",
                parameters={"selector": "#btn"},
                is_mutating=True,
            ),
        ]

        executor = WorkflowExecutor(
            tool_executor=always_fail,
            recovery_policy=RecoveryPolicy(),
            capability_registry=registry,
            max_retries=3,
        )
        state = executor.execute("no_loop_test", steps)

        assert state.status == WorkflowStatus.FAILED
        assert len(state.results) == 1  # Exactly 1 step attempted

    def test_precondition_failure_blocks_step(self, registry):
        """Step with unmet preconditions fails immediately."""
        steps = [
            WorkflowStep(
                tool_name="browser_input_type_text",
                parameters={"selector": "#email", "text": "test"},
                preconditions=["login_page_visible"],  # Never achieved
                is_mutating=True,
            ),
        ]

        executor = WorkflowExecutor(
            tool_executor=mock_success_executor,
        )
        state = executor.execute("precon_test", steps)

        assert state.status == WorkflowStatus.FAILED
        assert state.results[0].error == "Precondition validation failed"

    def test_mutating_tool_requires_verification(self, registry):
        """Mutating tool without matching postconditions fails verification."""
        def partial_success(tool_name, params):
            return {
                "status": "success",
                "postconditions": ["something_else"],  # Not what was expected
            }

        steps = [
            WorkflowStep(
                tool_name="browser_dom_click_element",
                parameters={"selector": "#btn"},
                is_mutating=True,
                expected_postconditions=["user_authenticated"],
            ),
        ]

        executor = WorkflowExecutor(tool_executor=partial_success)
        state = executor.execute("verify_test", steps)

        assert state.status == WorkflowStatus.FAILED
        assert "verification failed" in state.results[0].error.lower()

    def test_read_only_step_skips_verification(self, registry):
        """Non-mutating tools pass without postcondition checks."""
        steps = [
            WorkflowStep(
                tool_name="browser_extract_get_title",
                parameters={},
                is_mutating=False,
            ),
        ]

        executor = WorkflowExecutor(tool_executor=mock_success_executor)
        state = executor.execute("readonly_test", steps)

        assert state.status == WorkflowStatus.COMPLETED
        assert state.results[0].verified is True

    def test_workflow_state_dict(self, registry):
        """Workflow state serializes to structured dict."""
        steps = [
            WorkflowStep(tool_name="browser_nav_navigate_to_url", parameters={"url": "https://x.com"}),
        ]
        executor = WorkflowExecutor(tool_executor=mock_success_executor)
        state = executor.execute("serial_test", steps)

        d = state.to_dict()
        assert d["status"] == "completed"
        assert d["completed_steps"] == 1
        assert len(d["results"]) == 1


# ── Planner Bridge Tests ──

class TestPlannerBridge:

    def test_alias_resolution(self, registry):
        """Legacy alias is resolved to real tool name."""
        bridge = PlannerBridge(registry)
        real_name, confidence = bridge.resolve_tool("navigate_to_url")
        assert real_name == "browser_nav_navigate_to_url"
        assert confidence > 0.5

    def test_direct_tool_resolution(self, registry):
        """Real tool name resolves directly with high confidence."""
        bridge = PlannerBridge(registry)
        real_name, confidence = bridge.resolve_tool("browser_nav_navigate_to_url")
        assert real_name == "browser_nav_navigate_to_url"
        assert confidence >= 0.85

    def test_unknown_tool_low_confidence(self, registry):
        """Unknown tool gets very low confidence."""
        bridge = PlannerBridge(registry)
        real_name, confidence = bridge.resolve_tool("totally_fake_tool")
        assert confidence <= 0.3

    def test_plan_workflow_produces_ranked_steps(self, registry):
        """Plan workflow produces steps with confidence and quality metadata."""
        bridge = PlannerBridge(registry)
        raw_steps = [
            {"tool": "navigate_to_url", "parameters": {"url": "https://x.com"}},
            {"tool": "browser_input_type_text", "parameters": {"selector": "#q", "text": "hello"}},
        ]
        plan = bridge.plan_workflow("Search for hello", raw_steps)

        assert len(plan.steps) == 2
        assert plan.overall_confidence > 0.0
        # First step should be resolved from alias
        assert plan.steps[0].tool_name == "browser_nav_navigate_to_url"

    def test_low_confidence_plan_warns(self, registry):
        """Plan with unknown tools gets warning about autonomous threshold."""
        bridge = PlannerBridge(registry)
        raw_steps = [
            {"tool": "unknown_tool_1", "parameters": {}},
            {"tool": "unknown_tool_2", "parameters": {}},
        ]
        plan = bridge.plan_workflow("Do something risky", raw_steps)

        assert plan.overall_confidence < bridge.MIN_AUTONOMOUS_CONFIDENCE
        assert any("autonomous threshold" in w for w in plan.warnings)
        assert not bridge.should_execute_autonomously(plan)

    def test_high_confidence_plan_allows_autonomous(self, registry):
        """Plan with all core tools allows autonomous execution."""
        bridge = PlannerBridge(registry)
        raw_steps = [
            {"tool": "browser_nav_navigate_to_url", "parameters": {"url": "https://x.com"}},
            {"tool": "browser_extract_get_title", "parameters": {}},
        ]
        plan = bridge.plan_workflow("Get page title", raw_steps)

        assert plan.overall_confidence >= bridge.MIN_AUTONOMOUS_CONFIDENCE
        assert bridge.should_execute_autonomously(plan)


# ── Alias Resolution Tests ──

class TestLegacyAliases:

    def test_stub_names_resolve(self):
        """All browser_*_tool_N names resolve to real names."""
        for n in range(1, 6):
            alias = f"browser_nav_tool_{n}"
            resolved = resolve_alias(alias)
            assert resolved.startswith("browser_nav_")
            assert "tool_" not in resolved

    def test_shorthand_names_resolve(self):
        """Common shorthand names resolve correctly."""
        assert resolve_alias("click") == "browser_dom_click_element"
        assert resolve_alias("login") == "browser_auth_login_with_credentials"
        assert resolve_alias("screenshot") == "browser_extract_screenshot"
        assert resolve_alias("refresh") == "browser_nav_refresh_page"

    def test_real_names_passthrough(self):
        """Real namespaced names pass through unchanged."""
        assert resolve_alias("browser_nav_navigate_to_url") == "browser_nav_navigate_to_url"

    def test_is_legacy_name(self):
        """Legacy detection works."""
        assert is_legacy_name("click") is True
        assert is_legacy_name("browser_nav_navigate_to_url") is False


# ── Quality Ranking Tests ──

class TestQualityRanking:

    def test_core_preferred_over_experimental(self, registry):
        """Core tools rank above experimental tools."""
        specs = registry.find_by_capability("browser_dom", "click")
        assert len(specs) >= 2
        # Core should be first
        assert specs[0].maturity_level == "core"

    def test_verified_preferred_over_unverified(self, registry):
        """Verified tools rank above unverified at same maturity."""
        reg = CapabilityRegistry()
        reg.register(CapabilitySpec(
            tool_name="tool_a", domain="test", operation="op",
            reliability_score=0.8, verification_supported=True,
            maturity_level="stable",
        ))
        reg.register(CapabilitySpec(
            tool_name="tool_b", domain="test", operation="op",
            reliability_score=0.8, verification_supported=False,
            maturity_level="stable",
        ))
        ranked = reg.find_by_capability("test", "op")
        assert ranked[0].tool_name == "tool_a"  # Verified first

    def test_higher_reliability_preferred(self, registry):
        """Higher reliability scores rank first at same maturity."""
        reg = CapabilityRegistry()
        reg.register(CapabilitySpec(
            tool_name="low_rel", domain="test", operation="op",
            reliability_score=0.3, maturity_level="stable",
        ))
        reg.register(CapabilitySpec(
            tool_name="high_rel", domain="test", operation="op",
            reliability_score=0.9, maturity_level="stable",
        ))
        ranked = reg.find_by_capability("test", "op")
        assert ranked[0].tool_name == "high_rel"
