import time

import pytest

from core.tools.registry import RiskTier, ToolRegistry, ToolSpec, _validate_params
from registries.capability_registry import CapabilityRegistry, CapabilitySpec


def test_capability_registry_indexes_aliases_and_domains():
    registry = CapabilityRegistry()
    registry.register(
        CapabilitySpec(
            tool_name="process_list",
            domain="process",
            operation="list",
            aliases=["show running tasks", "list processes"],
            risk_level="LOW",
            idempotent=True,
            preconditions=[],
            postconditions=["process snapshot returned"],
        )
    )
    assert registry.find_by_alias("list processes")[0].tool_name == "process_list"
    assert registry.list_domain("process")[0].tool_name == "process_list"


def test_capability_registry_reregistration_replaces_stale_aliases_and_domains():
    registry = CapabilityRegistry()
    registry.register(
        CapabilitySpec(
            tool_name="process_list",
            domain="process",
            operation="list",
            aliases=["list processes"],
            risk_level="LOW",
            idempotent=True,
            preconditions=[],
            postconditions=["process snapshot returned"],
        )
    )

    registry.register(
        CapabilitySpec(
            tool_name="process_list",
            domain="system",
            operation="inspect",
            aliases=["inspect system tasks"],
            risk_level="LOW",
            idempotent=True,
            preconditions=[],
            postconditions=["system task snapshot returned"],
        )
    )

    assert registry.find_by_alias("list processes") == []
    assert registry.find_by_alias("inspect system tasks")[0].tool_name == "process_list"
    assert registry.list_domain("process") == []
    assert registry.list_domain("system")[0].tool_name == "process_list"


def test_capability_spec_normalizes_sequence_fields_to_tuples():
    spec = CapabilitySpec(
        tool_name="process_list",
        aliases=["show running tasks", "list processes"],
        preconditions=["process access available"],
        postconditions=["process snapshot returned"],
    )

    assert spec.aliases == ("show running tasks", "list processes")
    assert isinstance(spec.aliases, tuple)
    assert spec.preconditions == ("process access available",)
    assert isinstance(spec.preconditions, tuple)
    assert spec.postconditions == ("process snapshot returned",)
    assert isinstance(spec.postconditions, tuple)


def test_capability_spec_rejects_scalar_string_sequence_fields():
    with pytest.raises(TypeError):
        CapabilitySpec(tool_name="process_list", aliases="list processes")

    with pytest.raises(TypeError):
        CapabilitySpec(tool_name="process_list", preconditions="process access available")

    with pytest.raises(TypeError):
        CapabilitySpec(tool_name="process_list", postconditions="process snapshot returned")


def test_capability_spec_rejects_non_string_sequence_elements():
    with pytest.raises(TypeError):
        CapabilitySpec(tool_name="process_list", aliases=[1])

    with pytest.raises(TypeError):
        CapabilitySpec(tool_name="process_list", preconditions=[None])

    with pytest.raises(TypeError):
        CapabilitySpec(tool_name="process_list", postconditions=["ok", 7])


def test_validate_params_rejects_booleans_for_integer_and_number_types():
    schema = {
        "type": "object",
        "properties": {
            "count": {"type": "integer"},
            "ratio": {"type": "number"},
        },
    }

    errors = _validate_params(schema, {"count": True, "ratio": False})

    assert "Parameter 'count' expected type 'integer', got 'bool'" in errors
    assert "Parameter 'ratio' expected type 'number', got 'bool'" in errors


def test_tool_registry_enforces_spec_timeout():
    registry = ToolRegistry()

    def slow_handler(parameters: dict) -> str:
        time.sleep(0.2)
        return "done"

    registry.register(
        ToolSpec(
            name="slow_tool",
            description="Slow tool for timeout enforcement test",
            parameters={"type": "object", "properties": {}},
            handler=slow_handler,
            risk_tier=RiskTier.LOW,
            timeout=0.01,
        )
    )

    with pytest.raises(TimeoutError):
        registry.execute("slow_tool", {})
