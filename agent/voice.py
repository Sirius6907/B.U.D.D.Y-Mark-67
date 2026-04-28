from __future__ import annotations

import asyncio
import json
from collections import deque
from dataclasses import dataclass
from typing import Callable

from buddy_logging import get_logger
from agent.dp_brain import get_dp_brain
from agent.dp_core import build_subproblem_key
from agent.intent_compiler import CommandShape, CompiledCommand, IntentCompiler
from agent.models import SubproblemValue, TaskPlan, WorkflowRecipe
from agent.personality import (
    build_action_failure_reply,
    build_action_success_reply,
    build_internal_error_reply,
    build_planning_failure_reply,
    build_workflow_failure_reply,
    build_workflow_success_reply,
)
from agent.planner import create_plan
from agent.runtime import RuntimeCoordinator
from agent.screen_workflow import run_workflow
from agent.workflow_recipes import match_workflow_recipe, warm_preload_workflows

logger = get_logger("agent.voice")

INTENT_SYSTEM_PROMPT = """You are an intent classifier for B.U.D.D.Y (SIRIUS Mk 67), a personal AI assistant
that can control the user's computer. You will receive the user's latest message AND recent conversation history.

Classify the user's LATEST message into exactly ONE of these categories:

1. "action" - Anything that requires interacting with the computer or inspecting its
   real-time state. This includes:
   - Opening/closing apps, searching the web, controlling the browser, managing files,
     playing music, taking screenshots, coding tasks, etc.
   - SCREEN / SYSTEM AWARENESS queries - any question about what is currently
     happening on the device, what is visible on screen, or what the system is doing.

2. "chat" - Greetings, small talk, questions about BUDDY itself, personal questions,
   general knowledge questions, opinions, jokes, emotional sharing, or anything that
   can be answered conversationally from general knowledge or session context.

Reply with ONLY the single word: chat OR action
Nothing else."""

CHAT_SYSTEM_PROMPT = """You are B.U.D.D.Y (SIRIUS Mk 67), a highly intelligent personal AI assistant.
You speak like a refined, witty AI butler. Address the user as "Buddy" naturally.
Keep responses concise (1-3 sentences max). Always respond in English unless asked otherwise.

CRITICAL: You have a persistent memory system. Below you will find:
1. [LONG-TERM MEMORY]
2. [RECENT CONVERSATION]
3. [RELEVANT CONTEXT]

USE THIS INFORMATION to answer accurately and personally."""

MEMORY_EXTRACT_PROMPT = """You are a memory extraction system for an AI assistant.
Analyze the conversation below and extract ANY new facts worth remembering about the user.

Return a JSON object with categories as keys and key-value pairs as values.
Categories: identity, preferences, projects, relationships, wishes, notes, emotions

If there is NOTHING new to extract, return exactly: {}
Return ONLY valid JSON. No markdown, no explanation."""

_FAST_MODEL = "gemini-2.5-flash"


@dataclass
class VoiceSessionState:
    is_listening: bool = False
    is_speaking: bool = False
    last_transcript: str = ""


class VoiceOrchestrator:
    MAX_HISTORY = 30

    def __init__(self, api_key: str | None = None, speak_fn: Callable | None = None):
        self.api_key = api_key
        self.speak = speak_fn or (lambda text: None)
        self.state = VoiceSessionState()
        self.runtime = RuntimeCoordinator(api_key, speak_fn)
        self.dp_brain = get_dp_brain()
        self.intent_compiler = IntentCompiler()
        warm_preload_workflows(self.dp_brain)
        self.conversation_history: deque[dict] = deque(maxlen=self.MAX_HISTORY)
        self._memory = None

    def _get_memory(self):
        if self._memory is None:
            try:
                from memory.memory_manager import get_memory

                self._memory = get_memory()
            except Exception as exc:
                logger.warning("Failed to load HybridMemory: %s", exc)
        return self._memory

    @property
    def is_speaking(self) -> bool:
        return self.state.is_speaking

    def start_response(self, text: str) -> None:
        self.state.last_transcript = text
        self.state.is_speaking = True
        self.speak(text)

    def interrupt(self) -> None:
        self.state.is_speaking = False

    def _format_history_for_prompt(self) -> str:
        if not self.conversation_history:
            return ""
        lines = []
        for entry in self.conversation_history:
            prefix = "User" if entry.get("role") == "user" else "BUDDY"
            lines.append(f"  {prefix}: {entry.get('text', '')}")
        return "\n".join(lines)

    def _build_memory_context(self, query: str) -> str:
        sections = []
        mem = self._get_memory()
        if mem is None:
            return ""

        try:
            from memory.memory_manager import format_memory_for_prompt

            formatted = format_memory_for_prompt(mem.get_all_memory())
            if formatted.strip():
                sections.append(f"[LONG-TERM MEMORY]\n{formatted}")
        except Exception as exc:
            logger.debug("Failed to load long-term memory: %s", exc)

        try:
            user_profile = mem.get_user_profile()
            if user_profile.strip():
                sections.append(f"[USER PROFILE]\n{user_profile}")
        except Exception as exc:
            logger.debug("Failed to load user profile: %s", exc)

        try:
            soul_profile = mem.get_soul_profile()
            if soul_profile.strip():
                sections.append(f"[BUDDY SOUL]\n{soul_profile}")
        except Exception as exc:
            logger.debug("Failed to load soul profile: %s", exc)

        history = self._format_history_for_prompt()
        if history:
            sections.append(f"[RECENT CONVERSATION]\n{history}")

        try:
            results = mem.search_semantic(query, n_results=3)
            docs = results.get("documents", [[]])[0] if results else []
            relevant = [doc for doc in docs if doc and len(doc) > 10]
            if relevant:
                sections.append("[RELEVANT CONTEXT]\n" + "\n".join(f"  - {doc}" for doc in relevant))
        except Exception as exc:
            logger.debug("Semantic search failed: %s", exc)

        return "\n\n".join(sections) if sections else ""

    def _extract_and_save_memories(self, user_text: str, buddy_reply: str):
        mem = self._get_memory()
        if mem is None:
            return
        try:
            from agent.llm_gateway import llm_generate_json
            from memory.memory_manager import update_memory

            extracted = llm_generate_json(
                prompt=f"Conversation:\nUser: {user_text}\nBUDDY: {buddy_reply}",
                system=MEMORY_EXTRACT_PROMPT,
                gemini_model=_FAST_MODEL,
            )
            if not isinstance(extracted, dict) or not extracted:
                return
            update_memory(extracted)
            try:
                mem.consolidate()
            except Exception as exc:
                logger.debug("Profile consolidation failed: %s", exc)
            fact_count = sum(len(v) if isinstance(v, dict) else 1 for v in extracted.values())
            logger.info("Saved %d new memory facts from conversation: %s", fact_count, list(extracted.keys()))
        except json.JSONDecodeError:
            logger.debug("Memory extraction returned non-JSON")
        except Exception as exc:
            logger.debug("Memory extraction failed: %s", exc)

    def _build_action_context(self, text: str) -> dict:
        lowered = text.lower()
        tool_surface = "generic"
        if any(platform in lowered for platform in ("whatsapp", "telegram", "signal", "discord", "messenger")):
            tool_surface = "messaging"
        elif "youtube" in lowered or "browser" in lowered or "chrome" in lowered:
            tool_surface = "browser"
        elif any(token in lowered for token in ("volume", "brightness", "bluetooth", "settings")):
            tool_surface = "system_controls"
        return {
            "intent_family": "generic",
            "tool_surface": tool_surface,
            "state_snapshot": {
                "tool_surface": tool_surface,
                "recent_actions": list(self.conversation_history)[-3:],
            },
        }

    @staticmethod
    def _is_fast_path_eligible(command: CompiledCommand) -> bool:
        return (
            command.shape is CommandShape.SINGLE_ACTION
            and not command.ambiguity_markers
            and command.extracted_entities.get("platform") not in {"linkedin", "github"}
        )

    @staticmethod
    def _should_skip_dp(command: CompiledCommand) -> bool:
        return command.shape in {
            CommandShape.COMPOUND_ACTION,
            CommandShape.AMBIGUOUS,
            CommandShape.HISTORY_QUESTION,
        }

    def _classify_intent(self, text: str) -> str:
        try:
            from agent.llm_gateway import llm_generate

            history = self._format_history_for_prompt()
            classify_input = f"[RECENT CONTEXT]\n{history}\n\n[LATEST MESSAGE]\n{text}" if history else text
            result = llm_generate(
                prompt=classify_input,
                system=INTENT_SYSTEM_PROMPT,
                gemini_model=_FAST_MODEL,
            )
            raw = result.text.strip().lower()
            intent = raw.split()[0] if raw else "action"
            if intent in {"chat", "action"}:
                logger.info("Intent classified: %s (via %s)", intent, result.model)
                return intent
            return "action"
        except Exception:
            logger.exception("Intent classification failed, defaulting to action")
            return "action"

    def _chat_response(self, text: str) -> str:
        try:
            from agent.llm_gateway import llm_generate

            memory_context = self._build_memory_context(text)
            full_system = CHAT_SYSTEM_PROMPT
            if memory_context:
                full_system += f"\n\n--- MEMORY CONTEXT ---\n{memory_context}\n--- END MEMORY ---"
            result = llm_generate(
                prompt=text,
                system=full_system,
                gemini_model=_FAST_MODEL,
            )
            return result.text.strip()
        except Exception:
            logger.exception("Chat response generation failed")
            return build_internal_error_reply()

    async def _handle_chat_command(self, text: str) -> None:
        self.conversation_history.append({"role": "user", "text": text})
        reply = await asyncio.to_thread(self._chat_response, text)
        self.start_response(reply)
        self.conversation_history.append({"role": "assistant", "text": reply})
        asyncio.get_event_loop().run_in_executor(None, self._extract_and_save_memories, text, reply)

    async def _handle_compiled_action(self, command: CompiledCommand) -> None:
        text = command.normalized_text
        self.conversation_history.append({"role": "user", "text": f"[ACTION] {text}"})

        try:
            from agent.kernel import kernel

            match = kernel.agents.route_by_text(text)
            if match:
                kernel.agents.activate(match.name)
                logger.info("Agent routing: '%s' (score=%.2f) for: %s", match.name, match.score, text[:60])
        except Exception as route_exc:
            logger.debug("Agent routing skipped: %s", route_exc)

        action_context = await asyncio.to_thread(self._build_action_context, text)
        action_context["intent_shape"] = command.shape.value
        if command.extracted_entities:
            action_context["entities"] = command.extracted_entities

        if self._is_fast_path_eligible(command):
            try:
                fast_recipe = await asyncio.to_thread(self.dp_brain.fast_lookup, text)
                if fast_recipe is not None:
                    workflow_result = await self.runtime.execute_workflow(fast_recipe, run_workflow)
                    reply = build_workflow_success_reply(fast_recipe, workflow_result) if workflow_result.status == "success" else build_workflow_failure_reply(fast_recipe, workflow_result)
                    self.start_response(reply)
                    self.conversation_history.append({"role": "assistant", "text": reply})
                    return
            except Exception as exc:
                logger.debug("Fast-path lookup failed: %s", exc)

        if not self._should_skip_dp(command):
            try:
                dp_match = await asyncio.to_thread(self.dp_brain.compose, text, action_context)
                if dp_match is not None:
                    logger.info("DP Hit: reusing cached solution for: %s", text)
                    if isinstance(dp_match, WorkflowRecipe):
                        workflow_result = await self.runtime.execute_workflow(dp_match, run_workflow)
                        reply = build_workflow_success_reply(dp_match, workflow_result) if workflow_result.status == "success" else build_workflow_failure_reply(dp_match, workflow_result)
                        self.start_response(reply)
                        self.conversation_history.append({"role": "assistant", "text": reply})
                        return
                    if isinstance(dp_match, TaskPlan):
                        success = await self.runtime.execute_plan(dp_match)
                        reply = build_action_success_reply(dp_match.goal) if success else build_action_failure_reply(dp_match.goal)
                        self.start_response(reply)
                        self.conversation_history.append({"role": "assistant", "text": reply})
                        return
            except Exception as dp_exc:
                logger.debug("DP lookup/execution failed: %s", dp_exc)

        if command.shape is CommandShape.CAREER_WORKFLOW:
            try:
                from career.orchestrator import CareerOrchestrator

                orchestrator = CareerOrchestrator(
                    self._get_memory(),
                    approval_callback=self.runtime.runtime.approval_callback,
                )
                result = await orchestrator.handle_command(text)
                self.runtime.runtime.status.pending_approval = result.needs_approval
                self.runtime.runtime.status.active_draft_id = str(result.observations.get("draft_id", ""))
                self.runtime.runtime.status.current_goal = text
                self.runtime.runtime.status.current_step = result.observations.get("stage", "")
                self.runtime.runtime._emit_status()
                self.start_response(result.summary)
                self.conversation_history.append({"role": "assistant", "text": result.summary})
                return
            except Exception as exc:
                logger.debug("Career orchestration unavailable, falling back to planner: %s", exc)

        recipe = None
        if command.shape is CommandShape.SINGLE_ACTION:
            recipe = await asyncio.to_thread(match_workflow_recipe, text)
        if recipe is not None:
            action_context["intent_family"] = recipe.intent_family
            workflow_result = await self.runtime.execute_workflow(recipe, run_workflow)
            if workflow_result.status == "success":
                try:
                    key = build_subproblem_key(text, action_context)
                    recipe_payload = recipe.model_dump() if hasattr(recipe, "model_dump") else recipe.dict()
                    self.dp_brain.store_success(
                        key,
                        SubproblemValue(
                            solution_type="workflow_recipe",
                            solution_payload=recipe_payload,
                            status="solved",
                            confidence=1.0,
                            solution_steps=recipe_payload["steps"],
                            evidence={"recipe": recipe_payload},
                            verified_boundaries={"solution_type": "workflow_recipe"},
                        ),
                    )
                except Exception as dp_store_exc:
                    logger.debug("Failed to store workflow success in DP: %s", dp_store_exc)
                reply = build_workflow_success_reply(recipe, workflow_result)
            else:
                reply = build_workflow_failure_reply(recipe, workflow_result)
            self.start_response(reply)
            self.conversation_history.append({"role": "assistant", "text": reply})
            return

        plan = await asyncio.to_thread(create_plan, text)
        if not plan.nodes:
            reply = build_planning_failure_reply()
            self.start_response(reply)
            self.conversation_history.append({"role": "assistant", "text": reply})
            self.interrupt()
            return

        success = await self.runtime.execute_plan(plan)
        action_context["intent_family"] = plan.metadata.get("intent_family", "generic")
        try:
            key = build_subproblem_key(text, action_context)
            plan_payload = plan.model_dump() if hasattr(plan, "model_dump") else plan.dict()
            value = SubproblemValue(
                solution_type="task_plan",
                solution_payload=plan_payload,
                status="solved" if success else "failed",
                confidence=1.0,
                negative_reason=None if success else "plan_execution_failed",
                solution_steps=plan_payload["nodes"],
                evidence={"plan": plan_payload},
                verified_boundaries={"solution_type": "task_plan"},
            )
            if success:
                self.dp_brain.store_success(key, value)
            else:
                self.dp_brain.store_failure(key, value)
        except Exception as dp_store_exc:
            logger.debug("Failed to store plan outcome in DP: %s", dp_store_exc)

        reply = build_action_success_reply(plan.goal) if success else build_action_failure_reply(plan.goal)
        self.start_response(reply)
        self.conversation_history.append({"role": "assistant", "text": reply})

    async def handle_user_command(self, text: str) -> None:
        compiled_commands = self.intent_compiler.compile(text)
        if not compiled_commands:
            logger.info("Suppressed duplicate or empty command: %s", text)
            return

        logger.info("Processing intent: %s", text)
        self.state.is_listening = False
        self.state.last_transcript = text

        try:
            for command in compiled_commands:
                intent = await asyncio.to_thread(self._classify_intent, command.normalized_text)
                if intent == "chat" and command.shape not in {
                    CommandShape.STATE_QUESTION,
                    CommandShape.HISTORY_QUESTION,
                    CommandShape.CAREER_WORKFLOW,
                }:
                    await self._handle_chat_command(command.normalized_text)
                else:
                    await self._handle_compiled_action(command)
        except Exception as exc:
            logger.exception("VoiceOrchestrator error: %s", exc)
            self.start_response(build_internal_error_reply())
        finally:
            self.interrupt()
            self.state.is_listening = True
