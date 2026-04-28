"""Full system boot test — validates the entire BUDDY architecture."""
import sys
import asyncio

print("=" * 60)
print("BUDDY Full System Boot Test")
print("=" * 60)

errors = []
warnings = []

# 1. Kernel boot
try:
    from agent.kernel import kernel
    loop = asyncio.new_event_loop()
    loop.run_until_complete(kernel.initialize())
    assert kernel._initialized, "Kernel not initialized"
    print(f"[PASS] KernelOS v{kernel.VERSION} booted successfully")
except Exception as e:
    errors.append(f"Kernel boot: {e}")
    print(f"[FAIL] Kernel boot: {e}")

# 2. Tool registry population
try:
    stats = kernel.tools.get_stats()
    total = stats.get("total_tools", 0)
    assert total > 0, f"Expected tools > 0, got {total}"
    print(f"[PASS] ToolRegistry: {total} tools loaded")
except Exception as e:
    errors.append(f"ToolRegistry: {e}")
    print(f"[FAIL] ToolRegistry: {e}")

# 3. Subagent registry
try:
    agent_stats = kernel.agents.get_stats()
    count = agent_stats.get("total_agents", 0)
    assert count >= 6, f"Expected >= 6 agents, got {count}"
    print(f"[PASS] SubagentRegistry: {count} agents registered")
except Exception as e:
    errors.append(f"SubagentRegistry: {e}")
    print(f"[FAIL] SubagentRegistry: {e}")

# 4. MCP Manager ready (no servers running)
try:
    mcp_status = kernel.mcp.get_status()
    catalog = mcp_status["catalog_servers"]
    running = mcp_status["running_servers"]
    assert len(catalog) >= 4, f"Expected >= 4 catalog entries, got {len(catalog)}"
    assert len(running) == 0, f"Expected 0 running, got {len(running)}"
    print(f"[PASS] MCPManager: {len(catalog)} in catalog, 0 running (on-demand)")
except Exception as e:
    errors.append(f"MCPManager: {e}")
    print(f"[FAIL] MCPManager: {e}")

# 5. Context manager
try:
    ctx_stats = kernel.context.get_stats()
    assert ctx_stats["max_chars"] == 12000
    print(f"[PASS] ContextManager: budget={ctx_stats['max_chars']}, slots={ctx_stats['slot_count']}")
except Exception as e:
    errors.append(f"ContextManager: {e}")
    print(f"[FAIL] ContextManager: {e}")

# 6. mcp_controller action is callable
try:
    from actions.base import ActionRegistry
    result = ActionRegistry.execute("mcp_controller", {"action": "status"})
    import json
    status = json.loads(result)
    assert "catalog_servers" in status
    print(f"[PASS] mcp_controller action executes correctly")
except Exception as e:
    errors.append(f"mcp_controller action: {e}")
    print(f"[FAIL] mcp_controller action: {e}")

# 7. Full status report
try:
    full = kernel.get_full_status()
    required_keys = {"kernel", "context", "tools", "agents", "mcp"}
    missing = required_keys - set(full.keys())
    assert not missing, f"Missing keys: {missing}"
    print(f"[PASS] get_full_status() contains all subsystem reports")
except Exception as e:
    errors.append(f"Full status: {e}")
    print(f"[FAIL] Full status: {e}")

# 8. Agent routing works
try:
    match = kernel.agents.route_by_text("start openclaw server")
    assert match is not None, "No agent match for 'start openclaw server'"
    assert match.name == "system_agent", f"Expected system_agent, got {match.name}"
    print(f"[PASS] Agent routing: 'start openclaw' -> {match.name} (score={match.score:.2f})")
except Exception as e:
    errors.append(f"Agent routing: {e}")
    print(f"[FAIL] Agent routing: {e}")

# 9. VoiceOrchestrator imports cleanly
try:
    from agent.voice import VoiceOrchestrator
    vo = VoiceOrchestrator()
    assert hasattr(vo, "handle_user_command")
    print(f"[PASS] VoiceOrchestrator imports and initializes")
except Exception as e:
    errors.append(f"VoiceOrchestrator: {e}")
    print(f"[FAIL] VoiceOrchestrator: {e}")

# 10. Graceful shutdown
try:
    loop.run_until_complete(kernel.shutdown())
    assert not kernel._initialized
    print(f"[PASS] KernelOS graceful shutdown complete")
except Exception as e:
    errors.append(f"Shutdown: {e}")
    print(f"[FAIL] Shutdown: {e}")

print()
print("=" * 60)
if errors:
    print(f"RESULT: {len(errors)} FAILURES, {len(warnings)} WARNINGS")
    for err in errors:
        print(f"  X {err}")
    sys.exit(1)
else:
    print(f"RESULT: ALL 10 CHECKS PASSED")
    print("BUDDY architecture is fully operational.")
    sys.exit(0)
