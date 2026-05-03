"""Auto-generated browser_nav tools — DO NOT EDIT MANUALLY."""
from actions.base import Action, ActionRegistry
from typing import Any


class BrowserNavGoForward(Action):
    @property
    def name(self) -> str: return "browser_nav_go_forward"
    @property
    def description(self) -> str: return "Navigate forward in browser history."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().go_forward(browser=parameters.get("browser"), player=player)


class BrowserNavSearchBing(Action):
    @property
    def name(self) -> str: return "browser_nav_search_bing"
    @property
    def description(self) -> str: return "Search Bing for a query."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"query": {"type": "STRING"}}, "required": ["query"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().search(parameters["query"], browser=parameters.get("browser"), player=player)


class BrowserNavSearchDuckduckgo(Action):
    @property
    def name(self) -> str: return "browser_nav_search_duckduckgo"
    @property
    def description(self) -> str: return "Search DuckDuckGo for a query."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"query": {"type": "STRING"}}, "required": ["query"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().search(parameters["query"], browser=parameters.get("browser"), player=player)


class BrowserNavSearchYoutube(Action):
    @property
    def name(self) -> str: return "browser_nav_search_youtube"
    @property
    def description(self) -> str: return "Search YouTube for a query."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"query": {"type": "STRING"}}, "required": ["query"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().search(parameters["query"], browser=parameters.get("browser"), player=player)


class BrowserNavOpenNewWindow(Action):
    @property
    def name(self) -> str: return "browser_nav_open_new_window"
    @property
    def description(self) -> str: return "Open a new browser window."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().new_window(browser=parameters.get("browser"), player=player)


class BrowserNavNavigateToBookmark(Action):
    @property
    def name(self) -> str: return "browser_nav_navigate_to_bookmark"
    @property
    def description(self) -> str: return "Navigate to a bookmarked URL."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"url": {"type": "STRING"}}, "required": ["url"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().navigate(parameters["url"], browser=parameters.get("browser"), player=player)


class BrowserNavWaitForLoad(Action):
    @property
    def name(self) -> str: return "browser_nav_wait_for_load"
    @property
    def description(self) -> str: return "Wait for page to fully load."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().wait_for_load(browser=parameters.get("browser"), player=player)


class BrowserNavWaitForElement(Action):
    @property
    def name(self) -> str: return "browser_nav_wait_for_element"
    @property
    def description(self) -> str: return "Wait for a specific element to appear."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}}, "required": ["selector"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().wait_for_element(parameters["selector"], browser=parameters.get("browser"), player=player)


class BrowserNavStopLoading(Action):
    @property
    def name(self) -> str: return "browser_nav_stop_loading"
    @property
    def description(self) -> str: return "Stop the current page from loading."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().stop_loading(browser=parameters.get("browser"), player=player)


class BrowserNavSetViewport(Action):
    @property
    def name(self) -> str: return "browser_nav_set_viewport"
    @property
    def description(self) -> str: return "Set viewport size."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"width": {"type": "INTEGER"}, "height": {"type": "INTEGER"}}, "required": ["width", "height"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().set_viewport(parameters["width"], parameters["height"], browser=parameters.get("browser"), player=player)


for _cls in [BrowserNavGoForward, BrowserNavSearchBing, BrowserNavSearchDuckduckgo, BrowserNavSearchYoutube, BrowserNavOpenNewWindow, BrowserNavNavigateToBookmark, BrowserNavWaitForLoad, BrowserNavWaitForElement, BrowserNavStopLoading, BrowserNavSetViewport]:
    ActionRegistry.register(_cls)
