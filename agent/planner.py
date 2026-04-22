import json
import re
import sys
import uuid
from pathlib import Path

from config import get_api_key
from agent.models import TaskPlan, TaskNode, RiskTier


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR        = get_base_dir()


TOOL_RISK_MAP = {
    "screen_process": RiskTier.TIER_0,
    "web_search": RiskTier.TIER_0,
    "weather_report": RiskTier.TIER_0,
    "open_app": RiskTier.TIER_1,
    "browser_control": RiskTier.TIER_1,
    "youtube_video": RiskTier.TIER_1,
    "file_controller": RiskTier.TIER_2,
    "computer_control": RiskTier.TIER_2,
    "computer_settings": RiskTier.TIER_2,
    "desktop_control": RiskTier.TIER_2,
    "reminder": RiskTier.TIER_2,
    "antivirus_manager": RiskTier.TIER_2,
    "security_auditor": RiskTier.TIER_2,
    "send_message": RiskTier.TIER_3,
    "firewall_manager": RiskTier.TIER_3,
    "privacy_manager": RiskTier.TIER_3,
    "software_manager": RiskTier.TIER_3,
    "screen_recorder": RiskTier.TIER_2,
    "access_monitor": RiskTier.TIER_2,
    "network_security": RiskTier.TIER_2,
    "process_shield": RiskTier.TIER_2,
    "maintenance_manager": RiskTier.TIER_2,
    "hardware_diagnostics": RiskTier.TIER_1,
    "recovery_manager": RiskTier.TIER_3,
    "app_optimizer": RiskTier.TIER_1,
    "backup_manager": RiskTier.TIER_2,
    "vault_manager": RiskTier.TIER_3,
    "privacy_hardener": RiskTier.TIER_3,
}


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
file_controller | action: write, path: desktop, name: mechanical_engineering.txt, content: "MECHANICAL ENGINEERING RESEARCH\n\nThis file will be filled with web research results."

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


def normalize_plan(plan: dict) -> list[TaskNode]:
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


def create_plan(goal: str, context: str = "") -> TaskPlan:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=_get_api_key())

    user_input = f"Goal: {goal}"
    if context:
        user_input += f"\n\nContext: {context}"

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_input,
            config=types.GenerateContentConfig(
                system_instruction=PLANNER_PROMPT
            )
        )
        text     = response.text.strip()
        text     = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()

        data = json.loads(text)

        # Validation and cleanup
        for node in data.get("nodes", []):
            if node.get("tool") == "generated_code":
                node["tool"] = "web_search"
                node["parameters"] = {"query": node.get("objective", goal)[:200]}

        plan = TaskPlan(**data)
        print(f"[Planner] ✅ Plan created: {plan.plan_id} ({len(plan.nodes)} nodes)")
        return plan

    except Exception as e:
        print(f"[Planner] ⚠️ Planning failed: {e}")
        return _fallback_plan(goal)


def _fallback_plan(goal: str) -> TaskPlan:
    print("[Planner] 🔄 Generating fallback plan")
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


def replan(goal: str, completed_nodes: list[TaskNode], failed_node: TaskNode, error: str) -> TaskPlan:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=_get_api_key())

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
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=PLANNER_PROMPT
            )
        )
        text     = response.text.strip()
        text     = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
        data     = json.loads(text)

        for node in data.get("nodes", []):
            if node.get("tool") == "generated_code":
                node["tool"] = "web_search"
                node["parameters"] = {"query": node.get("objective", goal)[:200]}

        plan = TaskPlan(**data)
        print(f"[Planner] 🔄 Revised plan: {plan.plan_id} ({len(plan.nodes)} nodes)")
        return plan
    except Exception as e:
        print(f"[Planner] ⚠️ Replan failed: {e}")
        return _fallback_plan(goal)
