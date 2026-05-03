"""Real browser_extract tools — get_title, get_url, get_html, screenshot, get_links."""
from actions.base import Action, ActionRegistry
from typing import Any
from runtime.results.builder import build_tool_result
from runtime.contracts.models import RiskLevel


class BrowserExtractGetTitle(Action):
    @property
    def name(self) -> str: return "browser_extract_get_title"
    @property
    def description(self) -> str: return "Get the title of the current page."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().get_title(browser=parameters.get("browser"), player=player)

class BrowserExtractGetUrl(Action):
    @property
    def name(self) -> str: return "browser_extract_get_url"
    @property
    def description(self) -> str: return "Get the current page URL."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().get_url(browser=parameters.get("browser"), player=player)

class BrowserExtractGetHtml(Action):
    @property
    def name(self) -> str: return "browser_extract_get_html"
    @property
    def description(self) -> str: return "Get full HTML source of the current page."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING", "description": "Optional CSS selector for partial HTML"}}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().get_html(selector=parameters.get("selector"), browser=parameters.get("browser"), player=player)

class BrowserExtractScreenshot(Action):
    @property
    def name(self) -> str: return "browser_extract_screenshot"
    @property
    def description(self) -> str: return "Take a screenshot of the current page."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"path": {"type": "STRING", "description": "File path to save screenshot"}}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().screenshot(path=parameters.get("path"), browser=parameters.get("browser"), player=player)

class BrowserExtractGetLinks(Action):
    @property
    def name(self) -> str: return "browser_extract_get_links"
    @property
    def description(self) -> str: return "Get all links (anchor hrefs) from the current page."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().get_links(browser=parameters.get("browser"), player=player)

for cls in [BrowserExtractGetTitle, BrowserExtractGetUrl, BrowserExtractGetHtml, BrowserExtractScreenshot, BrowserExtractGetLinks]:
    ActionRegistry.register(cls)
