"""
agent/executor.py — Tool Execution Engine
==========================================
Routes task nodes to their corresponding action modules via a registry-based
dispatch system. Handles error recovery, replanning, and LLM-generated code
fallback with sandboxing warnings.

Architecture:
    TaskNode → _TOOL_REGISTRY lookup → action module → ActionResult
    Unknown tools → _run_generated_code() (sandboxed fallback with warning)
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Callable

from buddy_logging import get_logger
from config import get_api_key
from agent.error_handler import ErrorDecision, analyze_error, generate_fix
from agent.models import ActionResult, TaskNode, TaskPlan
from agent.personality import (
    build_planning_failure_reply,
    build_task_aborted_reply,
    build_task_cancelled_reply,
    build_task_failed_reply,
    build_task_retry_reply,
)
from agent.planner import create_plan, replan

__all__ = ["AgentExecutor", "call_tool", "call_tool_structured"]

logger = get_logger("agent.executor")

_FAILURE_MARKERS = (
    "error",
    "failed",
    "could not",
    "not found",
    "timeout",
    "timed out",
    "blocked",
    "unknown ",
    "requires administrator",
    "requires admin",
    "pyautogui is not installed",
    "no bluetooth adapter found",
)


def _looks_like_tool_failure(result: Any) -> bool:
    if not isinstance(result, str):
        return False
    normalized = result.strip().lower()
    return any(marker in normalized for marker in _FAILURE_MARKERS)


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = get_base_dir()


def _get_api_key() -> str:
    return get_api_key(required=True)


# ── Registry-Based Tool Dispatch ──────────────────────────────────────────────
# Each entry maps a tool name to a lazy-import callable.
# Standard signature: fn(parameters=dict, player=None, **kw) -> str
#
# Tools that accept `speak` are marked separately in _SPEAK_AWARE_TOOLS.

def _make_standard_tool(module_path: str, fn_name: str) -> Callable:
    """Create a lazy-loading tool wrapper for standard (parameters, player) signature."""
    def _invoke(parameters: dict, speak: Callable | None = None, **kw: Any) -> str:
        import importlib
        mod = importlib.import_module(module_path)
        fn = getattr(mod, fn_name)
        return fn(parameters=parameters, player=None) or "Done."
    return _invoke


def _make_speak_tool(module_path: str, fn_name: str) -> Callable:
    """Create a lazy-loading tool wrapper for tools that accept a speak callback."""
    def _invoke(parameters: dict, speak: Callable | None = None, **kw: Any) -> str:
        import importlib
        mod = importlib.import_module(module_path)
        fn = getattr(mod, fn_name)
        return fn(parameters=parameters, player=None, speak=speak) or "Done."
    return _invoke


def _screen_process_tool(parameters: dict, speak: Callable | None = None, **kw: Any) -> str:
    from actions.screen_processor import screen_process
    screen_process(parameters=parameters, player=None)
    return "Screen captured and analyzed."


def _screen_recorder_tool(parameters: dict, speak: Callable | None = None, **kw: Any) -> str:
    from actions.screen_recorder import ScreenRecorderAction
    return ScreenRecorderAction().execute(
        parameters.get("action"),
        parameters.get("duration"),
        parameters.get("resolution"),
        parameters.get("fps"),
        parameters.get("bitrate"),
        parameters.get("audio_source"),
    )


def _generated_code_tool(parameters: dict, speak: Callable | None = None, **kw: Any) -> str:
    description = parameters.get("description", "")
    if not description:
        raise ValueError("generated_code requires a 'description' parameter.")
    return _run_generated_code(description, speak=speak)


# ── Tool Registry ─────────────────────────────────────────────────────────────
# Central registry: tool_name -> callable(parameters, speak) -> str
# Adding a new tool = one line in this dict. No more if/elif chains.

_TOOL_REGISTRY: dict[str, Callable[..., str]] = {
    # ── Read-Only / Safe ──────────────────────────────────────────────────
    "screen_process":       _screen_process_tool,
    "web_search":           _make_standard_tool("actions.web_search", "web_search"),
    "weather_report":       _make_standard_tool("actions.weather_report", "weather_action"),
    "hardware_diagnostics": _make_standard_tool("actions.hardware_diagnostics", "hardware_diagnostics"),
    "process_manager":      _make_standard_tool("actions.process_manager", "process_manager"),
    "bluetooth_manager":    _make_standard_tool("actions.bluetooth_manager", "bluetooth_manager"),

    # ── UI Automation ─────────────────────────────────────────────────────
    "open_app":             _make_standard_tool("actions.open_app", "open_app"),
    "browser_control":      _make_standard_tool("actions.browser_control", "browser_control"),
    "youtube_video":        _make_standard_tool("actions.youtube_video", "youtube_video"),
    "desktop_control":      _make_standard_tool("actions.desktop", "desktop_control"),
    "computer_control":     _make_standard_tool("actions.computer_control", "computer_control"),
    "app_optimizer":        _make_standard_tool("actions.app_optimizer", "app_optimizer"),

    # ── File & Data ───────────────────────────────────────────────────────
    "file_controller":      _make_standard_tool("actions.file_controller", "file_controller"),
    "send_message":         _make_standard_tool("actions.send_message", "send_message"),
    "reminder":             _make_standard_tool("actions.reminder", "reminder"),
    "computer_settings":    _make_standard_tool("actions.computer_settings", "computer_settings"),
    "backup_manager":       _make_standard_tool("actions.backup_manager", "backup_manager"),

    # ── Security & System ─────────────────────────────────────────────────
    "access_monitor":       _make_standard_tool("actions.access_monitor", "access_monitor"),
    "network_security":     _make_standard_tool("actions.network_security", "network_security"),
    "process_shield":       _make_standard_tool("actions.process_shield", "process_shield"),
    "maintenance_manager":  _make_standard_tool("actions.maintenance_manager", "maintenance_manager"),
    "recovery_manager":     _make_standard_tool("actions.recovery_manager", "recovery_manager"),
    "vault_manager":        _make_standard_tool("actions.vault_manager", "vault_manager"),
    "privacy_hardener":     _make_standard_tool("actions.privacy_hardener", "privacy_hardener"),

    # ── Developer & Code ──────────────────────────────────────────────────
    "code_helper":          _make_speak_tool("actions.code_helper", "code_helper"),
    "dev_agent":            _make_speak_tool("actions.dev_agent", "dev_agent"),
    "game_updater":         _make_speak_tool("actions.game_updater", "game_updater"),
    "flight_finder":        _make_speak_tool("actions.flight_finder", "flight_finder"),

    # ── Special ───────────────────────────────────────────────────────────
    "screen_recorder":      _screen_recorder_tool,
    "generated_code":       _generated_code_tool,
}


# ── Generated Code Fallback (Sandboxed) ──────────────────────────────────────

def _run_generated_code(description: str, speak: Callable | None = None) -> str:
    """
    ⚠️ SANDBOX WARNING: This function executes LLM-generated Python code.
    The code runs in a subprocess with a 120-second timeout, but it has
    access to the user's filesystem and environment. Use with caution.

    This is a fallback for tasks that don't match any registered tool.
    """
    from agent.llm_gateway import llm_generate

    logger.warning(
        "⚠️ SANDBOX: Executing LLM-generated code for task: %s",
        description[:100],
    )

    if speak:
        speak("Writing custom code for this task, Buddy. Please note this runs in sandbox mode.")

    home = Path.home()
    desktop = home / "Desktop"
    downloads = home / "Downloads"
    documents = home / "Documents"

    try:
        result = llm_generate(
            prompt=(
                f"Write Python code to accomplish this task:\n\n{description}\n\n"
                f"Paths:\nDesktop={desktop}\nDownloads={downloads}\n"
                f"Documents={documents}\nHome={home}"
            ),
            system=(
                "You are an expert Python developer. "
                "Write clean, complete, working Python code. "
                "Use standard library + common packages. "
                "Return ONLY the Python code."
            ),
        )
        code = result.text.strip()
        code = re.sub(r"```(?:python)?", "", code).strip().rstrip("`").strip()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as temp_file:
            temp_file.write(code)
            tmp_path = temp_file.name

        logger.info("Executing generated code: %s (via %s)", tmp_path, result.model)

        run_result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(Path.home()),
        )
        os.unlink(tmp_path)

        if run_result.returncode == 0 and run_result.stdout.strip():
            return run_result.stdout.strip()
        if run_result.returncode == 0:
            return "Task completed successfully."
        raise RuntimeError(run_result.stderr.strip() or "Generated code failed.")
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Generated code timed out after 120 seconds.") from exc


# ── Language Detection & Translation ──────────────────────────────────────────

def _detect_language(text: str) -> str:
    from agent.llm_gateway import llm_generate

    try:
        result = llm_generate(
            prompt=(
                "What language is this text written in? "
                "Reply with ONLY the language name in English.\n\n"
                f"Text: {text[:200]}"
            ),
        )
        return result.text.strip()
    except Exception:
        return "English"


def _translate_to_goal_language(content: str, goal: str) -> str:
    if not goal:
        return content

    if os.getenv("BUDDY_ENABLE_GOAL_LANGUAGE_TRANSLATION", "").strip().lower() not in {"1", "true", "yes"}:
        return content

    try:
        from agent.llm_gateway import llm_generate

        target_lang = _detect_language(goal)
        result = llm_generate(
            prompt=(
                f"Translate the following text into {target_lang}. "
                "Keep structure and facts intact. Return only the translated text.\n\n"
                f"{content[:4000]}"
            ),
        )
        return result.text.strip()
    except Exception:
        return content


# ── Context Injection ─────────────────────────────────────────────────────────

def _inject_context(
    params: dict, tool: str, step_results: dict, goal: str = ""
) -> dict:
    if not step_results:
        return params

    params = dict(params)
    if tool == "file_controller" and params.get("action") in {"write", "create_file"}:
        content = params.get("content", "")
        if not content or len(content) < 50:
            all_results = [
                value
                for value in step_results.values()
                if value and len(value) > 100 and value not in {"Done.", "Completed."}
            ]
            if all_results:
                params["content"] = _translate_to_goal_language(
                    "\n\n---\n\n".join(all_results), goal
                )
    return params


# ── Unified Tool Dispatch ─────────────────────────────────────────────────────

def call_tool(tool: str, parameters: dict, speak: Callable | None = None) -> str:
    """
    Dispatch a tool call through the registry.
    Priority: core.tools.ToolRegistry → legacy _TOOL_REGISTRY → generated code.
    """
    # Try new strict registry first (if kernel is initialized)
    try:
        from agent.kernel import kernel
        if tool in kernel.tools:
            logger.info("Dispatching tool via ToolRegistry: %s", tool)
            return kernel.tools.execute(tool, parameters, speak=speak)
    except Exception as exc:
        logger.debug("ToolRegistry dispatch skipped for '%s': %s", tool, exc)

    # Fall back to legacy registry
    handler = _TOOL_REGISTRY.get(tool)
    if handler is not None:
        logger.info("Dispatching tool via legacy registry: %s", tool)
        return handler(parameters=parameters, speak=speak)

    # Fallback: unknown tool → generated code (sandboxed)
    logger.warning("Unknown tool '%s' — falling back to generated code sandbox.", tool)
    return _run_generated_code(
        f"Accomplish this task using tool concept '{tool}': {parameters}",
        speak=speak,
    )


def call_tool_structured(
    node: TaskNode, speak: Callable | None = None
) -> ActionResult:
    """
    Execute a TaskNode and return a structured ActionResult.
    Wraps call_tool with rich metadata extraction.
    """
    tool = node.tool
    parameters = node.parameters
    started_at = time.time()

    try:
        if tool == "open_app":
            summary = call_tool(tool, parameters, speak)
            status = "error" if _looks_like_tool_failure(summary) else "success"
            return ActionResult(
                status=status,
                summary=str(summary),
                observations={"app_name": parameters.get("app_name", "")},
                changed_state={"app_name": parameters.get("app_name", "")},
                retryable=status == "error",
                error_message=str(summary) if status == "error" else None,
            )

        if tool == "web_search":
            result = call_tool(tool, parameters, speak)
            return ActionResult(
                status="success",
                summary="Research complete",
                observations={"results": result, "query": parameters.get("query", "")},
                started_at=started_at,
                completed_at=time.time(),
            )

        if tool == "file_controller":
            result = call_tool(tool, parameters, speak)
            changed_state: dict[str, Any] = {}
            if parameters.get("action") in {"write", "create_file"}:
                target_path = _infer_file_path(parameters)
                if target_path:
                    changed_state["path"] = target_path
            return ActionResult(
                status="success",
                summary="File action complete",
                observations={"output": result, **changed_state},
                changed_state=changed_state,
                started_at=started_at,
                completed_at=time.time(),
            )

        if tool == "browser_control":
            result = call_tool(tool, parameters, speak)
            observed_url = ""
            if isinstance(result, str) and "Opened:" in result:
                observed_url = result.split("Opened:", 1)[1].strip()
            status = "error" if _looks_like_tool_failure(result) else "success"
            return ActionResult(
                status=status,
                summary=str(result),
                observations={"url": observed_url, "action": parameters.get("action", "")},
                retryable=status == "error",
                error_message=str(result) if status == "error" else None,
            )

        if tool == "send_message":
            result = call_tool(tool, parameters, speak)
            status = "error" if _looks_like_tool_failure(result) else "success"
            return ActionResult(
                status=status,
                summary=str(result),
                changed_state={"receiver": parameters.get("receiver", "")},
                retryable=status == "error",
                error_message=str(result) if status == "error" else None,
            )

        # Generic tool execution
        result = call_tool(tool, parameters, speak)
        status = "error" if _looks_like_tool_failure(result) else "success"
        return ActionResult(
            status=status,
            summary=str(result),
            retryable=status == "error",
            error_message=str(result) if status == "error" else None,
        )

    except Exception as exc:
        logger.error("Tool '%s' failed: %s", tool, exc, exc_info=True)
        return ActionResult(
            status="error",
            summary=f"Tool {tool} failed",
            error_message=str(exc),
            retryable=True,
            started_at=started_at,
            completed_at=time.time(),
        )


# Backward compatibility aliases
_call_tool = call_tool
_call_tool_structured = call_tool_structured


def _infer_file_path(parameters: dict) -> str:
    path = str(parameters.get("path", "")).strip()
    name = str(parameters.get("name", "")).strip()
    if not path:
        return ""

    if path.lower() == "desktop":
        base = Path.home() / "Desktop"
    elif path.lower() == "downloads":
        base = Path.home() / "Downloads"
    elif path.lower() == "documents":
        base = Path.home() / "Documents"
    else:
        base = Path(path).expanduser()

    target = base / name if name else base
    return str(target)


# ── Agent Executor (Orchestration Loop) ───────────────────────────────────────

class AgentExecutor:
    """
    High-level executor that runs a full plan with error recovery and replanning.
    Coordinates the OPEV (Observe-Plan-Execute-Verify) loop.
    """

    MAX_REPLAN_ATTEMPTS = 2

    def execute(
        self,
        goal: str,
        speak: Callable | None = None,
        cancel_flag: threading.Event | None = None,
    ) -> str:
        logger.info("Executing goal: %s", goal)

        replan_attempts = 0
        completed_nodes: list[TaskNode] = []
        step_results: dict[str, str] = {}
        plan = create_plan(goal)

        while True:
            if not isinstance(plan, TaskPlan) or not plan.nodes:
                message = build_planning_failure_reply()
                logger.warning("Plan creation failed for goal: %s", goal)
                if speak:
                    speak(message)
                return message

            success = True
            failed_node: TaskNode | None = None
            failed_error = ""

            for node in plan.nodes:
                if cancel_flag and cancel_flag.is_set():
                    logger.info("Task cancelled by user.")
                    if speak:
                        speak(build_task_cancelled_reply())
                    return build_task_cancelled_reply()

                params = _inject_context(
                    node.parameters, node.tool, step_results, goal=goal
                )
                node.parameters = params
                logger.info(
                    "Step %s: [%s] %s", node.node_id, node.tool, node.objective
                )

                attempt = 1
                while attempt <= 3:
                    try:
                        result = call_tool(node.tool, params, speak)
                        step_results[node.node_id] = result
                        completed_nodes.append(node)
                        logger.info(
                            "Step %s complete: %s", node.node_id, str(result)[:100]
                        )
                        break
                    except Exception as exc:
                        error_msg = str(exc)
                        logger.error(
                            "Step %s attempt %d failed: %s",
                            node.node_id,
                            attempt,
                            error_msg,
                        )
                        recovery = analyze_error(
                            {
                                "step": node.node_id,
                                "tool": node.tool,
                                "description": node.objective,
                                "parameters": node.parameters,
                            },
                            error_msg,
                            attempt=attempt,
                        )
                        decision = recovery["decision"]

                        if speak and recovery.get("user_message"):
                            speak(recovery["user_message"])

                        if decision == ErrorDecision.RETRY:
                            attempt += 1
                            time.sleep(2)
                            continue

                        if decision == ErrorDecision.SKIP:
                            completed_nodes.append(node)
                            break

                        if decision == ErrorDecision.ABORT:
                            message = build_task_aborted_reply(str(recovery.get("reason", "")))
                            if speak:
                                speak(message)
                            return message

                        fix_suggestion = recovery.get("fix_suggestion", "")
                        if fix_suggestion and node.tool != "generated_code":
                            fixed_step = generate_fix(
                                {
                                    "step": node.node_id,
                                    "tool": node.tool,
                                    "description": node.objective,
                                    "parameters": node.parameters,
                                },
                                error_msg,
                                fix_suggestion,
                            )
                            result = call_tool(
                                fixed_step["tool"], fixed_step["parameters"], speak
                            )
                            step_results[node.node_id] = result
                            completed_nodes.append(node)
                            break

                        failed_node = node
                        failed_error = error_msg
                        success = False
                        break

                if not success:
                    break

            if success:
                return self._summarize(goal, completed_nodes, speak)

            if replan_attempts >= self.MAX_REPLAN_ATTEMPTS or failed_node is None:
                message = build_task_failed_reply()
                logger.error(message)
                if speak:
                    speak(message)
                return message

            if speak:
                speak(build_task_retry_reply())
            replan_attempts += 1
            logger.info("Replanning (attempt %d)...", replan_attempts)
            plan = replan(goal, completed_nodes, failed_node, failed_error)

    def _summarize(
        self,
        goal: str,
        completed_nodes: list[TaskNode],
        speak: Callable | None,
    ) -> str:
        fallback = f"All done, Buddy. Completed {len(completed_nodes)} steps for: {goal[:60]}."
        try:
            from agent.llm_gateway import llm_generate

            steps_str = "\n".join(
                f"- {node.objective}" for node in completed_nodes
            )
            prompt = (
                f'User goal: "{goal}"\n'
                f"Completed steps:\n{steps_str}\n\n"
                "Write a single natural sentence summarizing what was accomplished. "
                "Address the user as 'Buddy'. Be direct and positive."
            )
            result = llm_generate(prompt=prompt)
            summary = result.text.strip()
            if speak:
                speak(summary)
            return summary
        except Exception:
            if speak:
                speak(fallback)
            return fallback
