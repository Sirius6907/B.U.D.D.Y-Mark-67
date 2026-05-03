from __future__ import annotations

import json
from typing import Any, Callable, Optional

from actions.base import Action, ActionRegistry
from agent.kernel import kernel
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result

class MCPControllerAction(Action):
    @property
    def name(self) -> str:
        return "mcp_controller"

    @property
    def description(self) -> str:
        return (
            "Start, stop, restart, or query external MCP tool servers on demand. "
            "Use this when the user asks to launch OpenClaw, connect to GitHub, "
            "or manage any external MCP server. BUDDY remains the master controller."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING",
                    "description": (
                        "The lifecycle action to perform. "
                        "One of: start, stop, restart, status, "
                        "list_catalog, list_running, server_info."
                    ),
                    "enum": [
                        "start", "stop", "restart",
                        "status", "list_catalog",
                        "list_running", "server_info",
                    ],
                },
                "server_name": {
                    "type": "STRING",
                    "description": (
                        "The name of the MCP server to act on. "
                        "Examples: 'openclaw', 'github', 'filesystem', 'sqlite'. "
                        "Required for start/stop/restart/server_info."
                    ),
                },
            },
            "required": ["action"],
        }

    def execute(
        self,
        parameters: dict,
        player: Optional[Any] = None,
        speak: Optional[Callable] = None,
        **kwargs,
    ):
        mcp = getattr(kernel, "mcp", None)
        if mcp is None:
            return build_tool_result(
                tool_name=self.name,
                operation="mcp_control",
                risk_level=RiskLevel.LOW,
                status="failed",
                summary="MCP Manager is not initialized. The kernel has not been fully booted.",
                structured_data={"error": "mcp_not_initialized"},
                idempotent=True,
                preconditions=[],
                postconditions=[],
            )

        action = (parameters.get("action") or "").strip().lower()
        server = (parameters.get("server_name") or "").strip().lower()
        
        result_msg = ""
        structured_info = {}

        if action == "start":
            if not server:
                result_msg = "Missing 'server_name'. Which server should I start?"
            else:
                result_msg = str(mcp.start_server(server))
        elif action == "stop":
            if not server:
                result_msg = "Missing 'server_name'. Which server should I stop?"
            else:
                result_msg = str(mcp.stop_server(server))
        elif action == "restart":
            if not server:
                result_msg = "Missing 'server_name'. Which server should I restart?"
            else:
                result_msg = str(mcp.restart_server(server))
        elif action == "status":
            status = mcp.get_status()
            structured_info = status
            result_msg = json.dumps(status, indent=2)
        elif action == "list_catalog":
            catalog = mcp.list_catalog()
            structured_info = {"catalog": catalog}
            if not catalog:
                result_msg = "No MCP servers are configured in the catalog."
            else:
                result_msg = "Available MCP servers in catalog:\n" + "\n".join(f"  • {name}" for name in catalog)
        elif action == "list_running":
            running = mcp.list_running()
            if not running:
                result_msg = "No MCP servers are currently running."
            else:
                lines = ["Currently running MCP servers:"]
                server_infos = []
                for name in running:
                    info = mcp.get_server_info(name)
                    if info:
                        server_infos.append({"name": name, "info": info})
                        lines.append(f"  • {name} — {info['tool_count']} tools, uptime {info['uptime_seconds']}s, connected={info['connected']}")
                    else:
                        server_infos.append({"name": name, "info": None})
                        lines.append(f"  • {name}")
                structured_info = {"running_servers": server_infos}
                result_msg = "\n".join(lines)
        elif action == "server_info":
            if not server:
                result_msg = "Missing 'server_name'. Which server do you want info on?"
            else:
                info = mcp.get_server_info(server)
                if not info:
                    result_msg = f"MCP server '{server}' is not running."
                else:
                    structured_info = info
                    result_msg = json.dumps(info, indent=2)
        else:
            result_msg = f"Unknown MCP action '{action}'. Valid actions: start, stop, restart, status, list_catalog, list_running, server_info."

        is_mutating = action in ("start", "stop", "restart")
        risk = RiskLevel.MEDIUM if is_mutating else RiskLevel.LOW

        return build_tool_result(
            tool_name=self.name,
            operation=action,
            risk_level=risk,
            status="success" if not result_msg.startswith("Missing ") and not result_msg.startswith("Unknown ") else "failed",
            summary=result_msg,
            structured_data={"action": action, "server": server, "details": structured_info},
            idempotent=not is_mutating,
            preconditions=[],
            postconditions=[],
        )

ActionRegistry.register(MCPControllerAction)
