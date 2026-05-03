"""Auto-generated browser_tab tools — DO NOT EDIT MANUALLY."""
from actions.base import Action, ActionRegistry
from typing import Any


class BrowserTabPinTab(Action):
    @property
    def name(self) -> str: return "browser_tab_pin_tab"
    @property
    def description(self) -> str: return "Pin the current tab."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().pin_tab(browser=parameters.get("browser"), player=player)


class BrowserTabUnpinTab(Action):
    @property
    def name(self) -> str: return "browser_tab_unpin_tab"
    @property
    def description(self) -> str: return "Unpin the current tab."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().unpin_tab(browser=parameters.get("browser"), player=player)


class BrowserTabMuteTab(Action):
    @property
    def name(self) -> str: return "browser_tab_mute_tab"
    @property
    def description(self) -> str: return "Mute audio on current tab."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().mute_tab(browser=parameters.get("browser"), player=player)


class BrowserTabUnmuteTab(Action):
    @property
    def name(self) -> str: return "browser_tab_unmute_tab"
    @property
    def description(self) -> str: return "Unmute audio on current tab."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().unmute_tab(browser=parameters.get("browser"), player=player)


class BrowserTabGetActiveTab(Action):
    @property
    def name(self) -> str: return "browser_tab_get_active_tab"
    @property
    def description(self) -> str: return "Get info about the active tab."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().get_active(browser=parameters.get("browser"), player=player)


class BrowserTabCloseOtherTabs(Action):
    @property
    def name(self) -> str: return "browser_tab_close_other_tabs"
    @property
    def description(self) -> str: return "Close all tabs except the current one."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().close_others(browser=parameters.get("browser"), player=player)


class BrowserTabCloseTabsRight(Action):
    @property
    def name(self) -> str: return "browser_tab_close_tabs_right"
    @property
    def description(self) -> str: return "Close all tabs to the right."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().close_right(browser=parameters.get("browser"), player=player)


class BrowserTabReopenClosedTab(Action):
    @property
    def name(self) -> str: return "browser_tab_reopen_closed_tab"
    @property
    def description(self) -> str: return "Reopen the last closed tab."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().reopen_closed(browser=parameters.get("browser"), player=player)


class BrowserTabMoveTab(Action):
    @property
    def name(self) -> str: return "browser_tab_move_tab"
    @property
    def description(self) -> str: return "Move tab to a new position."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"from_index": {"type": "INTEGER"}, "to_index": {"type": "INTEGER"}}, "required": ["from_index", "to_index"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().move_tab(parameters["from_index"], parameters["to_index"], browser=parameters.get("browser"), player=player)


class BrowserTabCountTabs(Action):
    @property
    def name(self) -> str: return "browser_tab_count_tabs"
    @property
    def description(self) -> str: return "Count open tabs."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().count_tabs(browser=parameters.get("browser"), player=player)


for _cls in [BrowserTabPinTab, BrowserTabUnpinTab, BrowserTabMuteTab, BrowserTabUnmuteTab, BrowserTabGetActiveTab, BrowserTabCloseOtherTabs, BrowserTabCloseTabsRight, BrowserTabReopenClosedTab, BrowserTabMoveTab, BrowserTabCountTabs]:
    ActionRegistry.register(_cls)
