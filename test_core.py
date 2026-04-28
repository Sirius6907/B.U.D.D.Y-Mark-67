"""Quick integration test for the new core architecture."""
import sys
sys.path.insert(0, ".")

from agent.kernel import kernel
from core.agent.subagent_registry import AgentCapability
from core.memory.context_manager import SlotPriority

print(f"KernelOS v{kernel.VERSION}")
print(f"Context:  {kernel.context}")
print(f"Tools:    {kernel.tools}")
print(f"Agents:   {kernel.agents}")
print()

# Test agents
print("Registered agents:", kernel.agents.list_agents())
print()

# Test routing
result = kernel.agents.route({AgentCapability.CODE})
print(f"Route CODE -> {result.agent.name} (confidence={result.confidence:.2f})")

result2 = kernel.agents.route({AgentCapability.SYSTEM_CONTROL})
print(f"Route SYSTEM -> {result2.agent.name} (confidence={result2.confidence:.2f})")

result3 = kernel.agents.route({AgentCapability.WEB_SEARCH})
print(f"Route WEB -> {result3.agent.name} (confidence={result3.confidence:.2f})")

result4 = kernel.agents.route({AgentCapability.SCREEN})
print(f"Route SCREEN -> {result4.agent.name} (confidence={result4.confidence:.2f})")

# Test context packing
kernel.context.upsert("test_slot", "Hello world context", SlotPriority.SUPPLEMENTARY)
window = kernel.context.assemble()
print(f"\nContext window: {window.total_chars} chars, {window.slot_count} slots")
print(f"Slots included: {window.slots_included}")

stats = kernel.context.get_stats()
pct = stats["utilization"] * 100
print(f"Budget utilization: {pct:.1f}%")

# Test full status
status = kernel.get_full_status()
print(f"\nFull status: kernel={status['kernel']['status']}, "
      f"agents={status['agents']['total_agents']}, "
      f"tools={status['tools']['total_tools']}")

print("\n=== ALL TESTS PASSED ===")
