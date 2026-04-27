"""
actions/mcp_controller.py — MCP Server Controller Action
==========================================================
Gives the LLM brain the ability to start, stop, and query
external MCP servers ON DEMAND. BUDDY remains master.

Intent examples the LLM should map to this tool:
    "start openclaw"        → start_server("openclaw")
    "stop openclaw"         → stop_server("openclaw")
    "restart openclaw"      → restart_server("openclaw")
    "show mcp status"       → status()
    "list mcp servers"      → list_catalog()
    "what servers are up?"   → list_running()
"""

import json
from typing import Any, Callable, Optional

from actions.base import Action, ActionRegistry


def mcp_controller_action(parameters: dict, **kwargs) -> str:
    """
    Routes MCP lifecycle commands to the MCPManager singleton
    held on the KernelOS instance.
    """
    from agent.kernel import kernel

    # Validate MCPManager is available
    mcp = getattr(kernel, "mcp", None)
    if mcp is None:
        return (
            "MCP Manager is not initialized. "
            "The kernel has not been fully booted."
        )

    action = (parameters.get("action") or "").strip().lower()
    server = (parameters.get("server_name") or "").strip().lower()

    # ── Route to the correct MCPManager method ────────────────────────────

    if action == "start":
        if not server:
            return "Missing 'server_name'. Which server should I start?"
        return mcp.start_server(server)

    elif action == "stop":
        if not server:
            return "Missing 'server_name'. Which server should I stop?"
        return mcp.stop_server(server)

    elif action == "restart":
        if not server:
            return "Missing 'server_name'. Which server should I restart?"
        return mcp.restart_server(server)

    elif action == "status":
        status = mcp.get_status()
        return json.dumps(status, indent=2)

    elif action == "list_catalog":
        catalog = mcp.list_catalog()
        if not catalog:
            return "No MCP servers are configured in the catalog."
        return (
            "Available MCP servers in catalog:\n"
            + "\n".join(f"  • {name}" for name in catalog)
        )

    elif action == "list_running":
        running = mcp.list_running()
        if not running:
            return "No MCP servers are currently running."
        # Build a rich status for each running server
        lines = ["Currently running MCP servers:"]
        for name in running:
            info = mcp.get_server_info(name)
            if info:
                lines.append(
                    f"  • {name} — {info['tool_count']} tools, "
                    f"uptime {info['uptime_seconds']}s, "
                    f"connected={info['connected']}"
                )
            else:
                lines.append(f"  • {name}")
        return "\n".join(lines)

    elif action == "server_info":
        if not server:
            return "Missing 'server_name'. Which server do you want info on?"
        info = mcp.get_server_info(server)
        if not info:
            return f"MCP server '{server}' is not running."
        return json.dumps(info, indent=2)

    else:
        return (
            f"Unknown MCP action '{action}'. "
            "Valid actions: start, stop, restart, status, "
            "list_catalog, list_running, server_info."
        )


class MCPControllerAction(Action):
    """
    The LLM-facing tool for on-demand MCP server management.

    BUDDY uses this to spawn OpenClaw, GitHub, Filesystem or any
    other MCP server as a subordinate — then immediately gains
    access to all of that server's tools.
    """

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
    ) -> str:
        return mcp_controller_action(parameters, **kwargs)


ActionRegistry.register(MCPControllerAction)
