"""
core/tools/mcp_manager.py — On-Demand MCP Server Lifecycle Manager
====================================================================
BUDDY controls external MCP servers as subordinate tools.
Servers are launched ONLY when the user explicitly requests them.

Architecture:
    MCPManager      — Spawns, connects, and tears down MCP servers on demand
    MCPServerEntry  — Runtime state for a single managed MCP server

Design Principles:
    1. On-demand only — nothing starts at boot unless explicitly commanded.
    2. BUDDY is master — every MCP server is a subprocess BUDDY owns.
    3. Tool injection — discovered MCP tools are injected into ToolRegistry.
    4. Clean teardown — servers are terminated on disconnect or shutdown.
"""
from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from buddy_logging import get_logger
from core.tools.mcp_client import MCPClient, MCPServerConfig, MCPTransport
from core.tools.registry import ToolRegistry, ToolSpec, RiskTier

logger = get_logger("core.tools.mcp_manager")


# ── Default Server Catalog ────────────────────────────────────────────────────

# Pre-configured server definitions the user can launch by name.
# Only started when a user says "start <server-name>".
DEFAULT_CATALOG: dict[str, MCPServerConfig] = {
    "openclaw": MCPServerConfig(
        name="openclaw",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "open-claw@latest"],
    ),
    "filesystem": MCPServerConfig(
        name="filesystem",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "."],
    ),
    "github": MCPServerConfig(
        name="github",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@modelcontextprotocol/server-github"],
    ),
    "sqlite": MCPServerConfig(
        name="sqlite",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@modelcontextprotocol/server-sqlite"],
    ),
}


@dataclass
class MCPServerEntry:
    """Runtime bookkeeping for a live MCP server."""
    config: MCPServerConfig
    client: MCPClient
    started_at: float = field(default_factory=time.time)
    tool_count: int = 0


class MCPManager:
    """
    On-demand MCP server lifecycle manager.

    Usage:
        manager = MCPManager(tool_registry)
        manager.start_server("openclaw")          # Spawns OpenClaw as subprocess
        manager.send_to_server("openclaw", ...)   # Delegates work
        manager.stop_server("openclaw")           # Terminates
    """

    def __init__(self, tool_registry: ToolRegistry):
        self._registry = tool_registry
        self._servers: dict[str, MCPServerEntry] = {}
        self._catalog: dict[str, MCPServerConfig] = dict(DEFAULT_CATALOG)
        self._lock = threading.Lock()

    # ── Catalog Management ────────────────────────────────────────────────

    def add_to_catalog(self, config: MCPServerConfig) -> None:
        """Add or update a server definition in the catalog."""
        self._catalog[config.name] = config
        logger.info("Added '%s' to MCP server catalog.", config.name)

    def list_catalog(self) -> list[str]:
        """Return names of all known server definitions."""
        return list(self._catalog.keys())

    # ── Server Lifecycle ──────────────────────────────────────────────────

    def start_server(self, name: str, **override_env) -> str:
        """
        Start an MCP server by catalog name.
        Returns a status string suitable for LLM consumption.
        """
        with self._lock:
            if name in self._servers:
                entry = self._servers[name]
                if entry.client.is_connected:
                    return (
                        f"MCP server '{name}' is already running with "
                        f"{entry.tool_count} tools available."
                    )

        config = self._catalog.get(name)
        if not config:
            available = ", ".join(self._catalog.keys())
            return (
                f"Unknown MCP server '{name}'. "
                f"Available servers: {available}"
            )

        # Merge any env overrides
        if override_env:
            config = MCPServerConfig(
                name=config.name,
                transport=config.transport,
                command=config.command,
                args=list(config.args),
                url=config.url,
                env={**config.env, **override_env},
                auto_approve=list(config.auto_approve),
            )

        client = MCPClient(config)
        logger.info("Starting MCP server '%s' ...", name)

        if not client.connect():
            return f"Failed to start MCP server '{name}'. Check logs for details."

        # Discover and inject tools into BUDDY's ToolRegistry
        discovered = client.list_tools()
        injected = 0
        for decl in discovered:
            prefixed_name = f"mcp_{name}_{decl.name}"
            spec = ToolSpec(
                name=prefixed_name,
                description=f"[MCP:{name}] {decl.description}",
                parameters=decl.input_schema,
                handler=self._make_handler(name, decl.name),
                risk_tier=RiskTier.MODERATE,
                timeout=60,
            )
            self._registry.register(spec)
            injected += 1

        with self._lock:
            self._servers[name] = MCPServerEntry(
                config=config,
                client=client,
                tool_count=injected,
            )

        logger.info(
            "MCP server '%s' started — %d tools injected into ToolRegistry.",
            name, injected,
        )
        return (
            f"MCP server '{name}' is now running. "
            f"{injected} tools have been registered and are available for use. "
            f"Tools are prefixed with 'mcp_{name}_'."
        )

    def stop_server(self, name: str) -> str:
        """Stop a running MCP server and remove its tools."""
        with self._lock:
            entry = self._servers.pop(name, None)

        if not entry:
            return f"MCP server '{name}' is not running."

        # Disconnect
        entry.client.disconnect()

        # Remove injected tools from registry
        prefix = f"mcp_{name}_"
        tools_to_remove = [
            t for t in self._registry.list_tools() if t.startswith(prefix)
        ]
        for tool_name in tools_to_remove:
            self._registry._tools.pop(tool_name, None)

        logger.info(
            "MCP server '%s' stopped — %d tools removed.",
            name, len(tools_to_remove),
        )
        return (
            f"MCP server '{name}' has been stopped. "
            f"{len(tools_to_remove)} tools removed from registry."
        )

    def send_to_server(self, name: str, tool_name: str, arguments: dict) -> str:
        """Delegate a tool call directly to an MCP server."""
        with self._lock:
            entry = self._servers.get(name)

        if not entry:
            return f"MCP server '{name}' is not running. Start it first."

        if not entry.client.is_connected:
            return f"MCP server '{name}' is disconnected."

        return entry.client.call_tool(tool_name, arguments)

    def restart_server(self, name: str) -> str:
        """Restart an MCP server (stop then start)."""
        self.stop_server(name)
        return self.start_server(name)

    # ── Introspection ─────────────────────────────────────────────────────

    def list_running(self) -> list[str]:
        """Return names of currently running MCP servers."""
        with self._lock:
            return list(self._servers.keys())

    def get_server_info(self, name: str) -> Optional[dict]:
        """Get runtime info for a specific server."""
        with self._lock:
            entry = self._servers.get(name)
        if not entry:
            return None
        return {
            "name": name,
            "connected": entry.client.is_connected,
            "tool_count": entry.tool_count,
            "uptime_seconds": round(time.time() - entry.started_at, 1),
        }

    def get_status(self) -> dict:
        """Full status report."""
        with self._lock:
            running = {}
            for name, entry in self._servers.items():
                running[name] = {
                    "connected": entry.client.is_connected,
                    "tools": entry.tool_count,
                    "uptime_s": round(time.time() - entry.started_at, 1),
                }
        return {
            "catalog_servers": list(self._catalog.keys()),
            "running_servers": running,
        }

    # ── Shutdown ──────────────────────────────────────────────────────────

    def shutdown_all(self) -> None:
        """Stop all running MCP servers. Called during BUDDY shutdown."""
        with self._lock:
            names = list(self._servers.keys())
        for name in names:
            self.stop_server(name)
        logger.info("All MCP servers shut down.")

    # ── Internal ──────────────────────────────────────────────────────────

    def _make_handler(self, server_name: str, tool_name: str) -> Callable:
        """Create a closure that routes tool calls to the correct MCP server."""
        def handler(parameters: dict = None, **kwargs) -> str:
            return self.send_to_server(server_name, tool_name, parameters or {})
        return handler
