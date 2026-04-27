from agent.models import ActionResult, RiskTier, WorkflowRecipe, WorkflowStep, WorkflowVerification
from agent.screen_workflow import run_workflow


def test_run_workflow_maps_verification_failure_to_error(monkeypatch):
    monkeypatch.setattr(
        "agent.screen_workflow.call_tool_structured",
        lambda node, speak=None: ActionResult(status="success", summary="Opened WhatsApp."),
    )

    recipe = WorkflowRecipe(
        recipe_id="open_chat_test",
        intent_family="open_chat",
        goal="open whatsapp and search for contact Rajaa and open the chat",
        steps=[
            WorkflowStep(
                kind="tool",
                action="send_message",
                parameters={"receiver": "Rajaa", "platform": "WhatsApp", "mode": "open_chat"},
                verify=WorkflowVerification(
                    method="result_contains",
                    target="summary",
                    expected_state="opened chat",
                ),
            )
        ],
        requires_approval=False,
        risk_tier=RiskTier.TIER_1,
        success_reply_key="open_chat",
    )

    result = run_workflow(recipe)
    assert result.status == "error"
    assert "Verification failed" in result.summary


def test_run_workflow_succeeds_for_verified_step(monkeypatch):
    monkeypatch.setattr(
        "agent.screen_workflow.call_tool_structured",
        lambda node, speak=None: ActionResult(status="success", summary="Opened chat with Rajaa in WhatsApp."),
    )

    recipe = WorkflowRecipe(
        recipe_id="open_chat_test",
        intent_family="open_chat",
        goal="open whatsapp and search for contact Rajaa and open the chat",
        steps=[
            WorkflowStep(
                kind="tool",
                action="send_message",
                parameters={"receiver": "Rajaa", "platform": "WhatsApp", "mode": "open_chat"},
                verify=WorkflowVerification(
                    method="result_contains",
                    target="summary",
                    expected_state="opened chat",
                ),
            )
        ],
        requires_approval=False,
        risk_tier=RiskTier.TIER_1,
        success_reply_key="open_chat",
    )

    result = run_workflow(recipe)
    assert result.status == "success"
