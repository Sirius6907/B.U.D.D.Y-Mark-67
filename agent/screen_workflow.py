from __future__ import annotations

from dataclasses import dataclass

from agent.executor import call_tool_structured
from agent.models import ActionResult, TaskNode, WorkflowRecipe, WorkflowStep


@dataclass(slots=True)
class WorkflowRunContext:
    completed_steps: int = 0
    last_result: ActionResult | None = None


def _node_from_step(recipe: WorkflowRecipe, step: WorkflowStep, index: int) -> TaskNode:
    return TaskNode(
        node_id=f"{recipe.recipe_id}:{index}",
        objective=f"{recipe.intent_family}:{step.action}",
        tool=step.action,
        parameters=step.parameters,
        expected_outcome=step.verify.expected_state if step.verify else "Step completes successfully",
        risk_tier=recipe.risk_tier,
    )


def _verify_step(step: WorkflowStep, result: ActionResult) -> tuple[bool, str]:
    if result.status != "success":
        return False, result.summary or "Workflow step failed."

    verify = step.verify
    if verify is None:
        return True, ""

    summary = (result.summary or "").lower()
    expected = str(verify.expected_state or "").lower()

    if verify.method == "result_contains":
        if expected and expected not in summary:
            return False, f"Verification failed for {step.action}: expected '{verify.expected_state}' in result."
        return True, ""

    if verify.method == "status_is":
        if expected and expected != result.status.lower():
            return False, f"Verification failed for {step.action}: expected status '{verify.expected_state}'."
        return True, ""

    return True, ""


def run_workflow(recipe: WorkflowRecipe, speak=None) -> ActionResult:
    context = WorkflowRunContext()
    last_error = ""
    resume_from = int(recipe.metadata.get("dp_resume_from_step", 0) or 0)

    for index, step in enumerate(recipe.steps, start=1):
        if step.kind != "tool":
            return ActionResult(
                status="error",
                summary=f"Unsupported workflow step kind: {step.kind}",
                retryable=False,
            )

        node = _node_from_step(recipe, step, index)
        result = call_tool_structured(node, speak=speak)
        context.last_result = result

        verified, verification_error = _verify_step(step, result)
        if not verified:
            last_error = verification_error or result.summary
            return ActionResult(
                status="error",
                summary=last_error,
                observations={
                    "recipe_id": recipe.recipe_id,
                    "intent_family": recipe.intent_family,
                    "failed_step": index,
                    "completed_steps": context.completed_steps,
                    "resume_from_step": resume_from,
                },
                retryable=result.retryable,
                error_message=last_error,
            )

        context.completed_steps += 1

    final_summary = context.last_result.summary if context.last_result else f"Workflow completed: {recipe.intent_family}"
    return ActionResult(
        status="success",
        summary=final_summary,
        observations={
            "recipe_id": recipe.recipe_id,
            "intent_family": recipe.intent_family,
            "completed_steps": context.completed_steps,
            "resume_from_step": resume_from,
        },
        changed_state=context.last_result.changed_state if context.last_result else {},
    )
