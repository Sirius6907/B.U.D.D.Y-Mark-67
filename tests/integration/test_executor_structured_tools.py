from core.tools.registry import RiskTier, ToolRegistry, ToolSpec
from registries.capability_registry import CapabilityRegistry, CapabilitySpec


def test_vertical_slice_tools_register_in_new_domains():
    from actions import ActionRegistry

    assert ActionRegistry.get_action("file_read_metadata") is not None
    assert ActionRegistry.get_action("process_list") is not None
    assert ActionRegistry.get_action("network_list_adapters") is not None


def test_call_tool_prefers_structured_registry(monkeypatch):
    from agent import executor
    from agent.kernel import kernel

    captured: dict[str, object] = {}

    def structured_handler(*, parameters: dict, speak=None) -> str:
        captured["parameters"] = parameters
        return "structured-ok"

    original_tools = kernel.tools
    original_capabilities = kernel.capabilities

    test_tools = ToolRegistry()
    test_tools.register(
        ToolSpec(
            name="structured_tool",
            description="Structured test tool",
            parameters={"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
            handler=structured_handler,
            risk_tier=RiskTier.LOW,
            domain="files",
            operation="read",
        )
    )

    test_capabilities = CapabilityRegistry()
    test_capabilities.register(
        CapabilitySpec(
            tool_name="structured_tool",
            domain="files",
            operation="read",
        )
    )

    monkeypatch.setattr(kernel, "tools", test_tools)
    monkeypatch.setattr(kernel, "capabilities", test_capabilities)

    try:
        result = executor.call_tool("structured_tool", {"name": "buddy"})
    finally:
        monkeypatch.setattr(kernel, "tools", original_tools)
        monkeypatch.setattr(kernel, "capabilities", original_capabilities)

    assert result == "structured-ok"
    assert captured["parameters"] == {"name": "buddy"}
