from datetime import datetime

from agent.models import ActionResult, RiskTier, WorkflowRecipe, WorkflowStep, WorkflowVerification
from agent.personality import (
    KOLKATA_TZ,
    build_action_success_reply,
    build_action_failure_reply,
    build_boot_greeting,
    build_internal_error_reply,
    build_shutdown_farewell,
    build_task_cancelled_reply,
    build_telegram_start_message,
    build_tts_status_message,
    build_workflow_success_reply,
)


def test_build_boot_greeting_uses_morning_voice():
    greeting = build_boot_greeting(datetime(2026, 4, 27, 5, 0, tzinfo=KOLKATA_TZ))
    assert greeting.startswith("Good morning Buddy, I am now fully online and awake.")
    assert "Buddy" in greeting


def test_build_boot_greeting_uses_late_night_voice():
    greeting = build_boot_greeting(datetime(2026, 4, 27, 23, 30, tzinfo=KOLKATA_TZ))
    assert greeting.startswith("Hey wassup Buddy, I am now fully online and awake.")


def test_build_shutdown_farewell_uses_goodnight_at_late_night():
    farewell = build_shutdown_farewell(datetime(2026, 4, 27, 23, 45, tzinfo=KOLKATA_TZ))
    assert farewell.startswith("Bye Buddy, I'm shutting down.")
    assert "Goodnight" in farewell


def test_build_action_success_reply_is_natural_for_youtube_goal():
    reply = build_action_success_reply('open youtube in chrome and play "suave" video')
    assert "Task complete" not in reply
    assert "raw command" not in reply
    assert "played the video you wanted" in reply


def test_build_action_success_reply_uses_shutdown_farewell_for_shutdown_goal():
    reply = build_action_success_reply("Shutdown")
    assert reply.startswith("Bye Buddy, I'm shutting down.")


def test_build_action_success_reply_treats_whatsapp_message_goal_as_message_send():
    reply = build_action_success_reply("open whatsapp.web in chrome and search for the contact name Rajaa then message him Hii")
    assert "sent that message" in reply
    assert "opened whatsapp.web" not in reply.lower()


def test_build_workflow_success_reply_is_truthful_for_open_chat():
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

    reply = build_workflow_success_reply(
        recipe,
        ActionResult(status="success", summary="Opened chat with Rajaa in WhatsApp."),
    )

    assert "opened the chat with Rajaa in WhatsApp" in reply
    assert "opened whatsapp and search" not in reply.lower()


def test_build_action_failure_reply_avoids_robotic_completion_language():
    reply = build_action_failure_reply("open youtube and play suave")
    assert "Task failed" not in reply
    assert "open youtube and play suave" in reply


def test_telegram_start_message_feels_conversational():
    reply = build_telegram_start_message()
    assert "Awaiting commands" not in reply
    assert "Buddy" in reply


def test_tts_status_message_is_human():
    assert build_tts_status_message(True) == "Voice replies are on here now, Buddy."
    assert build_tts_status_message(False) == "Voice replies are off here now, Buddy."


def test_cancel_and_internal_error_replies_are_natural():
    assert build_task_cancelled_reply() == "All right, Buddy. I have stopped that task."
    assert "Something went wrong on my side" in build_internal_error_reply()
