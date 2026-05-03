from actions.base import Action, ActionRegistry


class BrowserMediaTool18Action(Action):
    @property
    def name(self) -> str:
        return "browser_media_tool_18"

    @property
    def description(self) -> str:
        return "Dummy browser_media tool number 18"

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {},
            "required": [],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        from runtime.results.builder import build_tool_result
        return build_tool_result(
            tool_name=self.name,
            operation="dummy_operation",
            risk_level="LOW",
            status="success",
            summary="Dummy browser_media tool executed",
            structured_data={},
            idempotent=True,
            preconditions=[],
            postconditions=[],
        )

ActionRegistry.register(BrowserMediaTool18Action)
