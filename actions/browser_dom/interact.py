"""Real browser_dom tools — click, smart_click, get_text, press_key, type."""
from actions.base import Action, ActionRegistry
from typing import Any


class BrowserDomClickElement(Action):
    @property
    def name(self) -> str: return "browser_dom_click_element"
    @property
    def description(self) -> str: return "Click an element by CSS selector."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING", "description": "CSS selector"}}, "required": ["selector"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().click(selector=parameters["selector"], browser=parameters.get("browser"), player=player)

class BrowserDomClickByText(Action):
    @property
    def name(self) -> str: return "browser_dom_click_by_text"
    @property
    def description(self) -> str: return "Click an element by its visible text content."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"text": {"type": "STRING", "description": "Visible text to click"}}, "required": ["text"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().click(text=parameters["text"], browser=parameters.get("browser"), player=player)

class BrowserDomClickByRole(Action):
    @property
    def name(self) -> str: return "browser_dom_click_by_role"
    @property
    def description(self) -> str: return "Smart click using element description (tries role, text, placeholder, aria-label)."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"description": {"type": "STRING", "description": "Element description"}}, "required": ["description"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().smart_click(parameters["description"], browser=parameters.get("browser"), player=player)

class BrowserDomGetPageText(Action):
    @property
    def name(self) -> str: return "browser_dom_get_page_text"
    @property
    def description(self) -> str: return "Get all visible text content from the current page."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().get_page_text(browser=parameters.get("browser"), player=player)

class BrowserDomPressKey(Action):
    @property
    def name(self) -> str: return "browser_dom_press_key"
    @property
    def description(self) -> str: return "Press a keyboard key (Enter, Escape, Tab, etc.)."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"key": {"type": "STRING", "description": "Key name (e.g. Enter, Escape, F5)"}}, "required": ["key"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().press_key(parameters["key"], browser=parameters.get("browser"), player=player)

for cls in [BrowserDomClickElement, BrowserDomClickByText, BrowserDomClickByRole, BrowserDomGetPageText, BrowserDomPressKey]:
    ActionRegistry.register(cls)
