import asyncio

from agent.models import ActionResult, RiskTier, WorkflowRecipe, WorkflowStep, WorkflowVerification
from agent.voice import VoiceOrchestrator


def test_voice_orchestrator_can_interrupt_active_response():
    orchestrator = VoiceOrchestrator()
    orchestrator.start_response("Working on it")
    assert orchestrator.is_speaking is True
    orchestrator.interrupt()
    assert orchestrator.is_speaking is False


def test_voice_orchestrator_uses_workflow_recipe_before_planner(monkeypatch):
    spoken = []
    orchestrator = VoiceOrchestrator(speak_fn=spoken.append)

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
        metadata={"receiver": "Rajaa", "platform": "WhatsApp"},
    )

    monkeypatch.setattr("agent.voice.match_workflow_recipe", lambda text: recipe)
    monkeypatch.setattr("agent.voice.create_plan", lambda text: (_ for _ in ()).throw(AssertionError("planner should be bypassed")))
    monkeypatch.setattr("agent.voice.run_workflow", lambda recipe, speak=None: ActionResult(status="success", summary="Opened chat with Rajaa in WhatsApp."))
    monkeypatch.setattr(orchestrator, "_classify_intent", lambda text: "action")
    monkeypatch.setattr(orchestrator.runtime, "execute_workflow", lambda recipe, runner: asyncio.sleep(0, result=ActionResult(status="success", summary="Opened chat with Rajaa in WhatsApp.")))

    asyncio.run(orchestrator.handle_user_command("open whatsapp and search for contact Rajaa and open the chat"))

    assert spoken
    assert "opened the chat with Rajaa in WhatsApp" in spoken[-1]
