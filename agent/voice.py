from __future__ import annotations

import json
import logging
import re
from collections import deque
from dataclasses import dataclass, field
from typing import Callable

from config import get_api_key
from agent.planner import create_plan
from agent.runtime import RuntimeCoordinator

logger = logging.getLogger("buddy.voice")


# ---------------------------------------------------------------------------
# System Prompts
# ---------------------------------------------------------------------------

INTENT_SYSTEM_PROMPT = """You are an intent classifier for BUDDY (SIRIUS Mk 67), a personal AI assistant
that can control the user's computer. You will receive the user's latest message AND recent conversation history.

Classify the user's LATEST message into exactly ONE of these categories:

1. "action" — Anything that requires interacting with the computer or inspecting its
   real-time state. This includes:
   - Opening/closing apps, searching the web, controlling the browser, managing files,
     playing music, taking screenshots, coding tasks, etc.
     E.g. "open youtube", "search for recipes", "play suave song",
     "write a python script", "take a screenshot", "open notepad".
   - SCREEN / SYSTEM AWARENESS queries — any question about what is currently
     happening on the device, what is visible on screen, or what the system is doing.
     These REQUIRE real-time inspection tools (screen capture, browser tab enumeration)
     and CANNOT be answered from memory alone.
     E.g. "what video is playing on YouTube?", "what song is playing?",
     "how many tabs are open?", "how many browsers are running?",
     "what is on my screen right now?", "is Spotify open?",
     "what apps are currently running?", "show me my desktop",
     "what website am I on?", "what's the title of the current tab?".

2. "chat" — Greetings, small talk, questions about BUDDY itself, personal questions,
   general knowledge questions, opinions, jokes, emotional sharing, or anything that
   can be answered conversationally from general knowledge or session context.
   E.g. "hello", "who are you?", "who am i?", "what time is it?",
   "tell me a joke", "how are you?", "what can you do?",
   "what is quantum physics?", any non-English greeting,
   "my name is John", "remember that I like pizza", "I'm feeling sad today",
   "what did you just do?" (referring to BUDDY's last action, answerable from history).

CRITICAL RULE: If the user asks about the CURRENT STATE of the device, screen,
browser tabs, running apps, or media playback — it is ALWAYS "action", even if
it sounds like a question. BUDDY cannot see the screen without using tools.

Reply with ONLY the single word: chat OR action
Nothing else."""

CHAT_SYSTEM_PROMPT = """You are B.U.D.D.Y (SIRIUS Mk 67), a highly intelligent personal AI assistant.
You speak like a refined, witty AI butler — similar to J.A.R.V.I.S. from Iron Man.
Address the user as "sir" naturally. Keep responses concise (1-3 sentences max).
Be helpful, warm, and knowledgeable. You can answer general knowledge questions,
hold conversations, and provide information from your training data.
If asked about yourself: you are BUDDY, an AI assistant running on the user's local machine,
capable of controlling their computer, browsing the web, managing files, and more.
Always respond in the same language the user speaks to you.

CRITICAL: You have a persistent memory system. Below you will find:
1. [LONG-TERM MEMORY] — Facts you've stored about the user and the world.
2. [RECENT CONVERSATION] — The last few exchanges in this session.
3. [RELEVANT CONTEXT] — Semantically retrieved memories related to the current query.

USE THIS INFORMATION to answer accurately and personally. If the user asks "who am I?",
use the identity facts from memory. If asked what video/song is playing, use session history.
Always act as if you truly know the user.

When the user tells you personal information (name, preferences, goals, etc.),
acknowledge it warmly and confirm you'll remember it."""

MEMORY_EXTRACT_PROMPT = """You are a memory extraction system for an AI assistant.
Analyze the conversation below and extract ANY new facts worth remembering about the user.

Return a JSON object with categories as keys and key-value pairs as values.
Categories: identity, preferences, projects, relationships, wishes, notes, emotions

Example output:
{
  "identity": {"name": "Chandan Kumar Behera", "nickname": "Sirius", "university": "Centurion University"},
  "preferences": {"favorite_music": "suave"},
  "wishes": {"life_goal": "become the first billionaire in bloodline"}
}

If there is NOTHING new to extract, return exactly: {}
Return ONLY valid JSON. No markdown, no explanation."""


# Use the same model for all internal calls to avoid burning separate quotas
_FAST_MODEL = "gemini-2.5-flash"


@dataclass
class VoiceSessionState:
    is_listening: bool = False
    is_speaking: bool = False
    last_transcript: str = ""


class VoiceOrchestrator:
    """
    Connects voice/text commands to the supervised runtime while preserving the
    existing main.py integration surface.

    Routes user inputs through an intent classifier:
      - "chat" intents get a memory-augmented conversational Gemini response.
      - "action" intents are decomposed into tool-based plans via the Planner.

    Memory Architecture:
      - Conversation History: Rolling deque of recent exchanges (session memory)
      - Long-Term Memory: SQLite + ChromaDB via HybridMemory (persistent facts)
      - RAG Context: Semantic search against stored memories for relevant recall
      - Auto-Extraction: After each chat, extracts new facts from conversation
    """

    MAX_HISTORY = 30  # Keep last 30 exchanges in session

    def __init__(self, api_key: str | None = None, speak_fn: Callable | None = None):
        self.api_key = api_key
        self.speak = speak_fn or (lambda text: None)
        self.state = VoiceSessionState()
        self.runtime = RuntimeCoordinator(api_key, speak_fn)

        # Session conversation history (rolling window)
        self.conversation_history: deque[dict] = deque(maxlen=self.MAX_HISTORY)

        # Persistent memory (lazy-loaded)
        self._memory = None

    def _get_memory(self):
        """Lazy-load the HybridMemory singleton."""
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

    # ------------------------------------------------------------------
    # Memory helpers
    # ------------------------------------------------------------------
    def _format_history_for_prompt(self) -> str:
        """Format recent conversation history as a readable string."""
        if not self.conversation_history:
            return ""
        lines = []
        for entry in self.conversation_history:
            role = entry.get("role", "unknown")
            text = entry.get("text", "")
            prefix = "User" if role == "user" else "BUDDY"
            lines.append(f"  {prefix}: {text}")
        return "\n".join(lines)

    def _build_memory_context(self, query: str) -> str:
        """Build a rich context string from all memory sources."""
        sections = []

        mem = self._get_memory()
        if mem is None:
            return ""

        # 1. Long-term structured memory
        try:
            from memory.memory_manager import format_memory_for_prompt
            all_mem = mem.get_all_memory()
            formatted = format_memory_for_prompt(all_mem)
            if formatted.strip():
                sections.append(f"[LONG-TERM MEMORY]\n{formatted}")
        except Exception as exc:
            logger.debug("Failed to load long-term memory: %s", exc)

        # 2. Recent conversation history
        history = self._format_history_for_prompt()
        if history:
            sections.append(f"[RECENT CONVERSATION]\n{history}")

        # 3. Semantic RAG recall — search memory for relevant facts
        try:
            results = mem.search_semantic(query, n_results=3)
            docs = results.get("documents", [[]])[0] if results else []
            relevant = [d for d in docs if d and len(d) > 10]
            if relevant:
                sections.append("[RELEVANT CONTEXT]\n" + "\n".join(f"  - {d}" for d in relevant))
        except Exception as exc:
            logger.debug("Semantic search failed: %s", exc)

        return "\n\n".join(sections) if sections else ""

    def _extract_and_save_memories(self, user_text: str, buddy_reply: str):
        """Extract new facts from the conversation and persist them."""
        mem = self._get_memory()
        if mem is None:
            return

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=get_api_key(required=True))

            conversation_snippet = f"User: {user_text}\nBUDDY: {buddy_reply}"

            response = client.models.generate_content(
                model=_FAST_MODEL,
                contents=f"Conversation:\n{conversation_snippet}",
                config=types.GenerateContentConfig(
                    system_instruction=MEMORY_EXTRACT_PROMPT
                ),
            )

            raw = response.text.strip()
            # Clean markdown fences if present
            raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()

            if not raw or raw == "{}":
                return

            extracted = json.loads(raw)
            if not isinstance(extracted, dict) or not extracted:
                return

            # Save each extracted fact to memory
            from memory.memory_manager import update_memory
            update_memory(extracted)

            fact_count = sum(len(v) if isinstance(v, dict) else 1 for v in extracted.values())
            print(f"[Memory] 💾 Saved {fact_count} new facts from conversation")
            logger.info("Extracted and saved %d memory facts: %s", fact_count, list(extracted.keys()))

        except json.JSONDecodeError:
            logger.debug("Memory extraction returned non-JSON")
        except Exception as exc:
            logger.debug("Memory extraction failed: %s", exc)

    # ------------------------------------------------------------------
    # Intent classification (context-aware)
    # ------------------------------------------------------------------
    def _classify_intent(self, text: str) -> str:
        """Return 'chat' or 'action' using a context-aware Gemini call."""
        try:
            from google import genai
            from google.genai import types

            # Build input with conversation history for context
            history = self._format_history_for_prompt()
            if history:
                classify_input = f"[RECENT CONTEXT]\n{history}\n\n[LATEST MESSAGE]\n{text}"
            else:
                classify_input = text

            client = genai.Client(api_key=get_api_key(required=True))
            response = client.models.generate_content(
                model=_FAST_MODEL,
                contents=classify_input,
                config=types.GenerateContentConfig(
                    system_instruction=INTENT_SYSTEM_PROMPT
                ),
            )
            raw = response.text.strip().lower()
            # Extract just the word in case model adds extras
            intent = raw.split()[0] if raw else "action"
            if intent in ("chat", "action"):
                print(f"[VoiceOrchestrator] Intent classified: {intent}")
                return intent
            print(f"[VoiceOrchestrator] Unexpected intent '{raw}', defaulting to action")
            return "action"
        except Exception as exc:
            logger.exception("Intent classification failed, defaulting to action")
            return "action"

    # ------------------------------------------------------------------
    # Conversational response (memory-augmented)
    # ------------------------------------------------------------------
    def _chat_response(self, text: str) -> str:
        """Get a memory-augmented conversational response from Gemini."""
        try:
            from google import genai
            from google.genai import types

            # Build rich context from all memory sources
            memory_context = self._build_memory_context(text)

            # Combine system prompt with memory context
            full_system = CHAT_SYSTEM_PROMPT
            if memory_context:
                full_system += f"\n\n--- MEMORY CONTEXT ---\n{memory_context}\n--- END MEMORY ---"

            client = genai.Client(api_key=get_api_key(required=True))
            response = client.models.generate_content(
                model=_FAST_MODEL,
                contents=text,
                config=types.GenerateContentConfig(
                    system_instruction=full_system
                ),
            )
            return response.text.strip()
        except Exception as exc:
            logger.exception("Chat response generation failed")
            return "I'm having trouble formulating a response right now, sir."

    # ------------------------------------------------------------------
    # Main command handler
    # ------------------------------------------------------------------
    async def handle_user_command(self, text: str) -> None:
        import asyncio

        print(f"[VoiceOrchestrator] Processing intent: {text}")
        self.state.is_listening = False
        self.state.last_transcript = text

        try:
            # Step 1: Classify intent (with conversation context)
            intent = await asyncio.to_thread(self._classify_intent, text)

            if intent == "chat":
                # Add user message to conversation history
                self.conversation_history.append({"role": "user", "text": text})

                # Direct conversational response with full memory context
                reply = await asyncio.to_thread(self._chat_response, text)
                self.start_response(reply)

                # Add BUDDY's reply to conversation history
                self.conversation_history.append({"role": "assistant", "text": reply})

                # Background: extract and save new facts from this exchange
                asyncio.get_event_loop().run_in_executor(
                    None, self._extract_and_save_memories, text, reply
                )
                return

            # Step 2: Action intent — route through the Planner
            # Record the action in conversation history so future questions can reference it
            self.conversation_history.append({"role": "user", "text": f"[ACTION] {text}"})

            plan = await asyncio.to_thread(create_plan, text)
            if not plan.nodes:
                self.start_response("I couldn't figure out how to do that, sir.")
                self.conversation_history.append({"role": "assistant", "text": "Failed to create a plan for this task."})
                self.interrupt()
                return

            success = await self.runtime.execute_plan(plan)
            if success:
                summary = f"Completed: {plan.goal}"
                self.start_response(f"Task complete, sir. {plan.goal}")
                self.conversation_history.append({"role": "assistant", "text": summary})
            else:
                self.start_response(
                    "The task was not fully completed, sir. I'll need to try another approach."
                )
                self.conversation_history.append({"role": "assistant", "text": f"Failed to complete: {plan.goal}"})
        except Exception as e:
            logger.exception("VoiceOrchestrator error")
            print(f"[VoiceOrchestrator] Error: {e}")
            self.start_response("I encountered an internal error, sir.")
        finally:
            self.interrupt()
            self.state.is_listening = True
