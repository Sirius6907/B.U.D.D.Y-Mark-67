from __future__ import annotations

import os

from actions.base import Action, ActionRegistry
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result


class SystemGetEnvAction(Action):
    @property
    def name(self) -> str:
        return "system_get_env"

    @property
    def description(self) -> str:
        return "Get environment variables."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "variable": {"type": "STRING"}
            },
            "required": [],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        var_name = parameters.get("variable")
        
        if var_name:
            val = os.environ.get(var_name)
            return build_tool_result(
                tool_name=self.name,
                operation="get_env",
                risk_level=RiskLevel.LOW,
                status="success" if val is not None else "failed",
                summary=f"Environment variable {var_name}: {'Found' if val is not None else 'Not set'}",
                structured_data={var_name: val},
                idempotent=True,
                preconditions=[],
                postconditions=["env var retrieved"],
            )
        else:
            # Return all non-sensitive looking env vars
            safe_env = {}
            for k, v in os.environ.items():
                k_lower = k.lower()
                if any(x in k_lower for x in ["key", "secret", "token", "pass", "auth", "cred"]):
                    safe_env[k] = "[REDACTED]"
                else:
                    safe_env[k] = v
                    
            return build_tool_result(
                tool_name=self.name,
                operation="get_env",
                risk_level=RiskLevel.LOW,
                status="success",
                summary=f"Retrieved {len(safe_env)} environment variables",
                structured_data=safe_env,
                idempotent=True,
                preconditions=[],
                postconditions=["all env vars retrieved"],
            )


ActionRegistry.register(SystemGetEnvAction)
