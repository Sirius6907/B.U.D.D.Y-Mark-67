import asyncio
import time
from typing import Optional


class GeminiRouter:
    """
    Routes cognitive tasks through the Gemini API.
    Replaces the previous Ollama-based local model routing.
    - Fast mode: Uses gemini-2.5-flash for quick responses
    - Deep mode: Uses gemini-2.5-pro for complex reasoning
    """
    def __init__(self):
        self.fast_model = "gemini-2.5-flash"
        self.deep_model = "gemini-2.5-pro"

    async def invoke_fast(self, prompt: str, system: str = "") -> str:
        return await self._call_gemini(self.fast_model, prompt, system)

    async def invoke_deep(self, prompt: str, system: str = "") -> str:
        return await self._call_gemini(self.deep_model, prompt, system)

    async def _call_gemini(self, model: str, prompt: str, system: str) -> str:
        from google import genai
        from config import get_api_key

        print(f"[Gemini] Calling {model} ...")
        api_key = get_api_key(required=True)
        client = genai.Client(api_key=api_key)

        contents = prompt
        config = None
        if system:
            from google.genai import types
            config = types.GenerateContentConfig(
                system_instruction=system,
            )

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
        )
        return response.text


class TaskEngine:
    """
    Deterministic layer. Handles task retries without using LLM logic,
    saving massive amounts of generation time and context overhead.
    """
    def __init__(self):
        self.max_retries = 3

    async def execute_with_retry(self, action_func, *args, **kwargs):
        from buddy_logging import get_logger
        import traceback
        logger = get_logger("kernel.tasks")
        
        attempts = 0
        last_err = None
        while attempts < self.max_retries:
            try:
                res = await action_func(*args, **kwargs)
                return res
            except Exception as e:
                attempts += 1
                last_err = e
                err_msg = f"Task failed. Retry {attempts}/{self.max_retries}. Error: {e}\n{traceback.format_exc()}"
                print(f"[Kernel] ⚠️ {err_msg}")
                logger.error(err_msg)
                await asyncio.sleep(1.0)
        raise RuntimeError(f"Task failed after {self.max_retries} retries: {last_err}")


class KernelOS:
    """
    The central orchestrator of the AI OS.
    All cognition routes through cloud-based Gemini API.
    """
    def __init__(self):
        self.models = GeminiRouter()
        self.tasks = TaskEngine()

    async def initialize(self):
        print("\n[Kernel] 🟢 Booting Kernel OS...")

        # Start RAG Indexer
        try:
            from memory.memory_manager import CHROMA_PATH
            from memory.rag_indexer import get_indexer
            indexer = get_indexer(str(CHROMA_PATH))
            indexer.start_background_indexing()
            print("[Kernel] 📚 RAG Indexer started in background.")
        except Exception as e:
            print(f"[Kernel] ⚠️ Failed to start RAG Indexer: {e}")

        print("[Kernel] ✅ Cloud Gemini Engine Ready.")


# Singleton Kernel Instance
kernel = KernelOS()
