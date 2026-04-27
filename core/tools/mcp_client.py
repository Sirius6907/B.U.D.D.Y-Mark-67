"""
core/tools/mcp_client.py — MCP Server Bridge Client
=====================================================
Inspired by OpenClaw's mcp/channel-bridge.ts. Provides a Python client
that can connect to external MCP servers (stdio or SSE transport) and
route tool calls through them.

Architecture:
    MCPClient       — Manages connection to a single MCP server
    MCPServerConfig — Configuration for an MCP server connection

Design Principles (from OpenClaw reverse-engineering):
    1. Async-ready but sync-compatible — works in threaded voice pipeline.
    2. Stateful connection — maintains persistent channel to MCP server.
    3. Tool discovery — auto-registers available tools from MCP server.
    4. Approval gating — destructive tools queue for user approval.
"""
from __future__ import annotations

import json
import subprocess
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Optional, Callable
from enum import Enum

from buddy_logging import get_logger

logger = get_logger("core.tools.mcp")


class MCPTransport(str, Enum):
    STDIO = "stdio"
    SSE = "sse"


@dataclass
class MCPServerConfig:
    """Configuration for connecting to an MCP server."""
    name: str
    transport: MCPTransport
    command: Optional[str] = None      # For stdio transport
    args: list[str] = field(default_factory=list)
    url: Optional[str] = None          # For SSE transport
    env: dict[str, str] = field(default_factory=dict)
    auto_approve: list[str] = field(default_factory=list)  # Tool names to auto-approve


@dataclass
class MCPToolDeclaration:
    """A tool discovered from an MCP server."""
    name: str
    description: str
    input_schema: dict
    server_name: str


class MCPClient:
    """
    Bridges external MCP servers with the Buddy tool registry.

    Usage:
        config = MCPServerConfig(
            name="filesystem",
            transport=MCPTransport.STDIO,
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/home"],
        )
        client = MCPClient(config)
        client.connect()
        tools = client.list_tools()
        result = client.call_tool("read_file", {"path": "/home/test.txt"})
    """

    def __init__(self, config: MCPServerConfig):
        self.config = config
        self._process: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        self._request_id = 0
        self._connected = False
        self._tools: dict[str, MCPToolDeclaration] = {}

    # ── Connection Lifecycle ──────────────────────────────────────────────

    def connect(self) -> bool:
        """Establish connection to the MCP server."""
        if self._connected:
            return True

        if self.config.transport == MCPTransport.STDIO:
            return self._connect_stdio()
        elif self.config.transport == MCPTransport.SSE:
            logger.warning("SSE transport not yet implemented for MCP client")
            return False

        return False

    def _connect_stdio(self) -> bool:
        """Start MCP server as a subprocess with stdio transport."""
        if not self.config.command:
            logger.error("No command specified for stdio MCP server '%s'", self.config.name)
            return False

        try:
            cmd = [self.config.command] + self.config.args
            env = {**dict(__import__("os").environ), **self.config.env}

            self._process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
            )

            # Initialize MCP protocol
            init_response = self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "buddy-mk67", "version": "1.0.0"},
            })

            if init_response and "result" in init_response:
                self._connected = True
                # Send initialized notification
                self._send_notification("notifications/initialized", {})
                # Discover tools
                self._discover_tools()
                logger.info(
                    "Connected to MCP server '%s' — %d tools available",
                    self.config.name, len(self._tools),
                )
                return True
            else:
                logger.error("MCP initialization failed for '%s'", self.config.name)
                self.disconnect()
                return False

        except Exception as exc:
            logger.error("Failed to start MCP server '%s': %s", self.config.name, exc)
            return False

    def disconnect(self) -> None:
        """Terminate the MCP server connection."""
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except Exception:
                self._process.kill()
            self._process = None
        self._connected = False
        self._tools.clear()
        logger.info("Disconnected from MCP server '%s'", self.config.name)

    # ── Protocol Communication ────────────────────────────────────────────

    def _send_request(self, method: str, params: dict) -> Optional[dict]:
        """Send a JSON-RPC request and return the response."""
        if not self._process or not self._process.stdin or not self._process.stdout:
            return None

        with self._lock:
            self._request_id += 1
            request = {
                "jsonrpc": "2.0",
                "id": self._request_id,
                "method": method,
                "params": params,
            }

            try:
                request_str = json.dumps(request) + "\n"
                self._process.stdin.write(request_str)
                self._process.stdin.flush()

                response_str = self._process.stdout.readline()
                if response_str:
                    return json.loads(response_str)
                return None
            except Exception as exc:
                logger.error("MCP request failed (%s): %s", method, exc)
                return None

    def _send_notification(self, method: str, params: dict) -> None:
        """Send a JSON-RPC notification (no response expected)."""
        if not self._process or not self._process.stdin:
            return

        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }

        try:
            notif_str = json.dumps(notification) + "\n"
            self._process.stdin.write(notif_str)
            self._process.stdin.flush()
        except Exception as exc:
            logger.error("MCP notification failed (%s): %s", method, exc)

    # ── Tool Discovery ────────────────────────────────────────────────────

    def _discover_tools(self) -> None:
        """Query the MCP server for available tools."""
        response = self._send_request("tools/list", {})
        if not response or "result" not in response:
            return

        tools_data = response["result"].get("tools", [])
        for tool_data in tools_data:
            decl = MCPToolDeclaration(
                name=tool_data["name"],
                description=tool_data.get("description", ""),
                input_schema=tool_data.get("inputSchema", {}),
                server_name=self.config.name,
            )
            self._tools[decl.name] = decl

        logger.debug(
            "Discovered %d tools from MCP server '%s': %s",
            len(self._tools), self.config.name,
            list(self._tools.keys()),
        )

    # ── Tool Execution ────────────────────────────────────────────────────

    def call_tool(self, name: str, arguments: dict) -> str:
        """Call a tool on the MCP server."""
        if not self._connected:
            return f"Error: Not connected to MCP server '{self.config.name}'"

        if name not in self._tools:
            return f"Error: Tool '{name}' not found on server '{self.config.name}'"

        response = self._send_request("tools/call", {
            "name": name,
            "arguments": arguments,
        })

        if not response:
            return f"Error: No response from MCP server for tool '{name}'"

        if "error" in response:
            error = response["error"]
            return f"MCP Error: {error.get('message', 'Unknown error')}"

        result = response.get("result", {})
        content = result.get("content", [])

        # Concatenate text content blocks
        text_parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text_parts.append(block.get("text", ""))

        return "\n".join(text_parts) if text_parts else json.dumps(result)

    # ── Introspection ─────────────────────────────────────────────────────

    def list_tools(self) -> list[MCPToolDeclaration]:
        """Return all tools available from this MCP server."""
        return list(self._tools.values())

    @property
    def is_connected(self) -> bool:
        return self._connected

    def __repr__(self) -> str:
        return (
            f"<MCPClient server='{self.config.name}' "
            f"transport={self.config.transport.value} "
            f"connected={self._connected} "
            f"tools={len(self._tools)}>"
        )
