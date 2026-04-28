from __future__ import annotations

import hashlib
import json
import platform
import re
from typing import Any

from agent.models import SubproblemKey


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


class StateEncoder:
    def __init__(self, schema_version: str = "dp-v2"):
        self.schema_version = schema_version

    def normalize_goal(self, goal: str) -> str:
        return re.sub(r"\s+", " ", (goal or "").strip().lower())

    def infer_intent_family(self, context: dict[str, Any] | None) -> str:
        context = context or {}
        return str(context.get("intent_family") or context.get("route") or "generic")

    def infer_tool_surface(self, context: dict[str, Any] | None) -> str:
        context = context or {}
        return str(
            context.get("tool_surface")
            or context.get("surface")
            or context.get("app_surface")
            or "generic"
        )

    def environment_signature(self, context: dict[str, Any] | None) -> str:
        context = context or {}
        data = {
            "platform": context.get("platform") or platform.system().lower(),
            "intent_family": self.infer_intent_family(context),
            "tool_surface": self.infer_tool_surface(context),
            "window_family": context.get("window_family", ""),
            "url_family": context.get("url_family", ""),
            "schema_version": self.schema_version,
        }
        return _stable_json(data)

    def state_hash(self, context: dict[str, Any] | None) -> str:
        context = context or {}
        state = context.get("state_snapshot") or context.get("state") or {}
        if not state:
            state = {
                "preconditions": context.get("preconditions") or {},
                "selectors": context.get("semantic_selectors") or [],
            }
        return hashlib.sha1(_stable_json(state).encode("utf-8")).hexdigest()

    def build_key(self, goal: str, context: dict[str, Any] | None = None) -> SubproblemKey:
        context = context or {}
        return SubproblemKey(
            normalized_goal=self.normalize_goal(goal),
            intent_family=self.infer_intent_family(context),
            environment_signature=self.environment_signature(context),
            state_hash=self.state_hash(context),
            tool_surface=self.infer_tool_surface(context),
            schema_version=self.schema_version,
        )
