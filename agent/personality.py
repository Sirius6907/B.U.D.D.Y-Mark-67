from __future__ import annotations

from datetime import datetime
from random import choice
from zoneinfo import ZoneInfo

from agent.models import ActionResult, WorkflowRecipe

KOLKATA_TZ = ZoneInfo("Asia/Kolkata")

_BOOT_COMMENTS = {
    "morning": [
        "By the way, what pulled you out this early, and what are we building first?",
        "You woke me up bright and early, Buddy. What mission are we running first?",
        "That is an early start, Buddy. Tell me what you want handled first.",
    ],
    "afternoon": [
        "I am locked in and ready, Buddy. What are we taking care of this afternoon?",
        "Perfect timing, Buddy. What do you want me to handle for you right now?",
        "I am with you, Buddy. Tell me what deserves our focus this afternoon.",
    ],
    "evening": [
        "Nice to see you, Buddy. What are we getting done this evening?",
        "Evening shift is live, Buddy. What do you want me to take care of?",
        "I am here and tuned in, Buddy. What is tonight's first move?",
    ],
    "late_night": [
        "You have me up late, Buddy. What are we diving into tonight?",
        "Late-night mode is active, Buddy. What do you want me to handle?",
        "I am awake with you, Buddy. What is the move tonight?",
    ],
}

_SHUTDOWN_COMMENTS = {
    "day": [
        "Call me whenever you need me again, Buddy.",
        "Rest easy, Buddy. I will be ready when you bring me back.",
        "All right, Buddy. I will be here when you need another hand.",
    ],
    "late_night": [
        "Goodnight, Buddy. Sleep tight and get some proper rest.",
        "Goodnight, Buddy. Sleep tight and recharge for tomorrow.",
        "Goodnight, Buddy. Get some rest and I will see you soon.",
    ],
}


def kolkata_now() -> datetime:
    return datetime.now(KOLKATA_TZ)


def _time_bucket(now: datetime) -> str:
    hour = now.hour
    if hour >= 23 or hour < 5:
        return "late_night"
    if hour < 12:
        return "morning"
    if hour < 17:
        return "afternoon"
    return "evening"


def build_boot_greeting(now: datetime | None = None) -> str:
    current = now.astimezone(KOLKATA_TZ) if now else kolkata_now()
    bucket = _time_bucket(current)
    if bucket == "late_night":
        intro = "Hey wassup Buddy, I am now fully online and awake."
    elif bucket == "morning":
        intro = "Good morning Buddy, I am now fully online and awake."
    elif bucket == "afternoon":
        intro = "Good afternoon Buddy, I am now fully online and awake."
    else:
        intro = "Good evening Buddy, I am now fully online and awake."
    return f"{intro} {choice(_BOOT_COMMENTS[bucket])}"


def build_shutdown_farewell(now: datetime | None = None) -> str:
    current = now.astimezone(KOLKATA_TZ) if now else kolkata_now()
    bucket = _time_bucket(current)
    intro = "Bye Buddy, I'm shutting down."
    comment_bucket = "late_night" if bucket == "late_night" else "day"
    return f"{intro} {choice(_SHUTDOWN_COMMENTS[comment_bucket])}"


def build_action_success_reply(goal: str) -> str:
    normalized = " ".join(goal.strip().split())
    lowered = normalized.lower()

    if lowered in {
        "shutdown",
        "shut down",
        "shutdown buddy",
        "buddy shutdown",
        "close buddy",
        "stop buddy",
        "exit buddy",
        "turn yourself off",
    }:
        return build_shutdown_farewell()
    if "message " in lowered and any(platform in lowered for platform in ("whatsapp", "telegram", "signal", "discord", "messenger")):
        return "I have sent that message for you, Buddy. Anything else you want me to do?"
    if "youtube" in lowered and "play" in lowered:
        return "I have opened YouTube and played the video you wanted, Buddy. Anything else you want me to do?"
    if lowered.startswith("open "):
        subject = normalized[5:].strip().rstrip(".")
        if subject:
            return f"I have opened {subject} for you, Buddy. Anything else you want me to do?"
    if "send" in lowered and "message" in lowered:
        return "I have sent that message for you, Buddy. Anything else you want me to do?"
    if "remind" in lowered or "reminder" in lowered:
        return "I have set that reminder for you, Buddy. Anything else you want me to do?"
    if "search" in lowered or "find" in lowered:
        return "I have handled that search for you, Buddy. Anything else you want me to do?"
    if "play" in lowered:
        return "I have started that for you, Buddy. Anything else you want me to do?"
    return "I have finished that for you, Buddy. Anything else you want me to do?"


def build_action_failure_reply(goal: str) -> str:
    normalized = " ".join(goal.strip().split())
    if normalized:
        return f"I could not finish that cleanly yet, Buddy. I need another pass on {normalized}."
    return "I could not finish that cleanly yet, Buddy. Give me a moment and I can try another approach."


def build_workflow_success_reply(recipe: WorkflowRecipe, result: ActionResult) -> str:
    intent = recipe.intent_family
    metadata = recipe.metadata or {}

    if intent == "open_chat":
        receiver = metadata.get("receiver", "that contact")
        platform = metadata.get("platform", "the app")
        return f"I have opened the chat with {receiver} in {platform} for you, Buddy. Anything else you want me to do?"
    if intent == "send_message":
        return "I have sent that message for you, Buddy. Anything else you want me to do?"
    if intent == "youtube_play":
        return "I have opened YouTube and started that for you, Buddy. Anything else you want me to do?"
    if intent == "open_app":
        app_name = metadata.get("app_name", "that app")
        return f"I have opened {app_name} for you, Buddy. Anything else you want me to do?"
    if intent == "open_app_admin":
        app_name = metadata.get("app_name", "that app")
        return f"I have opened {app_name} as administrator for you, Buddy. Anything else you want me to do?"
    if intent == "browser_open":
        return "I have opened that site for you, Buddy. Anything else you want me to do?"
    if intent == "volume_control":
        return "I have adjusted the volume for you, Buddy. Anything else you want me to do?"
    if intent == "brightness_control":
        return "I have adjusted the brightness for you, Buddy. Anything else you want me to do?"
    if intent == "bluetooth_control":
        return "I have handled the Bluetooth request for you, Buddy. Anything else you want me to do?"
    if intent == "process_view":
        return "I have pulled that process view for you, Buddy. Anything else you want me to do?"
    if intent == "task_manager":
        return "I have opened Task Manager for you, Buddy. Anything else you want me to do?"
    if intent == "settings_open":
        return "I have opened Settings for you, Buddy. Anything else you want me to do?"
    return build_action_success_reply(recipe.goal)


def build_workflow_failure_reply(recipe: WorkflowRecipe, result: ActionResult) -> str:
    base = result.summary.strip() if result.summary else ""
    if base:
        return f"I could not complete that cleanly yet, Buddy. {base}"
    return build_action_failure_reply(recipe.goal)


def build_planning_failure_reply() -> str:
    return "I could not map that out properly yet, Buddy. Give me a clearer angle and I will take another pass."


def build_internal_error_reply() -> str:
    return "Something went wrong on my side, Buddy. Give me a second and try that again."


def build_tool_error_reply(tool_name: str, error: str) -> str:
    short = " ".join(str(error).strip().split())[:120]
    if short:
        return f"I hit a problem while using {tool_name}, Buddy. {short}"
    return f"I hit a problem while using {tool_name}, Buddy."


def build_task_cancelled_reply() -> str:
    return "All right, Buddy. I have stopped that task."


def build_task_aborted_reply(reason: str = "") -> str:
    clean_reason = " ".join(reason.strip().split())
    if clean_reason:
        return f"I had to stop that run, Buddy. {clean_reason}"
    return "I had to stop that run, Buddy."


def build_task_retry_reply() -> str:
    return "Give me a second, Buddy. I am adjusting my approach."


def build_task_failed_reply() -> str:
    return "I could not get that across the finish line yet, Buddy. I need a different approach."


def build_telegram_start_message() -> str:
    return "I am here with you, Buddy. Send me a task any time, and use /tts on if you want voice replies here."


def build_tts_status_message(enabled: bool | None = None) -> str:
    if enabled is None:
        return "Tell me if you want voice replies here. You can use /tts on or /tts off."
    if enabled:
        return "Voice replies are on here now, Buddy."
    return "Voice replies are off here now, Buddy."


def build_tts_usage_message() -> str:
    return "Use /tts on or /tts off, Buddy."
