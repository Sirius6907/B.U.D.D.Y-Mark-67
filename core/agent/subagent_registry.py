"""
core/agent/subagent_registry.py — Hub & Spoke Subagent Lifecycle Manager
=========================================================================
Inspired by OpenClaw's routing/resolve-route.ts and context-engine/registry.ts.
Implements a deterministic agent routing system where the KernelOS acts as
the central hub and delegates to specialized subagents.

Architecture:
    SubagentSpec     — Declaration of a subagent (name, capabilities, tools)
    SubagentRegistry — Manages registration, routing, and lifecycle

Design Principles (from OpenClaw reverse-engineering):
    1. Capability-based routing — match user intent to agent expertise.
    2. Tool isolation — each subagent has access to specific tools only.
    3. Lifecycle management — agents are spawned, tracked, and cleaned up.
    4. Priority routing — when multiple agents match, highest priority wins.
"""
from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Callable

from buddy_logging import get_logger

logger = get_logger("core.agent.subagent")


# ── Agent States ──────────────────────────────────────────────────────────────

class AgentState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"


class AgentCapability(str, Enum):
    """Capability tags for routing decisions."""
    CHAT = "chat"                        # General conversation
    CODE = "code"                        # Code generation / editing
    SYSTEM_CONTROL = "system_control"    # OS/app automation
    WEB_SEARCH = "web_search"            # Internet research
    FILE_MANAGEMENT = "file_management"  # File CRUD
    VOICE_CONTROL = "voice_control"      # Voice-specific actions
    MEMORY = "memory"                    # Memory read/write
    MEDIA = "media"                      # Media playback / control
    SCREEN = "screen"                    # Screen capture / analysis


# ── Subagent Spec ─────────────────────────────────────────────────────────────

@dataclass
class SubagentSpec:
    """
    Declaration of a subagent with its capabilities and tool access.

    Attributes:
        name:           Unique agent identifier
        description:    What this agent specializes in
        capabilities:   Set of capability tags for routing
        tool_names:     Tools this agent is allowed to call
        priority:       Routing priority (higher = preferred)
        system_prompt:  Custom system prompt override for this agent
        max_turns:      Max conversation turns before forced termination
        on_activate:    Optional callback when agent is activated
    """
    name: str
    description: str
    capabilities: set[AgentCapability]
    tool_names: list[str] = field(default_factory=list)
    priority: int = 50
    system_prompt: Optional[str] = None
    max_turns: int = 20
    on_activate: Optional[Callable] = None

    # Runtime state
    state: AgentState = field(default=AgentState.IDLE, repr=False)
    turn_count: int = field(default=0, repr=False)
    activated_at: Optional[float] = field(default=None, repr=False)
    total_calls: int = field(default=0, repr=False)


# ── Routing Result ────────────────────────────────────────────────────────────

@dataclass
class RoutingResult:
    """Result of a routing decision."""
    agent: SubagentSpec
    confidence: float  # 0.0 to 1.0
    matched_capabilities: set[AgentCapability]
    reason: str


@dataclass
class TextRoutingResult:
    """Lightweight routing result for text-based (voice) routing."""
    name: str
    score: float
    reason: str


# ── Subagent Registry ────────────────────────────────────────────────────────

class SubagentRegistry:
    """
    Hub-and-Spoke routing registry for subagents.

    Usage:
        registry = SubagentRegistry()
        registry.register(SubagentSpec(
            name="code_agent",
            description="Code generation and editing",
            capabilities={AgentCapability.CODE},
            tool_names=["write_file", "read_file", "run_code"],
            priority=80,
        ))

        result = registry.route({AgentCapability.CODE})
        agent = result.agent
    """

    def __init__(self):
        self._agents: dict[str, SubagentSpec] = {}
        self._active_agent: Optional[str] = None
        self._lock = threading.Lock()
        self._history: list[dict] = []  # Routing decision history

    # ── Registration ──────────────────────────────────────────────────────

    def register(self, spec: SubagentSpec) -> None:
        """Register a subagent specification."""
        with self._lock:
            if spec.name in self._agents:
                logger.warning("Overwriting agent registration: '%s'", spec.name)
            self._agents[spec.name] = spec

        logger.debug(
            "Registered subagent: '%s' (caps=%s, priority=%d, tools=%d)",
            spec.name,
            [c.value for c in spec.capabilities],
            spec.priority,
            len(spec.tool_names),
        )

    def unregister(self, name: str) -> bool:
        """Remove a subagent from the registry."""
        with self._lock:
            removed = self._agents.pop(name, None)
            if self._active_agent == name:
                self._active_agent = None
        return removed is not None

    # ── Text-Based Routing ────────────────────────────────────────────────

    # Keyword → capability mapping for natural-language routing
    _TEXT_CAPABILITY_MAP: dict[str, AgentCapability] = {
        # System control
        "open": AgentCapability.SYSTEM_CONTROL,
        "close": AgentCapability.SYSTEM_CONTROL,
        "launch": AgentCapability.SYSTEM_CONTROL,
        "shutdown": AgentCapability.SYSTEM_CONTROL,
        "restart": AgentCapability.SYSTEM_CONTROL,
        "settings": AgentCapability.SYSTEM_CONTROL,
        "mcp": AgentCapability.SYSTEM_CONTROL,
        "openclaw": AgentCapability.SYSTEM_CONTROL,
        "server": AgentCapability.SYSTEM_CONTROL,
        "app": AgentCapability.SYSTEM_CONTROL,
        # File management
        "file": AgentCapability.FILE_MANAGEMENT,
        "folder": AgentCapability.FILE_MANAGEMENT,
        "directory": AgentCapability.FILE_MANAGEMENT,
        "copy": AgentCapability.FILE_MANAGEMENT,
        "move": AgentCapability.FILE_MANAGEMENT,
        "delete": AgentCapability.FILE_MANAGEMENT,
        "rename": AgentCapability.FILE_MANAGEMENT,
        # Code
        "code": AgentCapability.CODE,
        "script": AgentCapability.CODE,
        "program": AgentCapability.CODE,
        "python": AgentCapability.CODE,
        "function": AgentCapability.CODE,
        "debug": AgentCapability.CODE,
        "compile": AgentCapability.CODE,
        # Web
        "search": AgentCapability.WEB_SEARCH,
        "browse": AgentCapability.WEB_SEARCH,
        "website": AgentCapability.WEB_SEARCH,
        "google": AgentCapability.WEB_SEARCH,
        "url": AgentCapability.WEB_SEARCH,
        # Media
        "play": AgentCapability.MEDIA,
        "music": AgentCapability.MEDIA,
        "video": AgentCapability.MEDIA,
        "youtube": AgentCapability.MEDIA,
        "song": AgentCapability.MEDIA,
        # Screen
        "screenshot": AgentCapability.SCREEN,
        "screen": AgentCapability.SCREEN,
        "record": AgentCapability.SCREEN,
        "capture": AgentCapability.SCREEN,
    }

    def route_by_text(self, text: str) -> Optional["TextRoutingResult"]:
        """
        Route to the best agent using natural-language keyword matching.

        This is the primary entry point for voice.py — it infers capabilities
        from the user's raw text and delegates to the capability-based router.

        Returns a lightweight TextRoutingResult with name and score,
        or None if no match.
        """
        words = set(text.lower().split())
        inferred: set[AgentCapability] = set()

        for keyword, cap in self._TEXT_CAPABILITY_MAP.items():
            if keyword in words:
                inferred.add(cap)

        if not inferred:
            # Default to system control for unrecognized action intents
            inferred = {AgentCapability.SYSTEM_CONTROL}

        result = self.route(inferred)
        if not result:
            return None

        return TextRoutingResult(
            name=result.agent.name,
            score=result.confidence,
            reason=result.reason,
        )

    # ── Capability-Based Routing ──────────────────────────────────────────

    def route(
        self,
        required_capabilities: set[AgentCapability],
        preferred_agent: Optional[str] = None,
    ) -> Optional[RoutingResult]:
        """
        Route to the best subagent based on required capabilities.

        Strategy (inspired by OpenClaw's resolve-route.ts):
        1. If preferred_agent is specified and capable, use it.
        2. Score all agents by capability overlap and priority.
        3. Return highest-scoring agent.
        """
        with self._lock:
            # Step 1: Preferred agent shortcut
            if preferred_agent and preferred_agent in self._agents:
                agent = self._agents[preferred_agent]
                overlap = required_capabilities & agent.capabilities
                if overlap or not required_capabilities:
                    return RoutingResult(
                        agent=agent,
                        confidence=1.0,
                        matched_capabilities=overlap,
                        reason=f"Preferred agent '{preferred_agent}' selected",
                    )

            # Step 2: Score all agents
            candidates: list[tuple[float, SubagentSpec, set]] = []

            for agent in self._agents.values():
                if agent.state == AgentState.TERMINATED:
                    continue

                overlap = required_capabilities & agent.capabilities
                if not overlap and required_capabilities:
                    continue

                # Score = (coverage ratio * 60) + (priority * 0.4)
                if required_capabilities:
                    coverage = len(overlap) / len(required_capabilities)
                else:
                    coverage = 0.5  # Neutral if no specific caps required

                score = (coverage * 60) + (agent.priority * 0.4)
                candidates.append((score, agent, overlap))

            if not candidates:
                logger.warning(
                    "No agent found for capabilities: %s",
                    [c.value for c in required_capabilities],
                )
                return None

            # Step 3: Pick highest score
            candidates.sort(key=lambda x: x[0], reverse=True)
            score, best, overlap = candidates[0]

            confidence = min(1.0, score / 100.0)
            result = RoutingResult(
                agent=best,
                confidence=confidence,
                matched_capabilities=overlap,
                reason=f"Best match by score ({score:.1f}): {best.name}",
            )

            # Record routing history
            self._history.append({
                "timestamp": time.time(),
                "required": [c.value for c in required_capabilities],
                "selected": best.name,
                "confidence": confidence,
            })

            return result

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def activate(self, name: str) -> bool:
        """Activate a subagent, deactivating the current one."""
        with self._lock:
            agent = self._agents.get(name)
            if not agent:
                return False

            # Deactivate current
            if self._active_agent and self._active_agent in self._agents:
                current = self._agents[self._active_agent]
                current.state = AgentState.IDLE
                logger.debug("Deactivated agent: '%s'", self._active_agent)

            # Activate new
            agent.state = AgentState.RUNNING
            agent.activated_at = time.time()
            agent.turn_count = 0
            agent.total_calls += 1
            self._active_agent = name

            if agent.on_activate:
                try:
                    agent.on_activate()
                except Exception as exc:
                    logger.error("Agent '%s' on_activate failed: %s", name, exc)

            logger.info("Activated subagent: '%s'", name)
            return True

    def deactivate_current(self) -> None:
        """Deactivate the currently active agent."""
        with self._lock:
            if self._active_agent and self._active_agent in self._agents:
                self._agents[self._active_agent].state = AgentState.IDLE
                logger.debug("Deactivated agent: '%s'", self._active_agent)
                self._active_agent = None

    def increment_turn(self) -> bool:
        """
        Increment turn counter for active agent.
        Returns False if max_turns exceeded (agent should be terminated).
        """
        with self._lock:
            if not self._active_agent:
                return True

            agent = self._agents.get(self._active_agent)
            if not agent:
                return True

            agent.turn_count += 1
            if agent.turn_count >= agent.max_turns:
                logger.warning(
                    "Agent '%s' exceeded max turns (%d/%d)",
                    agent.name, agent.turn_count, agent.max_turns,
                )
                agent.state = AgentState.TERMINATED
                self._active_agent = None
                return False

            return True

    # ── Introspection ─────────────────────────────────────────────────────

    @property
    def active_agent(self) -> Optional[SubagentSpec]:
        """Return the currently active subagent."""
        if self._active_agent:
            return self._agents.get(self._active_agent)
        return None

    def get_agent(self, name: str) -> Optional[SubagentSpec]:
        """Get a specific agent by name."""
        return self._agents.get(name)

    def list_agents(self) -> list[str]:
        """Return all registered agent names."""
        return list(self._agents.keys())

    def get_available_tools(self, agent_name: Optional[str] = None) -> list[str]:
        """Return tools available to a specific agent or the active one."""
        name = agent_name or self._active_agent
        if not name:
            return []
        agent = self._agents.get(name)
        return agent.tool_names if agent else []

    def get_stats(self) -> dict:
        """Return stats about the subagent registry."""
        return {
            "total_agents": len(self._agents),
            "active_agent": self._active_agent,
            "routing_decisions": len(self._history),
            "agents": {
                name: {
                    "state": agent.state.value,
                    "capabilities": [c.value for c in agent.capabilities],
                    "priority": agent.priority,
                    "total_calls": agent.total_calls,
                    "tools": len(agent.tool_names),
                }
                for name, agent in self._agents.items()
            },
        }

    def get_routing_history(self, limit: int = 10) -> list[dict]:
        """Return recent routing decisions."""
        return self._history[-limit:]

    def __contains__(self, name: str) -> bool:
        return name in self._agents

    def __len__(self) -> int:
        return len(self._agents)

    def __repr__(self) -> str:
        return (
            f"<SubagentRegistry agents={len(self._agents)} "
            f"active={self._active_agent or 'none'}>"
        )
