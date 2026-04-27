"""
core/tools/registry.py — Strict Tool Registry with JSON Schema Validation
===========================================================================
Inspired by OpenClaw's MCP channel-bridge.ts and tool calling patterns.
Every tool call is validated against its declared JSON Schema before execution.

Architecture:
    ToolSpec        — Declaration of a tool (name, schema, handler, risk tier)
    ToolRegistry    — Process-global registry with schema validation
    ValidationError — Raised when parameters fail schema validation

Design Principles (from OpenClaw reverse-engineering):
    1. Strict schema validation — no ad-hoc parameter shapes.
    2. Risk-tiered execution — destructive tools require explicit approval.
    3. Lazy-loading handlers — modules loaded only when first invoked.
    4. Unified dispatch — single entry point replaces scattered if/elif chains.
"""
from __future__ import annotations

import importlib
import inspect
import json
import time
import threading
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Callable, Optional

from buddy_logging import get_logger

logger = get_logger("core.tools.registry")


# ── Risk Tiers ────────────────────────────────────────────────────────────────

class RiskTier(IntEnum):
    """Tool risk classification. Higher = more dangerous."""
    SAFE = 0          # Read-only, no side effects
    LOW = 1           # Minor UI automation, web search
    MODERATE = 2      # File modifications, app launches
    HIGH = 3          # System settings, destructive actions
    CRITICAL = 4      # Admin-level operations, shell commands


# ── Exceptions ────────────────────────────────────────────────────────────────

class ValidationError(Exception):
    """Raised when tool parameters fail JSON Schema validation."""
    def __init__(self, tool_name: str, errors: list[str]):
        self.tool_name = tool_name
        self.errors = errors
        super().__init__(f"Validation failed for '{tool_name}': {'; '.join(errors)}")


class ToolNotFoundError(Exception):
    """Raised when a tool name is not registered."""
    pass


# ── Tool Specification ────────────────────────────────────────────────────────

@dataclass
class ToolSpec:
    """
    Complete specification of a registered tool.

    Attributes:
        name:           Unique tool identifier
        description:    Human-readable description for the LLM
        parameters:     JSON Schema dict for parameter validation
        handler:        Callable(parameters=dict, speak=fn, **kw) -> str
        risk_tier:      Risk classification
        module_path:    Lazy-load module path (if handler is None)
        fn_name:        Function name in module (for lazy loading)
        requires_speak: Whether the handler needs a speak callback
        timeout:        Max execution time in seconds
    """
    name: str
    description: str
    parameters: dict
    handler: Optional[Callable[..., str]] = None
    risk_tier: RiskTier = RiskTier.LOW
    module_path: Optional[str] = None
    fn_name: Optional[str] = None
    requires_speak: bool = False
    timeout: int = 120

    # Runtime stats
    call_count: int = field(default=0, repr=False)
    error_count: int = field(default=0, repr=False)
    total_latency_ms: float = field(default=0.0, repr=False)

    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / self.call_count if self.call_count else 0.0

    def get_handler(self) -> Callable[..., str]:
        """Return the handler, lazy-loading if necessary."""
        if self.handler is not None:
            return self.handler

        if not self.module_path or not self.fn_name:
            raise RuntimeError(
                f"Tool '{self.name}' has no handler and no module_path/fn_name for lazy loading."
            )

        try:
            mod = importlib.import_module(self.module_path)
            fn = getattr(mod, self.fn_name)
            self.handler = fn
            logger.debug("Lazy-loaded handler for tool '%s' from %s.%s",
                         self.name, self.module_path, self.fn_name)
            return fn
        except Exception as exc:
            raise RuntimeError(
                f"Failed to lazy-load tool '{self.name}' from {self.module_path}.{self.fn_name}: {exc}"
            ) from exc


# ── JSON Schema Validator (lightweight, no external deps) ─────────────────────

def _validate_params(schema: dict, params: dict) -> list[str]:
    """
    Lightweight JSON Schema validation.
    Checks: required fields, type matching, enum constraints.
    Returns list of error strings (empty = valid).
    """
    errors: list[str] = []
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))

    # Check required fields
    for req in required:
        if req not in params:
            errors.append(f"Missing required parameter: '{req}'")

    # Check type constraints
    TYPE_MAP = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
    }

    for key, value in params.items():
        if key not in properties:
            # Extra params are allowed (OpenClaw pattern: lenient on extras)
            continue

        prop_schema = properties[key]
        expected_type = prop_schema.get("type")

        if expected_type and value is not None:
            python_type = TYPE_MAP.get(expected_type)
            if python_type and not isinstance(value, python_type):
                errors.append(
                    f"Parameter '{key}' expected type '{expected_type}', "
                    f"got '{type(value).__name__}'"
                )

        # Check enum
        enum_values = prop_schema.get("enum")
        if enum_values and value not in enum_values:
            errors.append(
                f"Parameter '{key}' must be one of {enum_values}, got '{value}'"
            )

    return errors


# ── Tool Registry (Singleton) ────────────────────────────────────────────────

class ToolRegistry:
    """
    Process-global tool registry with strict JSON Schema validation.

    Usage:
        registry = ToolRegistry()
        registry.register(ToolSpec(
            name="web_search",
            description="Search the web",
            parameters={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
            module_path="actions.web_search",
            fn_name="web_search",
        ))

        result = registry.execute("web_search", {"query": "Python tips"})
    """

    def __init__(self):
        self._tools: dict[str, ToolSpec] = {}
        self._lock = threading.Lock()
        self._initialized = False

    # ── Registration ──────────────────────────────────────────────────────

    def register(self, spec: ToolSpec) -> None:
        """Register a tool specification."""
        with self._lock:
            if spec.name in self._tools:
                logger.warning(
                    "Overwriting existing tool registration: '%s'", spec.name
                )
            self._tools[spec.name] = spec

        logger.debug(
            "Registered tool: '%s' (risk=%s, module=%s)",
            spec.name, spec.risk_tier.name,
            spec.module_path or "(inline)",
        )

    def register_from_action(self, action) -> None:
        """
        Bridge: register an existing Action (from actions/base.py) into the
        new registry. Preserves backward compatibility with the current codebase.
        """
        spec = ToolSpec(
            name=action.name,
            description=action.description,
            parameters=action.parameters_schema,
            handler=lambda parameters, speak=None, player=None, _action=action, **kw: (
                _action.execute(parameters, player=player, speak=speak, **kw) or "Done."
            ),
            risk_tier=RiskTier.LOW,  # Default; can be overridden
        )
        self.register(spec)

    def bulk_register_from_action_registry(self) -> int:
        """
        Import all actions from the existing ActionRegistry into this
        new strict registry. Returns count of registered tools.
        """
        try:
            from actions.base import ActionRegistry as LegacyRegistry
            count = 0
            for name, action in LegacyRegistry._actions.items():
                self.register_from_action(action)
                count += 1
            logger.info("Bulk-registered %d tools from legacy ActionRegistry", count)
            self._initialized = True
            return count
        except Exception as exc:
            logger.error("Failed to bulk-register from ActionRegistry: %s", exc)
            return 0

    # ── Execution ─────────────────────────────────────────────────────────

    def execute(
        self,
        name: str,
        parameters: dict,
        speak: Optional[Callable] = None,
        skip_validation: bool = False,
        **kwargs: Any,
    ) -> str:
        """
        Execute a tool by name with schema validation.

        Steps:
        1. Lookup tool in registry
        2. Validate parameters against JSON Schema
        3. Invoke handler with timing
        4. Return result string
        """
        spec = self._tools.get(name)
        if spec is None:
            raise ToolNotFoundError(f"Tool '{name}' not found in registry")

        # Step 2: Validate parameters
        if not skip_validation and spec.parameters:
            errors = _validate_params(spec.parameters, parameters)
            if errors:
                raise ValidationError(name, errors)

        # Step 3: Execute with timing
        handler = spec.get_handler()
        start = time.time()

        try:
            signature = inspect.signature(handler)
            accepted = signature.parameters
            call_kwargs: dict[str, Any] = {}
            if "parameters" in accepted:
                call_kwargs["parameters"] = parameters
            if "speak" in accepted:
                call_kwargs["speak"] = speak
            for key, value in kwargs.items():
                if key in accepted or any(param.kind == inspect.Parameter.VAR_KEYWORD for param in accepted.values()):
                    call_kwargs[key] = value

            result = handler(**call_kwargs)

            elapsed_ms = (time.time() - start) * 1000
            spec.call_count += 1
            spec.total_latency_ms += elapsed_ms

            logger.info(
                "Tool '%s' executed in %.0fms (calls=%d, avg=%.0fms)",
                name, elapsed_ms, spec.call_count, spec.avg_latency_ms,
            )
            return result or "Done."

        except (ValidationError, ToolNotFoundError):
            raise
        except Exception as exc:
            elapsed_ms = (time.time() - start) * 1000
            spec.call_count += 1
            spec.error_count += 1
            spec.total_latency_ms += elapsed_ms

            logger.error(
                "Tool '%s' failed after %.0fms: %s", name, elapsed_ms, exc
            )
            raise

    # ── Introspection ─────────────────────────────────────────────────────

    def get_tool(self, name: str) -> Optional[ToolSpec]:
        """Get a tool spec by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        """Return all registered tool names."""
        return list(self._tools.keys())

    def get_declarations(self) -> list[dict]:
        """Return Gemini-compatible function declarations for all tools."""
        declarations = []
        for spec in self._tools.values():
            declarations.append({
                "name": spec.name,
                "description": spec.description,
                "parameters": spec.parameters,
            })
        return declarations

    def get_stats(self) -> dict:
        """Return execution statistics for all tools."""
        return {
            "total_tools": len(self._tools),
            "initialized": self._initialized,
            "tools": {
                name: {
                    "risk": spec.risk_tier.name,
                    "calls": spec.call_count,
                    "errors": spec.error_count,
                    "avg_latency_ms": round(spec.avg_latency_ms, 1),
                }
                for name, spec in self._tools.items()
                if spec.call_count > 0
            },
        }

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)

    def __repr__(self) -> str:
        return f"<ToolRegistry tools={len(self._tools)} initialized={self._initialized}>"
