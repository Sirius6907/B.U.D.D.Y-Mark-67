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
from typing import Callable

from config import get_api_key
from agent.error_handler import ErrorDecision, analyze_error, generate_fix
from agent.models import ActionResult, TaskNode, TaskPlan
from agent.planner import create_plan, replan


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = get_base_dir()


def _get_api_key() -> str:
    return get_api_key(required=True)


def _run_generated_code(description: str, speak: Callable | None = None) -> str:
    from google import genai
    from google.genai import types

    if speak:
        speak("Writing custom code for this task, sir.")

    home = Path.home()
    desktop = home / "Desktop"
    downloads = home / "Downloads"
    documents = home / "Documents"

    client = genai.Client(api_key=_get_api_key())

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Write Python code to accomplish this task:\n\n{description}\n\n"
                     f"Paths:\nDesktop={desktop}\nDownloads={downloads}\nDocuments={documents}\nHome={home}",
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are an expert Python developer. "
                    "Write clean, complete, working Python code. "
                    "Use standard library + common packages. "
                    "Return ONLY the Python code."
                )
            )
        )
        code = response.text.strip()
        code = re.sub(r"```(?:python)?", "", code).strip().rstrip("`").strip()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as temp_file:
            temp_file.write(code)
            tmp_path = temp_file.name

        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(Path.home()),
        )
        os.unlink(tmp_path)

        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        if result.returncode == 0:
            return "Task completed successfully."
        raise RuntimeError(result.stderr.strip() or "Generated code failed.")
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Generated code timed out after 120 seconds.") from exc


def _detect_language(text: str) -> str:
    from google import genai

    client = genai.Client(api_key=_get_api_key())
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="What language is this text written in? "
                     "Reply with ONLY the language name in English.\n\n"
                     f"Text: {text[:200]}"
        )
        return response.text.strip()
    except Exception:
        return "English"


def _translate_to_goal_language(content: str, goal: str) -> str:
    if not goal:
        return content

    try:
        from google import genai

        client = genai.Client(api_key=_get_api_key())
        target_lang = _detect_language(goal)
        prompt = (
            f"Translate the following text into {target_lang}. Keep structure and facts intact. "
            "Return only the translated text.\n\n"
            f"{content[:4000]}"
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception:
        return content


def _inject_context(params: dict, tool: str, step_results: dict, goal: str = "") -> dict:
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
                params["content"] = _translate_to_goal_language("\n\n---\n\n".join(all_results), goal)
    return params


def _call_tool(tool: str, parameters: dict, speak: Callable | None) -> str:
    if tool == "open_app":
        from actions.open_app import open_app

        return open_app(parameters=parameters, player=None) or "Done."
    if tool == "web_search":
        from actions.web_search import web_search

        return web_search(parameters=parameters, player=None) or "Done."
    if tool == "game_updater":
        from actions.game_updater import game_updater

        return game_updater(parameters=parameters, player=None, speak=speak) or "Done."
    if tool == "browser_control":
        from actions.browser_control import browser_control

        return browser_control(parameters=parameters, player=None) or "Done."
    if tool == "file_controller":
        from actions.file_controller import file_controller

        return file_controller(parameters=parameters, player=None) or "Done."
    if tool == "code_helper":
        from actions.code_helper import code_helper

        return code_helper(parameters=parameters, player=None, speak=speak) or "Done."
    if tool == "dev_agent":
        from actions.dev_agent import dev_agent

        return dev_agent(parameters=parameters, player=None, speak=speak) or "Done."
    if tool == "screen_process":
        from actions.screen_processor import screen_process

        screen_process(parameters=parameters, player=None)
        return "Screen captured and analyzed."
    if tool == "send_message":
        from actions.send_message import send_message

        return send_message(parameters=parameters, player=None) or "Done."
    if tool == "reminder":
        from actions.reminder import reminder

        return reminder(parameters=parameters, player=None) or "Done."
    if tool == "youtube_video":
        from actions.youtube_video import youtube_video

        return youtube_video(parameters=parameters, player=None) or "Done."
    if tool == "weather_report":
        from actions.weather_report import weather_action

        return weather_action(parameters=parameters, player=None) or "Done."
    if tool == "computer_settings":
        from actions.computer_settings import computer_settings

        return computer_settings(parameters=parameters, player=None) or "Done."
    if tool == "desktop_control":
        from actions.desktop import desktop_control

        return desktop_control(parameters=parameters, player=None) or "Done."
    if tool == "computer_control":
        from actions.computer_control import computer_control

        return computer_control(parameters=parameters, player=None) or "Done."
    if tool == "generated_code":
        description = parameters.get("description", "")
        if not description:
            raise ValueError("generated_code requires a 'description' parameter.")
        return _run_generated_code(description, speak=speak)
    if tool == "flight_finder":
        from actions.flight_finder import flight_finder

        return flight_finder(parameters=parameters, player=None, speak=speak) or "Done."
    if tool == "screen_recorder":
        from actions.screen_recorder import ScreenRecorderAction
        action_name = parameters.get("action")
        duration = parameters.get("duration")
        resolution = parameters.get("resolution")
        fps = parameters.get("fps")
        bitrate = parameters.get("bitrate")
        audio_source = parameters.get("audio_source")
        return ScreenRecorderAction().execute(action_name, duration, resolution, fps, bitrate, audio_source)

    if tool == "access_monitor":
        from actions.access_monitor import access_monitor
        return access_monitor(parameters=parameters, player=None) or "Done."
    if tool == "network_security":
        from actions.network_security import network_security
        return network_security(parameters=parameters, player=None) or "Done."
    if tool == "process_shield":
        from actions.process_shield import process_shield
        return process_shield(parameters=parameters, player=None) or "Done."
    if tool == "maintenance_manager":
        from actions.maintenance_manager import maintenance_manager
        return maintenance_manager(parameters=parameters, player=None) or "Done."
    if tool == "hardware_diagnostics":
        from actions.hardware_diagnostics import hardware_diagnostics
        return hardware_diagnostics(parameters=parameters, player=None) or "Done."
    if tool == "recovery_manager":
        from actions.recovery_manager import recovery_manager
        return recovery_manager(parameters=parameters, player=None) or "Done."
    if tool == "app_optimizer":
        from actions.app_optimizer import app_optimizer
        return app_optimizer(parameters=parameters, player=None) or "Done."
    if tool == "backup_manager":
        from actions.backup_manager import backup_manager
        return backup_manager(parameters=parameters, player=None) or "Done."
    if tool == "vault_manager":
        from actions.vault_manager import vault_manager
        return vault_manager(parameters=parameters, player=None) or "Done."
    if tool == "privacy_hardener":
        from actions.privacy_hardener import privacy_hardener
        return privacy_hardener(parameters=parameters, player=None) or "Done."

    return _run_generated_code(f"Accomplish this task: {parameters}", speak=speak)


def _call_tool_structured(node: TaskNode, speak: Callable | None = None) -> ActionResult:
    tool = node.tool
    parameters = node.parameters

    try:
        if tool == "open_app":
            summary = _call_tool(tool, parameters, speak)
            return ActionResult(
                status="success",
                summary=str(summary),
                observations={"app_name": parameters.get("app_name", "")},
                changed_state={"app_name": parameters.get("app_name", "")},
            )

        if tool == "web_search":
            result = _call_tool(tool, parameters, speak)
            return ActionResult(
                status="success",
                summary="Research complete",
                observations={"results": result, "query": parameters.get("query", "")},
            )

        if tool == "file_controller":
            result = _call_tool(tool, parameters, speak)
            changed_state = {}
            if parameters.get("action") in {"write", "create_file"}:
                target_path = _infer_file_path(parameters)
                if target_path:
                    changed_state["path"] = target_path
            return ActionResult(
                status="success",
                summary="File action complete",
                observations={"output": result, **changed_state},
                changed_state=changed_state,
            )

        if tool == "browser_control":
            result = _call_tool(tool, parameters, speak)
            observed_url = ""
            if isinstance(result, str) and "Opened:" in result:
                observed_url = result.split("Opened:", 1)[1].strip()
            return ActionResult(
                status="success",
                summary=str(result),
                observations={"url": observed_url, "action": parameters.get("action", "")},
            )

        if tool == "send_message":
            result = _call_tool(tool, parameters, speak)
            return ActionResult(
                status="success",
                summary=str(result),
                needs_approval=True,
                changed_state={"receiver": parameters.get("receiver", "")},
            )

        result = _call_tool(tool, parameters, speak)
        return ActionResult(status="success", summary=str(result))
    except Exception as exc:
        return ActionResult(
            status="error",
            summary=f"Tool {tool} failed",
            error_message=str(exc),
            retryable=True,
        )


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


class AgentExecutor:
    MAX_REPLAN_ATTEMPTS = 2

    def execute(
        self,
        goal: str,
        speak: Callable | None = None,
        cancel_flag: threading.Event | None = None,
    ) -> str:
        print(f"\n[Executor] Goal: {goal}")

        replan_attempts = 0
        completed_nodes: list[TaskNode] = []
        step_results: dict[str, str] = {}
        plan = create_plan(goal)

        while True:
            if not isinstance(plan, TaskPlan) or not plan.nodes:
                message = "I couldn't create a valid plan for this task, sir."
                if speak:
                    speak(message)
                return message

            success = True
            failed_node: TaskNode | None = None
            failed_error = ""

            for node in plan.nodes:
                if cancel_flag and cancel_flag.is_set():
                    if speak:
                        speak("Task cancelled, sir.")
                    return "Task cancelled."

                params = _inject_context(node.parameters, node.tool, step_results, goal=goal)
                node.parameters = params
                print(f"\n[Executor] Step {node.node_id}: [{node.tool}] {node.objective}")

                attempt = 1
                while attempt <= 3:
                    try:
                        result = _call_tool(node.tool, params, speak)
                        step_results[node.node_id] = result
                        completed_nodes.append(node)
                        print(f"[Executor] Step {node.node_id} done: {str(result)[:100]}")
                        break
                    except Exception as exc:
                        error_msg = str(exc)
                        print(f"[Executor] Step {node.node_id} attempt {attempt} failed: {error_msg}")
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
                            message = f"Task aborted, sir. {recovery.get('reason', '')}"
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
                            result = _call_tool(fixed_step["tool"], fixed_step["parameters"], speak)
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
                message = f"Task failed after {replan_attempts} replan attempts, sir."
                if speak:
                    speak(message)
                return message

            if speak:
                speak("Adjusting my approach, sir.")
            replan_attempts += 1
            plan = replan(goal, completed_nodes, failed_node, failed_error)

    def _summarize(self, goal: str, completed_nodes: list[TaskNode], speak: Callable | None) -> str:
        fallback = f"All done, sir. Completed {len(completed_nodes)} steps for: {goal[:60]}."
        try:
            from google import genai

            client = genai.Client(api_key=_get_api_key())
            steps_str = "\n".join(f"- {node.objective}" for node in completed_nodes)
            prompt = (
                f'User goal: "{goal}"\n'
                f"Completed steps:\n{steps_str}\n\n"
                "Write a single natural sentence summarizing what was accomplished. "
                "Address the user as 'sir'. Be direct and positive."
            )
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            summary = response.text.strip()
            if speak:
                speak(summary)
            return summary
        except Exception:
            if speak:
                speak(fallback)
            return fallback
