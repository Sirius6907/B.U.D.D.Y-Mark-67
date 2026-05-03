"""
agent/kernel.py — KernelOS: The Central Nervous System
=======================================================
All cognition routes through the Gemini API with intelligent routing,
client caching, circuit-breaker resilience, and health telemetry.

Architecture:
    GeminiRouter      — Cloud LLM routing (fast/deep modes) with circuit breaker
    TaskEngine        — Deterministic retry layer (no LLM overhead)
    KernelOS          — Central orchestrator singleton
    ContextManager    — Deterministic context window packer (core.memory)
    ToolRegistry      — JSON Schema-validated tool dispatch (core.tools)
    SubagentRegistry  — Hub & Spoke agent routing (core.agent)
"""
from __future__ import annotations

import asyncio
import time
import threading
from dataclasses import dataclass, field
from typing import Optional

from buddy_logging import get_logger

logger = get_logger("agent.kernel")


# ── Health & Telemetry ────────────────────────────────────────────────────────

@dataclass(slots=True)
class ModelTelemetry:
    """Per-model performance counters."""
    calls: int = 0
    errors: int = 0
    total_latency_ms: float = 0.0

    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / self.calls if self.calls else 0.0

    @property
    def error_rate(self) -> float:
        return self.errors / self.calls if self.calls else 0.0


@dataclass(slots=True)
class HealthCheck:
    """Snapshot of kernel health for monitoring."""
    status: str = "unknown"  # "healthy" | "degraded" | "down"
    uptime_seconds: float = 0.0
    fast_model: str = ""
    deep_model: str = ""
    fast_telemetry: ModelTelemetry = field(default_factory=ModelTelemetry)
    deep_telemetry: ModelTelemetry = field(default_factory=ModelTelemetry)
    circuit_open: bool = False


# ── Circuit Breaker ───────────────────────────────────────────────────────────

class CircuitBreaker:
    """
    Prevents cascading failures when the Gemini API is down.
    Opens after `threshold` consecutive failures, auto-resets after `reset_seconds`.
    """

    def __init__(self, threshold: int = 5, reset_seconds: float = 60.0):
        self.threshold = threshold
        self.reset_seconds = reset_seconds
        self._failures = 0
        self._last_failure: float = 0.0
        self._open = False
        self._lock = threading.Lock()

    @property
    def is_open(self) -> bool:
        with self._lock:
            if self._open and (time.time() - self._last_failure) > self.reset_seconds:
                logger.info("Circuit breaker auto-reset after %.0fs cooldown.", self.reset_seconds)
                self._open = False
                self._failures = 0
            return self._open

    def record_success(self) -> None:
        with self._lock:
            self._failures = 0
            self._open = False

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1
            self._last_failure = time.time()
            if self._failures >= self.threshold:
                self._open = True
                logger.error(
                    "Circuit breaker OPEN after %d consecutive failures. "
                    "Will auto-reset in %.0fs.",
                    self._failures,
                    self.reset_seconds,
                )


# ── Gemini Router ─────────────────────────────────────────────────────────────

class GeminiRouter:
    """
    Routes cognitive tasks through the Gemini API.
    - Fast mode: gemini-2.5-flash for quick responses
    - Deep mode: gemini-2.5-pro for complex reasoning

    Features:
    - Cached client instance (avoids re-creation per call)
    - Circuit breaker (prevents cascading failures on API outage)
    - Per-model telemetry (call count, latency, error rate)
    """

    def __init__(self):
        self.fast_model = "gemini-2.5-flash"
        self.deep_model = "gemini-2.5-pro"
        self._client = None
        self._client_lock = threading.Lock()
        self._circuit = CircuitBreaker(threshold=5, reset_seconds=60.0)
        self._telemetry: dict[str, ModelTelemetry] = {
            self.fast_model: ModelTelemetry(),
            self.deep_model: ModelTelemetry(),
        }

    def _get_client(self):
        """Thread-safe lazy initialization of the Gemini client."""
        if self._client is None:
            with self._client_lock:
                if self._client is None:
                    from google import genai
                    from config import get_api_key

                    api_key = get_api_key(required=True)
                    self._client = genai.Client(api_key=api_key)
                    logger.info("Gemini client initialized.")
        return self._client

    def reset_client(self) -> None:
        """Force re-creation of the client (e.g. after key rotation)."""
        with self._client_lock:
            self._client = None
            logger.info("Gemini client reset — will re-initialize on next call.")

    async def invoke_fast(self, prompt: str, system: str = "") -> str:
        return await self._call_gemini(self.fast_model, prompt, system)

    async def invoke_deep(self, prompt: str, system: str = "") -> str:
        return await self._call_gemini(self.deep_model, prompt, system)

    async def _call_gemini(self, model: str, prompt: str, system: str) -> str:
        # ── If circuit is open, skip Gemini entirely → OpenRouter fallback ──
        if self._circuit.is_open:
            logger.warning(
                "Circuit breaker OPEN — routing to OpenRouter fallback."
            )
            return await self._openrouter_fallback(prompt, system)

        telemetry = self._telemetry.get(model, ModelTelemetry())
        client = self._get_client()
        start = time.time()

        logger.info("Calling %s ...", model)

        config = None
        if system:
            from google.genai import types
            config = types.GenerateContentConfig(system_instruction=system)

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config,
                ),
            )

            elapsed_ms = (time.time() - start) * 1000
            telemetry.calls += 1
            telemetry.total_latency_ms += elapsed_ms
            self._circuit.record_success()

            logger.info(
                "%s responded in %.0fms (avg: %.0fms)",
                model,
                elapsed_ms,
                telemetry.avg_latency_ms,
            )
            return response.text

        except Exception as exc:
            elapsed_ms = (time.time() - start) * 1000
            telemetry.calls += 1
            telemetry.errors += 1
            telemetry.total_latency_ms += elapsed_ms
            self._circuit.record_failure()

            error_str = str(exc).lower()
            is_rate_limit = any(kw in error_str for kw in (
                "429", "rate", "quota", "resource exhausted", "resourceexhausted",
            ))

            logger.error(
                "%s failed after %.0fms (error rate: %.1f%%): %s",
                model,
                elapsed_ms,
                telemetry.error_rate * 100,
                exc,
            )

            # ── On rate-limit: fall through to OpenRouter instead of raising ──
            if is_rate_limit:
                logger.warning(
                    "🔄 Rate-limited on %s — falling back to OpenRouter.", model
                )
                return await self._openrouter_fallback(prompt, system)
            raise

    async def _openrouter_fallback(self, prompt: str, system: str) -> str:
        """Route through the OpenRouter free-model chain as a fallback."""
        try:
            from agent.llm_gateway import llm_generate
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: llm_generate(prompt, system=system, skip_gemini=True),
            )
            logger.info(
                "✅ OpenRouter fallback: %s (tier %d, %.0fms)",
                result.model, result.tier, result.latency_ms,
            )
            return result.text
        except Exception as fallback_exc:
            logger.error("❌ OpenRouter fallback also failed: %s", fallback_exc)
            raise RuntimeError(
                f"All LLM backends exhausted. Gemini and OpenRouter both failed."
            ) from fallback_exc

    def get_telemetry(self) -> dict[str, ModelTelemetry]:
        return dict(self._telemetry)


# ── Task Engine ───────────────────────────────────────────────────────────────

class TaskEngine:
    """
    Deterministic retry layer. Handles task retries without using LLM logic,
    saving massive amounts of generation time and context overhead.
    Uses exponential backoff between retries.
    """

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    async def execute_with_retry(self, action_func, *args, **kwargs):
        attempts = 0
        last_err = None

        while attempts < self.max_retries:
            try:
                res = await action_func(*args, **kwargs)
                return res
            except Exception as e:
                attempts += 1
                last_err = e
                backoff = min(2 ** attempts, 10)  # exponential backoff: 2, 4, 8 (capped at 10)
                logger.error(
                    "Task failed (attempt %d/%d, backoff %.1fs): %s",
                    attempts,
                    self.max_retries,
                    backoff,
                    e,
                )
                await asyncio.sleep(backoff)

        raise RuntimeError(f"Task failed after {self.max_retries} retries: {last_err}")


# ── KernelOS ──────────────────────────────────────────────────────────────────

class KernelOS:
    """
    The central orchestrator of the AI OS.
    All cognition routes through cloud-based Gemini API with resilience guarantees.

    Subsystems:
        models   — GeminiRouter for fast/deep LLM calls
        tasks    — TaskEngine for deterministic retries
        context  — ContextManager for deterministic prompt packing
        tools    — ToolRegistry for schema-validated tool dispatch
        agents   — SubagentRegistry for hub-and-spoke routing
    """

    VERSION = "2.0.0"

    def __init__(self):
        self.models = GeminiRouter()
        self.tasks = TaskEngine()
        self._boot_time: float = 0.0
        self._initialized = False
        self.loop: Optional[asyncio.AbstractEventLoop] = None

        # ── New Core Subsystems ───────────────────────────────────────────
        from core.memory.context_manager import ContextManager, SlotPriority
        from core.tools.registry import ToolRegistry
        from core.agent.subagent_registry import (
            SubagentRegistry, SubagentSpec, AgentCapability,
        )
        from core.tools.mcp_manager import MCPManager
        from registries.capability_registry import CapabilityRegistry

        self.context = ContextManager(max_chars=12000)
        self.tools = ToolRegistry()
        self.capabilities = CapabilityRegistry()
        self.agents = SubagentRegistry()
        self.mcp = MCPManager(self.tools)  # On-demand MCP server manager

        # Register default subagents
        self._register_default_agents(SubagentSpec, AgentCapability)

    def _register_default_agents(self, SubagentSpec, AgentCapability):
        """Bootstrap the standard subagent roster."""
        self.agents.register(SubagentSpec(
            name="chat_agent",
            description="General conversation and Q&A",
            capabilities={AgentCapability.CHAT, AgentCapability.MEMORY},
            tool_names=["web_search", "weather_report"],
            priority=40,
        ))
        self.agents.register(SubagentSpec(
            name="system_agent",
            description="OS control, app launching, desktop automation, MCP server management",
            capabilities={
                AgentCapability.SYSTEM_CONTROL,
                AgentCapability.FILE_MANAGEMENT,
            },
            tool_names=[
                "open_app", "desktop_control", "computer_control",
                "computer_settings", "file_controller", "app_optimizer",
                "maintenance_manager", "recovery_manager",
                "mcp_controller",
            ],
            priority=70,
        ))
        self.agents.register(SubagentSpec(
            name="code_agent",
            description="Code generation, dev tooling, project scaffolding",
            capabilities={AgentCapability.CODE},
            tool_names=["code_helper", "dev_agent", "generated_code"],
            priority=80,
        ))
        self.agents.register(SubagentSpec(
            name="web_agent",
            description="Web browsing, search, media playback",
            capabilities={
                AgentCapability.WEB_SEARCH,
                AgentCapability.MEDIA,
            },
            tool_names=[
                "web_search", "browser_control", "youtube_video",
                "flight_finder",
            ],
            priority=60,
        ))
        self.agents.register(SubagentSpec(
            name="security_agent",
            description="Security monitoring, network hardening, privacy",
            capabilities={AgentCapability.SYSTEM_CONTROL},
            tool_names=[
                "access_monitor", "network_security", "process_shield",
                "vault_manager", "privacy_hardener",
            ],
            priority=65,
        ))
        self.agents.register(SubagentSpec(
            name="screen_agent",
            description="Screen capture, analysis, and recording",
            capabilities={AgentCapability.SCREEN},
            tool_names=["screen_process", "screen_recorder"],
            priority=55,
        ))
        logger.info(
            "Registered %d default subagents.", len(self.agents),
        )

    async def initialize(self) -> None:
        logger.info("Booting KernelOS v%s ...", self.VERSION)
        self.loop = asyncio.get_running_loop()
        self._boot_time = time.time()

        # ── Initialize Tool Registry from legacy actions ──────────────────
        tool_count = self.tools.bulk_register_from_action_registry()
        self._sync_capabilities()
        logger.info("Tool registry initialized: %d tools loaded.", tool_count)

        # ── Set up default context slots ──────────────────────────────────
        from core.memory.context_manager import SlotPriority
        self.context.upsert(
            "system_prompt",
            (
                "You are BUDDY MARK LXVII, an advanced AI assistant created by Sirius. "
                "You control the user's computer, manage files, browse the web, "
                "write code, and handle system administration. "
                "Address the user as 'buddy'. Be direct and efficient."
            ),
            SlotPriority.SYSTEM_PROMPT,
            compressible=False,
        )

        # ── Start RAG Indexer ─────────────────────────────────────────────
        try:
            from memory.memory_manager import CHROMA_PATH
            from memory.rag_indexer import get_indexer

            indexer = get_indexer(str(CHROMA_PATH))
            indexer.start_background_indexing()
            logger.info("RAG Indexer started in background.")
        except Exception as e:
            logger.warning("Failed to start RAG Indexer: %s", e)

        self._initialized = True
        logger.info(
            "KernelOS v%s boot complete. "
            "%d tools, %d agents, context budget=%d chars.",
            self.VERSION,
            len(self.tools),
            len(self.agents),
            self.context._max_chars,
        )

    def health(self) -> HealthCheck:
        """Return a snapshot of kernel health for monitoring/dashboards."""
        telemetry = self.models.get_telemetry()
        fast_t = telemetry.get(self.models.fast_model, ModelTelemetry())
        deep_t = telemetry.get(self.models.deep_model, ModelTelemetry())

        if self.models._circuit.is_open:
            status = "down"
        elif fast_t.error_rate > 0.3 or deep_t.error_rate > 0.3:
            status = "degraded"
        elif self._initialized:
            status = "healthy"
        else:
            status = "unknown"

        return HealthCheck(
            status=status,
            uptime_seconds=time.time() - self._boot_time if self._boot_time else 0.0,
            fast_model=self.models.fast_model,
            deep_model=self.models.deep_model,
            fast_telemetry=fast_t,
            deep_telemetry=deep_t,
            circuit_open=self.models._circuit.is_open,
        )

    def get_full_status(self) -> dict:
        """Return comprehensive system status including all subsystems."""
        health = self.health()
        return {
            "kernel": {
                "version": self.VERSION,
                "status": health.status,
                "uptime_seconds": round(health.uptime_seconds, 1),
                "circuit_open": health.circuit_open,
            },
            "context": self.context.get_stats(),
            "tools": self.tools.get_stats(),
            "agents": self.agents.get_stats(),
            "mcp": self.mcp.get_status(),
        }

    def _sync_capabilities(self) -> None:
        from registries.capability_registry import CapabilitySpec

        for tool_name in self.tools.list_tools():
            spec = self.tools.get_spec(tool_name)
            if spec is None:
                continue
            self.capabilities.register(
                CapabilitySpec(
                    tool_name=spec.name,
                    domain=spec.domain,
                    operation=spec.operation,
                    aliases=list(spec.aliases),
                    risk_level=spec.risk_tier.name,
                    idempotent=spec.idempotent,
                    preconditions=list(spec.preconditions),
                    postconditions=list(spec.postconditions),
                    verification_mode=spec.verification_mode,
                )
            )

    async def shutdown(self) -> None:
        """Graceful shutdown — clean up resources."""
        logger.info("KernelOS shutting down...")
        self.mcp.shutdown_all()  # Terminate all subordinate MCP servers
        self.models.reset_client()
        self.context.clear()
        self.agents.deactivate_current()
        self._initialized = False
        logger.info("KernelOS shutdown complete.")


# ── Singleton ─────────────────────────────────────────────────────────────────
kernel = KernelOS()
