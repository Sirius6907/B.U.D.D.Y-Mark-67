"""Real browser_tab tools — new_tab, close_tab, switch_tab, list_tabs, duplicate_tab."""
from actions.base import Action, ActionRegistry
from typing import Any
from runtime.results.builder import build_tool_result
from runtime.contracts.models import RiskLevel


class BrowserTabNewTab(Action):
    @property
    def name(self) -> str: return "browser_tab_new_tab"
    @property
    def description(self) -> str: return "Open a new browser tab, optionally navigating to a URL."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"url": {"type": "STRING", "description": "URL to open in new tab (optional)"}}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().new_tab(url=parameters.get("url"), browser=parameters.get("browser"), player=player)

class BrowserTabCloseTab(Action):
    @property
    def name(self) -> str: return "browser_tab_close_tab"
    @property
    def description(self) -> str: return "Close the current browser tab."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().close_tab(browser=parameters.get("browser"), player=player)

class BrowserTabSwitchTab(Action):
    @property
    def name(self) -> str: return "browser_tab_switch_tab"
    @property
    def description(self) -> str: return "Switch to a specific tab by index."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"index": {"type": "INTEGER", "description": "Tab index (0-based)"}}, "required": ["index"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().switch_tab(parameters["index"], browser=parameters.get("browser"), player=player)

class BrowserTabListTabs(Action):
    @property
    def name(self) -> str: return "browser_tab_list_tabs"
    @property
    def description(self) -> str: return "List all open tabs with their titles and URLs."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().list_tabs(browser=parameters.get("browser"), player=player)

class BrowserTabDuplicateTab(Action):
    @property
    def name(self) -> str: return "browser_tab_duplicate_tab"
    @property
    def description(self) -> str: return "Duplicate the current tab."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        engine = BrowserEngine()
        url_result = engine.get_url(browser=parameters.get("browser"), player=player)
        url = url_result.get("structured_data", {}).get("url", "")
        return engine.new_tab(url=url, browser=parameters.get("browser"), player=player)

for cls in [BrowserTabNewTab, BrowserTabCloseTab, BrowserTabSwitchTab, BrowserTabListTabs, BrowserTabDuplicateTab]:
    ActionRegistry.register(cls)
