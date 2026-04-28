"""
agent/planner.py — OPEV Task Planner
=====================================
Decomposes user goals into structured, risk-tiered execution plans
using the Gemini API. Includes replanning for error recovery.

Architecture:
    create_plan()  → TaskPlan from user goal
    replan()       → Revised TaskPlan after step failure
    normalize_plan → Legacy dict → TaskNode converter
"""
from __future__ import annotations

import json
import re
import sys
import uuid
from pathlib import Path

from buddy_logging import get_logger
from config import get_api_key
from agent.models import TaskPlan, TaskNode, RiskTier

logger = get_logger("agent.planner")


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = get_base_dir()


# ── Risk Classification ──────────────────────────────────────────────────────

TOOL_RISK_MAP: dict[str, RiskTier] = {
    "screen_process": RiskTier.TIER_0,
    "web_search": RiskTier.TIER_0,
    "weather_report": RiskTier.TIER_0,
    "open_app": RiskTier.TIER_1,
    "browser_control": RiskTier.TIER_1,
    "youtube_video": RiskTier.TIER_1,
    "process_manager": RiskTier.TIER_1,
    "bluetooth_manager": RiskTier.TIER_1,
    "hardware_diagnostics": RiskTier.TIER_1,
    "app_optimizer": RiskTier.TIER_1,
    "file_controller": RiskTier.TIER_2,
    "computer_control": RiskTier.TIER_2,
    "computer_settings": RiskTier.TIER_2,
    "desktop_control": RiskTier.TIER_2,
    "reminder": RiskTier.TIER_2,
    "antivirus_manager": RiskTier.TIER_2,
    "security_auditor": RiskTier.TIER_2,
    "screen_recorder": RiskTier.TIER_2,
    "access_monitor": RiskTier.TIER_2,
    "network_security": RiskTier.TIER_2,
    "process_shield": RiskTier.TIER_2,
    "maintenance_manager": RiskTier.TIER_2,
    "backup_manager": RiskTier.TIER_2,
    "send_message": RiskTier.TIER_1,
    "firewall_manager": RiskTier.TIER_3,
    "privacy_manager": RiskTier.TIER_3,
    "software_manager": RiskTier.TIER_3,
    "recovery_manager": RiskTier.TIER_3,
    "vault_manager": RiskTier.TIER_3,
    "privacy_hardener": RiskTier.TIER_3,
}


# ── System Prompt ─────────────────────────────────────────────────────────────

PLANNER_PROMPT = """You are the planning module of BUDDY MARK LXVII, a personal AI assistant.
Your job: break any user goal into a sequence of steps using ONLY the tools listed below.

ABSOLUTE RULES:
- NEVER use generated_code or write Python scripts. It does not exist.
- NEVER reference previous step results in parameters. Every step is independent.
- Use web_search for ANY information retrieval, research, or current data.
- Use file_controller to save content to disk.
- For security modules (firewall, antivirus, security_auditor, privacy), ONLY use them if the user EXPLICITLY asks for a scan, security check, or privacy sweep. Do NOT use them proactively.
- Max 5 steps. Use the minimum steps needed.

AVAILABLE TOOLS AND THEIR PARAMETERS:

open_app
  app_name: string (required)
  run_as_admin: boolean (optional, default: false)

web_search
  query: string (required) — write a clear, focused search query
  mode: "search" or "compare" (optional, default: search)
  items: list of strings (optional, for compare mode)
  aspect: string (optional, for compare mode)

game_updater
  action: "update" | "install" | "list" | "download_status" | "schedule" (required)
  platform: "steam" | "epic" | "both" (optional, default: both)
  game_name: string (optional)
  app_id: string (optional)
  shutdown_when_done: boolean (optional)

browser_control
  action: "go_to" | "search" | "click" | "type" | "scroll" | "get_text" | "press" | "close" (required)
  url: string (for go_to)
  query: string (for search)
  text: string (for click/type)
  direction: "up" | "down" (for scroll)

file_controller
  action: "write" | "create_file" | "read" | "list" | "delete" | "move" | "copy" | "find" | "disk_usage" (required)
  path: string — use "desktop" for Desktop folder
  name: string — filename
  content: string — file content (for write/create_file)

computer_settings
  action: string (required)
  description: string — natural language description
  value: string (optional)

computer_control
  action: "type" | "click" | "hotkey" | "press" | "scroll" | "screenshot" | "screen_find" | "screen_click" (required)
  text: string (for type)
  x, y: int (for click)
  keys: string (for hotkey, e.g. "ctrl+c")
  key: string (for press)
  direction: "up" | "down" (for scroll)
  description: string (for screen_find/screen_click)

screen_process
  text: string (required) — what to analyze or ask about the screen
  angle: "screen" | "camera" (optional)

send_message
  receiver: string (required)
  message_text: string (required)
  platform: string (required)

process_manager
  action: "list" | "info" | "kill_safe" | "top" (required)
  name: string (optional)
  count: string (optional)
  sort_by: "cpu" | "memory" (optional)

bluetooth_manager
  action: "status" | "open_settings" | "toggle" | "connect_saved" | "pair_new" | "accept_pairing" (required)
  device_name: string (optional)

reminder
  date: string YYYY-MM-DD (required)
  time: string HH:MM (required)
  message: string (required)

desktop_control
  action: "wallpaper" | "organize" | "clean" | "list" | "task" (required)
  path: string (optional)
  task: string (optional)

youtube_video
  action: "play" | "summarize" | "trending" (required)
  query: string (for play)

weather_report
  city: string (required)

flight_finder
  origin: string (required)
  destination: string (required)
  date: string (required)

code_helper
  action: "write" | "edit" | "run" | "explain" (required)
  description: string (required)
  language: string (optional)
  output_path: string (optional)
  file_path: string (optional)

local_task
  prompt: string (required)
  mode: "fast" | "deep" (optional, default: fast)

dev_agent
  description: string (required)
  language: string (optional)

firewall_manager
  action: "status" | "enable" | "disable" | "block_ip" | "block_app" | "lockdown" | "stealth_mode" (required)
  ip: string (optional)
  app_path: string (optional)

antivirus_manager
  action: "status" | "quick_scan" | "full_scan" | "update_signatures" (required)

security_auditor
  action: "full_audit" | "check_remote_access" | "check_startup" (required)

privacy_manager
  action: "clear_all" | "empty_recycle_bin" | "clear_temp_files" | "clear_browser_cache" (required)

software_manager
  action: "list_installed" | "uninstall" (required)
  name: string (optional)

screen_recorder
  action: "start" | "stop" | "configure" (required)
  duration: integer (optional)
  resolution: string (optional, e.g., "1080p", "4k")
  fps: integer (optional, e.g., 60, 120)
  bitrate: integer (optional)
  audio_source: "system" | "system_and_mic" (optional)

access_monitor
  action: "rdp_status" | "login_history" | "active_shares" | "check_all" (required)

network_security
  action: "ports" | "bandwidth" | "wifi_audit" | "check_all" (required)

process_shield
  action: "monitor" | "kill_rogue" | "top_cpu" | "top_mem" (required)

maintenance_manager
  action: "clean_temp" | "empty_bin" | "disk_report" | "optimize_all" (required)

hardware_diagnostics
  action: "cpu" | "ram" | "gpu" | "battery" | "full_report" (required)

recovery_manager
  action: "check_updates" | "create_restore_point" | "system_health" (required)

app_optimizer
  action: "high_priority" | "low_priority" | "power_scheme" (required)
  app_name: string (optional)
  scheme: "balanced" | "performance" | "power_saver" (optional)

backup_manager
  action: "backup_folder" | "zip_files" | "list_backups" (required)
  source_path: string (optional)
  dest_path: string (optional)

vault_manager
  action: "encrypt" | "decrypt" | "status" (required)
  file_path: string (optional)

privacy_hardener
  action: "disable_telemetry" | "disable_ads" | "hardening_sweep" (required)

EXAMPLES:

Goal: "research mechanical engineering and save it to a notepad file"
Steps:

web_search | query: "mechanical engineering overview definition history"
web_search | query: "mechanical engineering applications and future trends"
file_controller | action: write, path: desktop, name: mechanical_engineering.txt, content: "MECHANICAL ENGINEERING RESEARCH\\n\\nThis file will be filled with web research results."

Goal: "What is the price of Bitcoin"
Steps:

web_search | query: "Bitcoin price today USD"

Goal: "List the files on the desktop and find the largest 5 files"
Steps:

file_controller | action: list, path: desktop
file_controller | action: largest, path: desktop, count: 5

Goal: "Install PUBG from Steam"
Steps:

game_updater | action: install, platform: steam, game_name: "PUBG"

Goal: "Update all my Steam games"
Steps:

game_updater | action: update, platform: steam

Goal: "Send John a message on WhatsApp saying there is a meeting tomorrow"
Steps:

send_message | receiver: John, message_text: "There is a meeting tomorrow", platform: WhatsApp

Goal: "Open the clock and set a reminder for 30 minutes later"
Steps:

reminder | date: [today], time: [now+30min], message: "Reminder"

OUTPUT — return ONLY valid JSON, no markdown, no explanation, no code blocks:
{
  "plan_id": "...",
  "goal": "...",
  "nodes": [
    {
      "node_id": "1",
      "objective": "...",
      "tool": "tool_name",
      "parameters": {},
      "expected_outcome": "...",
      "risk_tier": "tier_1",
      "depends_on": []
    }
  ]
}
"""


def _get_api_key() -> str:
    return get_api_key(required=True)


# ── Plan Normalization ────────────────────────────────────────────────────────

def normalize_plan(plan: dict) -> list[TaskNode]:
    """Convert a legacy plan dict (with 'steps') into a list of TaskNodes."""
    nodes: list[TaskNode] = []
    previous_id: str | None = None

    for index, step in enumerate(plan.get("steps", []), start=1):
        step_num = step.get("step", index)
        node_id = f"step-{step_num}"
        tool = step["tool"]
        node = TaskNode(
            node_id=node_id,
            objective=step["description"],
            tool=tool,
            parameters=step.get("parameters", {}),
            expected_outcome=step.get("expected_outcome", step["description"]),
            risk_tier=TOOL_RISK_MAP.get(tool, RiskTier.TIER_2),
            depends_on=[previous_id] if previous_id else [],
            verification_rule=step.get("verification_rule", ""),
        )
        nodes.append(node)
        previous_id = node_id

    return nodes


# ── Plan Creation ─────────────────────────────────────────────────────────────

def _sanitize_generated_code_nodes(data: dict, goal: str) -> None:
    """Replace any generated_code nodes with web_search fallback."""
    for node in data.get("nodes", []):
        if node.get("tool") == "generated_code":
            node["tool"] = "web_search"
            node["parameters"] = {"query": node.get("objective", goal)[:200]}
            logger.warning(
                "Sanitized generated_code node → web_search: %s",
                node.get("objective", "")[:60],
            )


def _strip_markdown_fences(text: str) -> str:
    """Remove markdown code block fences from LLM output."""
    return re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()


def _extract_json_payload(text: str) -> dict:
    """Extract the first valid JSON object from an LLM response."""
    cleaned = _strip_markdown_fences(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = cleaned[start : end + 1]
        return json.loads(candidate)

    raise json.JSONDecodeError("No JSON object found", cleaned, 0)


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


def _extract_contact_name(goal: str) -> str:
    patterns = [
        r'contact name\s+([A-Za-z0-9_.-]+)',
        r'to\s+([A-Z][A-Za-z0-9_.-]+)\s+then\s+message',
        r'message\s+([A-Z][A-Za-z0-9_.-]+)\s+',
    ]
    for pattern in patterns:
        match = re.search(pattern, goal, re.IGNORECASE)
        if match:
            return match.group(1).strip(' "\'')
    return ""


def _extract_message_text(goal: str) -> str:
    quoted = re.findall(r'"([^"]+)"', goal)
    if quoted:
        return quoted[-1].strip()

    match = re.search(r'\bmessage\s+(?:him|her|them|[A-Za-z0-9_.-]+)\s+(.+)$', goal, re.IGNORECASE)
    if match:
        return match.group(1).strip(' "\'.')
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
        domain = match.group(1)
        return f"https://{domain}"
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


def _is_message_goal(goal: str) -> bool:
    lowered = goal.lower()
    return any(platform in lowered for platform in ("whatsapp", "telegram", "signal", "discord", "messenger")) and "message" in lowered


def _is_open_chat_goal(goal: str) -> bool:
    lowered = goal.lower()
    has_platform = any(platform in lowered for platform in ("whatsapp", "telegram", "signal", "discord", "messenger"))
    has_chat_intent = any(token in lowered for token in ("open the chat", "open chat", "search for contact", "search contact", "find contact"))
    return has_platform and has_chat_intent and "message " not in lowered


def _is_direct_shutdown_goal(goal: str) -> bool:
    normalized = " ".join(goal.strip().lower().split())
    return normalized in {
        "shutdown",
        "shut down",
        "buddy shutdown",
        "shutdown buddy",
        "turn yourself off",
        "close buddy",
        "exit buddy",
        "stop buddy",
    }


def _build_fast_route_plan(goal: str) -> TaskPlan | None:
    lowered = " ".join(goal.lower().split())

    if "youtube" in lowered and ("play" in lowered or "watch" in lowered):
        query = _derive_youtube_query(goal)
        return TaskPlan(
            plan_id=str(uuid.uuid4()),
            goal=goal,
            nodes=[
                TaskNode(
                    node_id="1",
                    objective=f"Play {query} on YouTube",
                    tool="youtube_video",
                    parameters={"action": "play", "query": query},
                    expected_outcome="Requested YouTube video is opened and playing",
                    risk_tier=RiskTier.TIER_1,
                )
            ],
            metadata={"route": "fast_path", "intent_family": "youtube_play"},
        )

    if _is_message_goal(goal):
        receiver = _extract_contact_name(goal)
        message_text = _extract_message_text(goal)
        platform = (
            "WhatsApp"
            if "whatsapp" in lowered
            else "Telegram"
            if "telegram" in lowered
            else "Signal"
            if "signal" in lowered
            else "Discord"
            if "discord" in lowered
            else "Messenger"
        )
        if receiver and message_text:
            return TaskPlan(
                plan_id=str(uuid.uuid4()),
                goal=goal,
                nodes=[
                    TaskNode(
                        node_id="1",
                        objective=f"Send '{message_text}' to {receiver} via {platform}",
                        tool="send_message",
                        parameters={
                            "receiver": receiver,
                            "message_text": message_text,
                            "platform": platform,
                        },
                        expected_outcome=f"Message is sent to {receiver} via {platform}",
                        risk_tier=RiskTier.TIER_1,
                    )
                ],
                metadata={"route": "fast_path", "intent_family": "message_send"},
            )

    if _is_open_chat_goal(goal):
        receiver = _extract_contact_name(goal)
        platform = (
            "WhatsApp"
            if "whatsapp" in lowered
            else "Telegram"
            if "telegram" in lowered
            else "Signal"
            if "signal" in lowered
            else "Discord"
            if "discord" in lowered
            else "Messenger"
        )
        if receiver:
            return TaskPlan(
                plan_id=str(uuid.uuid4()),
                goal=goal,
                nodes=[
                    TaskNode(
                        node_id="1",
                        objective=f"Open the chat for {receiver} in {platform}",
                        tool="send_message",
                        parameters={
                            "receiver": receiver,
                            "message_text": "",
                            "platform": platform,
                            "mode": "open_chat",
                        },
                        expected_outcome=f"The chat for {receiver} is opened in {platform}",
                        risk_tier=RiskTier.TIER_1,
                    )
                ],
                metadata={"route": "fast_path", "intent_family": "open_chat"},
            )

    if any(token in lowered for token in ("volume", "mute", "unmute")):
        if "mute" in lowered or "unmute" in lowered:
            action = "volume_mute"
        else:
            value_match = re.search(r"(\d{1,3})\s*%", lowered)
            if value_match:
                action = "volume_set"
                value = max(0, min(100, int(value_match.group(1))))
                params = {"action": action, "value": str(value)}
            elif any(token in lowered for token in ("increase", "up", "raise", "higher")):
                action = "volume_up"
                params = {"action": action}
            else:
                action = "volume_down"
                params = {"action": action}
            return TaskPlan(
                plan_id=str(uuid.uuid4()),
                goal=goal,
                nodes=[
                    TaskNode(
                        node_id="1",
                        objective=f"Adjust system volume via {action}",
                        tool="computer_settings",
                        parameters=params,
                        expected_outcome="System volume changes",
                        risk_tier=RiskTier.TIER_1,
                    )
                ],
                metadata={"route": "fast_path", "intent_family": "volume_control"},
            )
        return TaskPlan(
            plan_id=str(uuid.uuid4()),
            goal=goal,
            nodes=[
                TaskNode(
                    node_id="1",
                    objective="Toggle mute state",
                    tool="computer_settings",
                    parameters={"action": action},
                    expected_outcome="Mute state changes",
                    risk_tier=RiskTier.TIER_1,
                )
            ],
            metadata={"route": "fast_path", "intent_family": "volume_control"},
        )

    if "brightness" in lowered:
        value_match = re.search(r"(\d{1,3})\s*%", lowered)
        if any(token in lowered for token in ("increase", "up", "raise", "higher")):
            action = "brightness_up"
        elif any(token in lowered for token in ("decrease", "down", "lower")):
            action = "brightness_down"
        elif value_match:
            action = "brightness_up" if int(value_match.group(1)) >= 50 else "brightness_down"
        else:
            action = "brightness_up"
        return TaskPlan(
            plan_id=str(uuid.uuid4()),
            goal=goal,
            nodes=[
                TaskNode(
                    node_id="1",
                    objective=f"Adjust display brightness via {action}",
                    tool="computer_settings",
                    parameters={"action": action},
                    expected_outcome="Display brightness changes",
                    risk_tier=RiskTier.TIER_1,
                )
            ],
            metadata={"route": "fast_path", "intent_family": "brightness_control"},
        )

    if "bluetooth" in lowered:
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
        return TaskPlan(
            plan_id=str(uuid.uuid4()),
            goal=goal,
            nodes=[
                TaskNode(
                    node_id="1",
                    objective=f"Handle Bluetooth request via {action}",
                    tool="bluetooth_manager",
                    parameters={"action": action, "device_name": _extract_device_name(goal)},
                    expected_outcome="Bluetooth request is handled",
                    risk_tier=RiskTier.TIER_1 if action in {"status", "open_settings", "connect_saved", "pair_new", "accept_pairing"} else RiskTier.TIER_2,
                )
            ],
            metadata={"route": "fast_path", "intent_family": "bluetooth_control"},
        )

    if "process" in lowered or "task manager" in lowered or "running app" in lowered:
        if "task manager" in lowered:
            return TaskPlan(
                plan_id=str(uuid.uuid4()),
                goal=goal,
                nodes=[
                    TaskNode(
                        node_id="1",
                        objective="Open Task Manager",
                        tool="computer_settings",
                        parameters={"action": "task_manager"},
                        expected_outcome="Task Manager opens",
                        risk_tier=RiskTier.TIER_1,
                    )
                ],
                metadata={"route": "fast_path", "intent_family": "process_view"},
            )
        action = "top" if any(token in lowered for token in ("top", "highest", "cpu", "memory")) else "list"
        params = {"action": action}
        if action == "top":
            params["sort_by"] = "cpu" if "cpu" in lowered else "memory"
        return TaskPlan(
            plan_id=str(uuid.uuid4()),
            goal=goal,
            nodes=[
                TaskNode(
                    node_id="1",
                    objective="Inspect running processes",
                    tool="process_manager",
                    parameters=params,
                    expected_outcome="Process list is returned",
                    risk_tier=RiskTier.TIER_1,
                )
            ],
            metadata={"route": "fast_path", "intent_family": "process_view"},
        )

    if re.search(r"\b(run|open|launch|start)\b", lowered):
        site_url = _extract_site_url(goal)
        if site_url:
            return TaskPlan(
                plan_id=str(uuid.uuid4()),
                goal=goal,
                nodes=[
                    TaskNode(
                        node_id="1",
                        objective=f"Open {site_url} in the browser",
                        tool="browser_control",
                        parameters={"action": "go_to", "url": site_url},
                        expected_outcome=f"{site_url} opens in the browser",
                        risk_tier=RiskTier.TIER_1,
                    )
                ],
                metadata={"route": "fast_path", "intent_family": "browser_open"},
            )

        app_name = _extract_app_name(goal)
        if app_name:
            run_as_admin = any(
                phrase in lowered
                for phrase in (
                    "run as admin",
                    "run as administrator",
                    "as admin",
                    "as administrator",
                )
            )
            return TaskPlan(
                plan_id=str(uuid.uuid4()),
                goal=goal,
                nodes=[
                    TaskNode(
                        node_id="1",
                        objective=f"Open {app_name}" + (" as administrator" if run_as_admin else ""),
                        tool="open_app",
                        parameters={"app_name": app_name, "run_as_admin": run_as_admin},
                        expected_outcome=f"{app_name} opens successfully",
                        risk_tier=RiskTier.TIER_3 if run_as_admin else RiskTier.TIER_1,
                    )
                ],
                metadata={"route": "fast_path", "intent_family": "open_app"},
            )

    return None


def _direct_shutdown_plan(goal: str) -> TaskPlan:
    return TaskPlan(
        plan_id=str(uuid.uuid4()),
        goal=goal,
        nodes=[
            TaskNode(
                node_id="1",
                objective="Shut down Buddy gracefully",
                tool="shutdown_buddy",
                parameters={},
                expected_outcome="Buddy shuts down cleanly",
                risk_tier=RiskTier.TIER_3,
            )
        ],
    )


def create_plan(goal: str, context: str = "") -> TaskPlan:
    """Create a structured TaskPlan from a user goal with automatic fallback."""
    from agent.llm_gateway import llm_generate

    logger.info("Creating plan for: %s", goal[:80])

    if _is_direct_shutdown_goal(goal):
        logger.info("Using direct shutdown plan for: %s", goal[:80])
        return _direct_shutdown_plan(goal)

    fast_route_plan = _build_fast_route_plan(goal)
    if fast_route_plan is not None:
        logger.info(
            "Using deterministic fast-path plan: id=%s, intent=%s",
            fast_route_plan.plan_id,
            fast_route_plan.metadata.get("intent_family", "generic"),
        )
        return fast_route_plan

    user_input = f"Goal: {goal}"
    if context:
        user_input += f"\n\nContext: {context}"

    try:
        result = llm_generate(
            prompt=user_input,
            system=PLANNER_PROMPT,
            gemini_model="gemini-2.5-flash",
        )
        data = _extract_json_payload(result.text)

        if "nodes" not in data and "steps" in data:
            return TaskPlan(plan_id=str(uuid.uuid4()), goal=data.get("goal", goal), nodes=normalize_plan(data))

        # Security: never allow generated_code from LLM
        _sanitize_generated_code_nodes(data, goal)

        plan = TaskPlan(**data)
        logger.info(
            "Plan created: id=%s, nodes=%d, tools=[%s] (via %s)",
            plan.plan_id,
            len(plan.nodes),
            ", ".join(n.tool for n in plan.nodes),
            result.model,
        )
        return plan

    except json.JSONDecodeError as exc:
        logger.error("Plan JSON parse failed: %s", exc)
        return _fallback_plan(goal)
    except Exception as exc:
        logger.error("Planning failed: %s", exc)
        return _fallback_plan(goal)


# ── Fallback Plan ─────────────────────────────────────────────────────────────

def _fallback_plan(goal: str) -> TaskPlan:
    """Generate a simple domain-aware fallback when planning fails."""
    logger.info("Generating fallback plan for: %s", goal[:60])

    if _is_direct_shutdown_goal(goal):
        return _direct_shutdown_plan(goal)

    return TaskPlan(
        plan_id=str(uuid.uuid4()),
        goal=goal,
        nodes=[
            TaskNode(
                node_id="1",
                objective=f"Search for: {goal}",
                tool="web_search",
                parameters={"query": goal},
                expected_outcome="Search results retrieved"
            )
        ]
    )


# ── Replanning ────────────────────────────────────────────────────────────────

def replan(
    goal: str,
    completed_nodes: list[TaskNode],
    failed_node: TaskNode,
    error: str,
) -> TaskPlan:
    """Create a revised plan after a step failure with automatic fallback."""
    from agent.llm_gateway import llm_generate

    logger.info(
        "Replanning after failure: node=%s, tool=%s, error=%s",
        failed_node.node_id,
        failed_node.tool,
        error[:80],
    )

    completed_summary = "\n".join(
        f"  - Node {n.node_id} ({n.tool}): DONE" for n in completed_nodes
    )

    prompt = f"""Goal: {goal}

Already completed:
{completed_summary if completed_summary else '  (none)'}

Failed node: [{failed_node.tool}] {failed_node.objective}
Error: {error}

Create a REVISED TaskPlan for the remaining work only. Do not repeat completed steps."""

    try:
        result = llm_generate(
            prompt=prompt,
            system=PLANNER_PROMPT,
            gemini_model="gemini-2.5-flash",
        )
        data = _extract_json_payload(result.text)

        _sanitize_generated_code_nodes(data, goal)

        plan = TaskPlan(**data)
        logger.info(
            "Revised plan: id=%s, nodes=%d (via %s)",
            plan.plan_id,
            len(plan.nodes),
            result.model,
        )
        return plan
    except Exception as exc:
        logger.error("Replan failed: %s", exc)
        return _fallback_plan(goal)
