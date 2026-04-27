from __future__ import annotations

import re
import uuid

from agent.models import RiskTier, WorkflowRecipe, WorkflowStep, WorkflowVerification


_MESSAGE_PLATFORMS = ("whatsapp", "telegram", "signal", "discord", "messenger")


def _platform_name(goal: str) -> str:
    lowered = goal.lower()
    if "telegram" in lowered:
        return "Telegram"
    if "signal" in lowered:
        return "Signal"
    if "discord" in lowered:
        return "Discord"
    if "messenger" in lowered or "facebook" in lowered:
        return "Messenger"
    return "WhatsApp"


def _extract_contact_name(goal: str) -> str:
    patterns = [
        r"contact name\s+([A-Za-z0-9_. -]+?)(?:\s+then|\s+and|\s*$)",
        r"contact\s+([A-Za-z0-9_. -]+?)(?:\s+then|\s+and|\s*$)",
        r"message\s+(?:him|her|them)\s+([A-Za-z0-9_. -]+?)(?:\s+then|\s+and|\s*$)",
        r"message\s+([A-Z][A-Za-z0-9_. -]+?)(?:\s+then|\s+and|\s+on|\s+via|\s*$)",
        r"for\s+contact\s+([A-Za-z0-9_. -]+?)(?:\s+then|\s+and|\s*$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, goal, re.IGNORECASE)
        if match:
            return match.group(1).strip(" .\"'")
    return ""


def _extract_message_text(goal: str) -> str:
    quoted = re.findall(r'"([^"]+)"', goal)
    if quoted:
        return quoted[-1].strip()

    match = re.search(
        r"\bmessage\s+(?:him|her|them|[A-Za-z0-9_. -]+)\s+(.+)$",
        goal,
        re.IGNORECASE,
    )
    if match:
        return match.group(1).strip(" \"'.")
    return ""


def _extract_app_name(goal: str) -> str:
    patterns = [
        r"(?:open|launch|start|run)\s+([a-zA-Z0-9 ._+-]+?)(?:\s+in\s+chrome|\s+as\s+admin|\s+as\s+administrator|$)",
        r"run\s+([a-zA-Z0-9 ._+-]+?)\s+as\s+admin",
    ]
    for pattern in patterns:
        match = re.search(pattern, goal, re.IGNORECASE)
        if match:
            app_name = match.group(1).strip(" .\"'")
            if app_name:
                return app_name
    return ""


def _extract_site_url(goal: str) -> str:
    lowered = goal.lower()
    if "whatsapp.web" in lowered:
        return "https://web.whatsapp.com/"
    match = re.search(r"\b([a-z0-9-]+\.(?:com|org|net|io|app|ai|dev|co))\b", lowered)
    if match:
        return f"https://{match.group(1)}"
    return ""


def _extract_device_name(goal: str) -> str:
    patterns = [
        r"device(?: named)?\s+([A-Za-z0-9 _.-]+)",
        r"connect(?: to)?\s+([A-Za-z0-9 _.-]+)\s+(?:via )?bluetooth",
        r"pair(?: with)?\s+([A-Za-z0-9 _.-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, goal, re.IGNORECASE)
        if match:
            return match.group(1).strip(" .\"'")
    return ""


def _derive_youtube_query(goal: str) -> str:
    quoted = re.findall(r'"([^"]+)"', goal)
    if quoted:
        return quoted[0].strip()

    lowered = goal.lower()
    for marker in ("play", "watch"):
        if marker in lowered:
            tail = goal[lowered.index(marker) + len(marker):].strip(" :.-")
            if tail:
                return tail.replace("video", "").strip(" \"'")
    return goal


def _recipe_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _tool_step(
    *,
    action: str,
    parameters: dict,
    verify_text: str,
    timeout: float = 15.0,
) -> WorkflowStep:
    return WorkflowStep(
        kind="tool",
        action=action,
        parameters=parameters,
        verify=WorkflowVerification(
            method="result_contains",
            target="summary",
            expected_state=verify_text,
        ),
        timeout=timeout,
    )


def _build_message_recipe(goal: str) -> WorkflowRecipe | None:
    if not any(platform in goal.lower() for platform in _MESSAGE_PLATFORMS):
        return None

    receiver = _extract_contact_name(goal)
    if not receiver:
        return None

    lowered = goal.lower()
    platform = _platform_name(goal)

    if "message" in lowered:
        message_text = _extract_message_text(goal)
        if not message_text:
            return None
        return WorkflowRecipe(
            recipe_id=_recipe_id("send_message"),
            intent_family="send_message",
            goal=goal,
            steps=[
                _tool_step(
                    action="send_message",
                    parameters={
                        "receiver": receiver,
                        "message_text": message_text,
                        "platform": platform,
                        "mode": "send",
                    },
                    verify_text="sent",
                    timeout=30.0,
                )
            ],
            requires_approval=True,
            approval_tool="send_message",
            approval_parameters={
                "receiver": receiver,
                "message_text": message_text,
                "platform": platform,
                "mode": "send",
            },
            risk_tier=RiskTier.TIER_1,
            success_reply_key="send_message",
            metadata={"platform": platform, "receiver": receiver, "message_text": message_text},
        )

    if any(token in lowered for token in ("open the chat", "open chat", "search for contact", "search contact", "find contact")):
        return WorkflowRecipe(
            recipe_id=_recipe_id("open_chat"),
            intent_family="open_chat",
            goal=goal,
            steps=[
                _tool_step(
                    action="send_message",
                    parameters={
                        "receiver": receiver,
                        "message_text": "",
                        "platform": platform,
                        "mode": "open_chat",
                    },
                    verify_text="opened chat",
                    timeout=25.0,
                )
            ],
            requires_approval=False,
            approval_tool="send_message",
            approval_parameters={
                "receiver": receiver,
                "message_text": "",
                "platform": platform,
                "mode": "open_chat",
            },
            risk_tier=RiskTier.TIER_1,
            success_reply_key="open_chat",
            metadata={"platform": platform, "receiver": receiver},
        )

    return None


def _build_youtube_recipe(goal: str) -> WorkflowRecipe | None:
    lowered = goal.lower()
    if "youtube" not in lowered or not any(token in lowered for token in ("play", "watch")):
        return None

    query = _derive_youtube_query(goal)
    return WorkflowRecipe(
        recipe_id=_recipe_id("youtube"),
        intent_family="youtube_play",
        goal=goal,
        steps=[
            _tool_step(
                action="youtube_video",
                parameters={"action": "play", "query": query},
                verify_text="opened",
                timeout=15.0,
            )
        ],
        requires_approval=False,
        approval_tool="youtube_video",
        approval_parameters={"action": "play", "query": query},
        risk_tier=RiskTier.TIER_1,
        success_reply_key="youtube_play",
        metadata={"query": query},
    )


def _build_volume_recipe(goal: str) -> WorkflowRecipe | None:
    lowered = goal.lower()
    if not any(token in lowered for token in ("volume", "mute", "unmute")):
        return None

    if "mute" in lowered or "unmute" in lowered:
        params = {"action": "volume_mute"}
        expected = "mute"
    else:
        value_match = re.search(r"(\d{1,3})\s*%", lowered)
        if value_match:
            value = max(0, min(100, int(value_match.group(1))))
            params = {"action": "volume_set", "value": str(value)}
            expected = "Volume set"
        elif any(token in lowered for token in ("increase", "up", "raise", "higher")):
            params = {"action": "volume_up"}
            expected = "Done"
        else:
            params = {"action": "volume_down"}
            expected = "Done"

    return WorkflowRecipe(
        recipe_id=_recipe_id("volume"),
        intent_family="volume_control",
        goal=goal,
        steps=[_tool_step(action="computer_settings", parameters=params, verify_text=expected)],
        requires_approval=False,
        approval_tool="computer_settings",
        approval_parameters=params,
        risk_tier=RiskTier.TIER_1,
        success_reply_key="volume_control",
        metadata=params,
    )


def _build_brightness_recipe(goal: str) -> WorkflowRecipe | None:
    lowered = goal.lower()
    if "brightness" not in lowered:
        return None

    if any(token in lowered for token in ("increase", "up", "raise", "higher")):
        params = {"action": "brightness_up"}
    else:
        params = {"action": "brightness_down"}

    return WorkflowRecipe(
        recipe_id=_recipe_id("brightness"),
        intent_family="brightness_control",
        goal=goal,
        steps=[_tool_step(action="computer_settings", parameters=params, verify_text="Done")],
        requires_approval=False,
        approval_tool="computer_settings",
        approval_parameters=params,
        risk_tier=RiskTier.TIER_1,
        success_reply_key="brightness_control",
        metadata=params,
    )


def _build_bluetooth_recipe(goal: str) -> WorkflowRecipe | None:
    lowered = goal.lower()
    if "bluetooth" not in lowered:
        return None

    if "pair" in lowered and "accept" in lowered:
        action = "accept_pairing"
    elif "pair" in lowered or "new device" in lowered:
        action = "pair_new"
    elif "connect" in lowered:
        action = "connect_saved"
    elif any(token in lowered for token in ("on", "off", "toggle")):
        action = "toggle"
    elif "settings" in lowered:
        action = "open_settings"
    else:
        action = "status"

    params = {"action": action, "device_name": _extract_device_name(goal)}
    expected = "Bluetooth" if action == "toggle" else "Opened" if action == "open_settings" else ""
    verify_text = expected or (params["device_name"] if params["device_name"] else "Bluetooth")

    return WorkflowRecipe(
        recipe_id=_recipe_id("bluetooth"),
        intent_family="bluetooth_control",
        goal=goal,
        steps=[_tool_step(action="bluetooth_manager", parameters=params, verify_text=verify_text, timeout=20.0)],
        requires_approval=action == "toggle",
        approval_tool="bluetooth_manager",
        approval_parameters=params,
        risk_tier=RiskTier.TIER_2 if action == "toggle" else RiskTier.TIER_1,
        success_reply_key="bluetooth_control",
        metadata=params,
    )


def _build_process_recipe(goal: str) -> WorkflowRecipe | None:
    lowered = goal.lower()
    if "task manager" in lowered:
        params = {"action": "task_manager"}
        return WorkflowRecipe(
            recipe_id=_recipe_id("task_manager"),
            intent_family="process_view",
            goal=goal,
            steps=[_tool_step(action="computer_settings", parameters=params, verify_text="Done")],
            requires_approval=False,
            approval_tool="computer_settings",
            approval_parameters=params,
            risk_tier=RiskTier.TIER_1,
            success_reply_key="task_manager",
            metadata=params,
        )

    if not any(token in lowered for token in ("process", "running app", "running apps")):
        return None

    action = "top" if any(token in lowered for token in ("top", "highest", "cpu", "memory")) else "list"
    params = {"action": action}
    if action == "top":
        params["sort_by"] = "cpu" if "cpu" in lowered else "memory"
    return WorkflowRecipe(
        recipe_id=_recipe_id("process"),
        intent_family="process_view",
        goal=goal,
        steps=[_tool_step(action="process_manager", parameters=params, verify_text="process")],
        requires_approval=False,
        approval_tool="process_manager",
        approval_parameters=params,
        risk_tier=RiskTier.TIER_1,
        success_reply_key="process_view",
        metadata=params,
    )


def _build_settings_recipe(goal: str) -> WorkflowRecipe | None:
    lowered = goal.lower()
    if "open settings" not in lowered and lowered.strip() != "settings":
        return None

    params = {"action": "open_settings"}
    return WorkflowRecipe(
        recipe_id=_recipe_id("settings"),
        intent_family="settings_open",
        goal=goal,
        steps=[_tool_step(action="computer_settings", parameters=params, verify_text="Done")],
        requires_approval=False,
        approval_tool="computer_settings",
        approval_parameters=params,
        risk_tier=RiskTier.TIER_1,
        success_reply_key="settings_open",
        metadata=params,
    )


def _build_browser_recipe(goal: str) -> WorkflowRecipe | None:
    lowered = goal.lower()
    if not re.search(r"\b(open|launch|start|run)\b", lowered):
        return None

    site_url = _extract_site_url(goal)
    if not site_url:
        return None

    params = {"action": "go_to", "url": site_url}
    return WorkflowRecipe(
        recipe_id=_recipe_id("browser"),
        intent_family="browser_open",
        goal=goal,
        steps=[_tool_step(action="browser_control", parameters=params, verify_text="Opened", timeout=20.0)],
        requires_approval=False,
        approval_tool="browser_control",
        approval_parameters=params,
        risk_tier=RiskTier.TIER_1,
        success_reply_key="browser_open",
        metadata=params,
    )


def _build_app_recipe(goal: str) -> WorkflowRecipe | None:
    lowered = goal.lower()
    if not re.search(r"\b(run|open|launch|start)\b", lowered):
        return None

    app_name = _extract_app_name(goal)
    if not app_name:
        return None

    run_as_admin = any(
        phrase in lowered
        for phrase in ("run as admin", "run as administrator", "as admin", "as administrator")
    )
    params = {"app_name": app_name, "run_as_admin": run_as_admin}
    return WorkflowRecipe(
        recipe_id=_recipe_id("open_app"),
        intent_family="open_app_admin" if run_as_admin else "open_app",
        goal=goal,
        steps=[_tool_step(action="open_app", parameters=params, verify_text="Opened", timeout=20.0)],
        requires_approval=run_as_admin,
        approval_tool="open_app",
        approval_parameters=params,
        risk_tier=RiskTier.TIER_3 if run_as_admin else RiskTier.TIER_1,
        success_reply_key="open_app_admin" if run_as_admin else "open_app",
        metadata=params,
    )


def match_workflow_recipe(goal: str) -> WorkflowRecipe | None:
    builders = (
        _build_message_recipe,
        _build_youtube_recipe,
        _build_volume_recipe,
        _build_brightness_recipe,
        _build_bluetooth_recipe,
        _build_process_recipe,
        _build_settings_recipe,
        _build_browser_recipe,
        _build_app_recipe,
    )
    for builder in builders:
        recipe = builder(goal)
        if recipe is not None:
            return recipe
    return None
