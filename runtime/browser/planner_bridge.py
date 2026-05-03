"""
runtime.browser.planner_bridge — Connect planner intent to capability selection.

Converts natural-language intents into quality-ranked tool selections
using the capability registry, alias resolution, and confidence scoring.

The planner bridge is the decision layer:
  intent → capability search → rank tools → attach confidence → return plan
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from registries.legacy_aliases import resolve_alias, is_legacy_name


@dataclass
class PlannedStep:
    """A single planned step with confidence and tool metadata."""
    tool_name: str
    parameters: dict[str, Any]
    confidence: float          # 0–1, planner's confidence in this step
    description: str = ""
    is_mutating: bool = True
    preconditions: list[str] = field(default_factory=list)
    expected_postconditions: list[str] = field(default_factory=list)
    # Quality metadata from registry
    reliability_score: float = 0.5
    maturity_level: str = "experimental"
    verification_supported: bool = False


@dataclass
class WorkflowPlan:
    """A complete plan produced by the planner bridge."""
    intent: str
    steps: list[PlannedStep]
    overall_confidence: float
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "intent": self.intent,
            "overall_confidence": self.overall_confidence,
            "step_count": len(self.steps),
            "steps": [
                {
                    "tool": s.tool_name,
                    "confidence": s.confidence,
                    "maturity": s.maturity_level,
                    "reliability": s.reliability_score,
                    "verified": s.verification_supported,
                    "description": s.description,
                }
                for s in self.steps
            ],
            "warnings": self.warnings,
        }


class PlannerBridge:
    """Bridges planner intent to workflow steps via capability registry.

    Resolution order for each tool reference:
    1. Legacy alias resolution
    2. Direct registry lookup
    3. Capability-based search (domain + operation)
    4. Quality ranking

    Confidence is computed per-step and rolled up to overall plan confidence.
    """

    # Minimum confidence to allow autonomous execution
    MIN_AUTONOMOUS_CONFIDENCE = 0.6
    # Confidence penalty for experimental tools
    EXPERIMENTAL_PENALTY = 0.15
    # Confidence bonus for verified tools
    VERIFIED_BONUS = 0.1

    def __init__(self, capability_registry: Any):
        self._registry = capability_registry

    def resolve_tool(self, tool_ref: str) -> tuple[str, float]:
        """Resolve a tool reference to its real name and base confidence.

        Returns (resolved_name, base_confidence).
        """
        # Step 1: Legacy alias resolution
        resolved = resolve_alias(tool_ref)
        was_alias = resolved != tool_ref

        # Step 2: Quality-aware registry lookup
        spec = self._registry.resolve_with_quality(resolved)

        if spec is not None:
            # Build confidence from quality metadata
            base = spec.reliability_score
            if spec.maturity_level == "experimental":
                base -= self.EXPERIMENTAL_PENALTY
            if spec.verification_supported:
                base += self.VERIFIED_BONUS
            # Alias resolution adds slight uncertainty
            if was_alias:
                base -= 0.05
            return spec.tool_name, max(0.0, min(1.0, base))

        # Tool not in registry — very low confidence
        return resolved, 0.2

    def plan_workflow(
        self,
        intent: str,
        raw_steps: list[dict[str, Any]],
    ) -> WorkflowPlan:
        """Convert raw step descriptions into a quality-ranked workflow plan.

        Each raw_step should have:
          - tool: str (tool name or alias)
          - parameters: dict
          - description: str (optional)
          - preconditions: list[str] (optional)
          - postconditions: list[str] (optional)
          - is_mutating: bool (optional, default True)
        """
        planned_steps: list[PlannedStep] = []
        warnings: list[str] = []

        for raw in raw_steps:
            tool_ref = raw["tool"]
            params = raw.get("parameters", {})

            # Resolve tool with quality scoring
            real_name, confidence = self.resolve_tool(tool_ref)

            # Look up full spec for metadata
            spec = self._registry.get(real_name)

            if spec is None:
                warnings.append(
                    f"Tool '{tool_ref}' resolved to '{real_name}' but not found in registry"
                )

            step = PlannedStep(
                tool_name=real_name,
                parameters=params,
                confidence=confidence,
                description=raw.get("description", ""),
                is_mutating=raw.get("is_mutating", True),
                preconditions=raw.get("preconditions", []),
                expected_postconditions=raw.get("postconditions", []),
                reliability_score=spec.reliability_score if spec else 0.0,
                maturity_level=spec.maturity_level if spec else "experimental",
                verification_supported=spec.verification_supported if spec else False,
            )
            planned_steps.append(step)

        # Overall confidence = geometric mean of step confidences
        if planned_steps:
            product = 1.0
            for s in planned_steps:
                product *= s.confidence
            overall = product ** (1.0 / len(planned_steps))
        else:
            overall = 0.0

        # Add warnings for low-confidence plans
        if overall < self.MIN_AUTONOMOUS_CONFIDENCE:
            warnings.append(
                f"Overall confidence {overall:.2f} is below autonomous threshold "
                f"({self.MIN_AUTONOMOUS_CONFIDENCE}). Human review recommended."
            )

        return WorkflowPlan(
            intent=intent,
            steps=planned_steps,
            overall_confidence=overall,
            warnings=warnings,
        )

    def should_execute_autonomously(self, plan: WorkflowPlan) -> bool:
        """Check if a plan has sufficient confidence for autonomous execution."""
        return plan.overall_confidence >= self.MIN_AUTONOMOUS_CONFIDENCE

    def find_alternatives(self, tool_name: str, domain: str) -> list[str]:
        """Find alternative tools in the same domain, ranked by quality."""
        specs = self._registry.find_by_capability(domain)
        return [s.tool_name for s in specs if s.tool_name != tool_name]
