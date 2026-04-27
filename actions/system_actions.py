import asyncio
import concurrent.futures
import threading
import sys
import os
import time

from actions.base import Action, ActionRegistry
from agent.personality import (
    build_task_failed_reply,
    build_shutdown_farewell,
)
from agent.task_queue import get_queue, TaskPriority
from agent.kernel import kernel
from memory.memory_manager import update_memory, search_local_files
from agent.planner import create_plan

class ShutdownBuddyAction(Action):
    @property
    def name(self) -> str:
        return "shutdown_buddy"

    @property
    def description(self) -> str:
        return (
            "Shuts down the assistant completely. "
            "Call this when the user expresses intent to end the conversation, "
            "close the assistant, say goodbye, or stop Buddy. "
            "The user can say this in ANY language."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {},
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        if player:
            player.write_log("SYS: Shutdown requested.")
        farewell = build_shutdown_farewell()
        speech_future = None
        if speak:
            speech_future = speak(farewell)

        def _shutdown():
            if isinstance(speech_future, concurrent.futures.Future):
                try:
                    speech_future.result(timeout=15)
                except Exception:
                    pass
            else:
                time.sleep(1)
            try:
                if player and hasattr(player, "bridge"):
                    player.bridge.publish_shutdown_requested(farewell)
            except Exception:
                pass
            time.sleep(1.8)
            try:
                if player and hasattr(player, "root"):
                    player.root.quit()
            except Exception:
                pass
            time.sleep(4)
            os._exit(0)

        threading.Thread(target=_shutdown, daemon=True).start()
        return "Shutting down."

class SaveMemoryAction(Action):
    @property
    def name(self) -> str:
        return "save_memory"

    @property
    def description(self) -> str:
        return (
            "Save an important personal fact about the user to long-term memory. "
            "Call this silently whenever the user reveals something worth remembering: "
            "name, age, city, job, preferences, hobbies, relationships, projects, or future plans. "
            "Do NOT call for: weather, reminders, searches, or one-time commands. "
            "Do NOT announce that you are saving — just call it silently. "
            "Values must be in English regardless of the conversation language."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "category": {
                    "type": "STRING",
                    "description": (
                        "identity — name, age, birthday, city, job, language, nationality | "
                        "preferences — favorite food/color/music/film/game/sport, hobbies | "
                        "projects — active projects, goals, things being built | "
                        "relationships — friends, family, partner, colleagues | "
                        "wishes — future plans, things to buy, travel dreams | "
                        "notes — habits, schedule, anything else worth remembering"
                    )
                },
                "key":   {"type": "STRING", "description": "Short snake_case key (e.g. name, favorite_food, sister_name)"},
                "value": {"type": "STRING", "description": "Concise value in English (e.g. Fatih, pizza, older sister)"},
            },
            "required": ["category", "key", "value"]
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        category = parameters.get("category", "notes")
        key      = parameters.get("key", "")
        value    = parameters.get("value", "")
        
        if key and value:
            update_memory({category: {key: {"value": value}}})
            print(f"[Memory] 💾 save_memory: {category}/{key} = {value}")
            
        return "Memory saved."

class LocalTaskAction(Action):
    @property
    def name(self) -> str:
        return "local_task"

    @property
    def description(self) -> str:
        return (
            "Executes a cognitive task using the Gemini brain. "
            "Use for private reasoning, quick answers, or when a focused LLM response is preferred. "
            "Supports 'fast' (Gemini Flash) and 'deep' (Gemini Pro) modes."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "prompt": {"type": "STRING", "description": "The task or question for the brain"},
                "mode":   {"type": "STRING", "description": "fast | deep (default: fast)"}
            },
            "required": ["prompt"]
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        prompt = parameters.get("prompt", "")
        mode   = parameters.get("mode", "fast").lower()
        loop = kernel.loop or asyncio.get_event_loop()
        
        if mode == "deep":
            future = asyncio.run_coroutine_threadsafe(kernel.models.invoke_deep(prompt), loop)
            return future.result()
        else:
            future = asyncio.run_coroutine_threadsafe(kernel.models.invoke_fast(prompt), loop)
            return future.result()

class RuntimeOrchestratorAction(Action):
    @property
    def name(self) -> str:
        return "runtime_orchestrator"

    @property
    def description(self) -> str:
        return (
            "The ELITE TIER execution engine. Use for complex, high-risk, or multi-step tasks "
            "that require strict verification, policy checks, and learning from past experience. "
            "This is 10000x more powerful than standard agent_task."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "goal": {"type": "STRING", "description": "The complex goal to achieve"}
            },
            "required": ["goal"]
        }

    def execute(self, parameters: dict, player=None, speak=None, orchestrator=None, **kwargs) -> str:
        goal = parameters.get("goal", "")
        plan = create_plan(goal)
        
        if orchestrator and hasattr(orchestrator, "runtime"):
            loop = kernel.loop or asyncio.get_event_loop()
            future = asyncio.run_coroutine_threadsafe(orchestrator.runtime.execute_plan(plan), loop)
            success = future.result()
            return (
                "I handled that full workflow for you, Buddy."
                if success
                else build_task_failed_reply()
            )
        else:
            return "I could not reach the deeper runtime for that one, Buddy."

class LocalKnowledgeSearchAction(Action):
    @property
    def name(self) -> str:
        return "local_knowledge_search"

    @property
    def description(self) -> str:
        return (
            "Searches through the user's local documents, code, and files indexed via RAG. "
            "Use this when the user asks about their own files, projects, or local information "
            "that wouldn't be on the web."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "query": {"type": "STRING", "description": "The search query for local files"}
            },
            "required": ["query"]
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        query = parameters.get("query", "")
        results = search_local_files(query, n_results=5)

        if not results or not results.get('documents') or not results['documents'][0]:
            return "No relevant local information found."

        formatted_results = ["[LOCAL KNOWLEDGE SEARCH RESULTS]"]
        for i in range(len(results['documents'][0])):
            doc = results['documents'][0][i]
            meta = results['metadatas'][0][i]
            path = meta.get('file_path', 'Unknown')
            formatted_results.append(f"\nSource: {path}\nContent: {doc}")

        return "\n".join(formatted_results)

class AgentTaskAction(Action):
    @property
    def name(self) -> str:
        return "agent_task"

    @property
    def description(self) -> str:
        return (
            "Executes complex multi-step tasks requiring multiple different tools. "
            "Examples: 'research X and save to file', 'find and organize files'. "
            "DO NOT use for single commands. NEVER use for Steam/Epic — use game_updater."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "goal":     {"type": "STRING", "description": "Complete description of what to accomplish"},
                "priority": {"type": "STRING", "description": "low | normal | high (default: normal)"}
            },
            "required": ["goal"]
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        priority_map = {"low": TaskPriority.LOW, "normal": TaskPriority.NORMAL, "high": TaskPriority.HIGH}
        priority = priority_map.get(parameters.get("priority", "normal").lower(), TaskPriority.NORMAL)
        task_id  = get_queue().submit(goal=parameters.get("goal", ""), priority=priority, speak=speak)
        return f"I have started working on that for you, Buddy. Tracking ID: {task_id}."

ActionRegistry.register(ShutdownBuddyAction)
ActionRegistry.register(SaveMemoryAction)
ActionRegistry.register(LocalTaskAction)
ActionRegistry.register(RuntimeOrchestratorAction)
ActionRegistry.register(LocalKnowledgeSearchAction)
ActionRegistry.register(AgentTaskAction)
