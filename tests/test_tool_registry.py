from core.tools.registry import ToolRegistry, ToolSpec


def test_tool_registry_execute_filters_optional_kwargs_for_plain_handlers():
    registry = ToolRegistry()
    captured: list[dict] = []

    def handler(parameters):
        captured.append(parameters)
        return "ok"

    registry.register(
        ToolSpec(
            name="plain_tool",
            description="Plain handler",
            parameters={"type": "object", "properties": {}},
            handler=handler,
        )
    )

    result = registry.execute("plain_tool", {"query": "hello"}, speak=lambda text: None, player="ui")

    assert result == "ok"
    assert captured == [{"query": "hello"}]
