"""Real browser_nav tools — replaces tool_1.py through tool_5.py stubs."""
from actions.base import Action, ActionRegistry
from typing import Optional, Any, Callable


class BrowserNavNavigateToUrl(Action):
    @property
    def name(self) -> str: return "browser_nav_navigate_to_url"
    @property
    def description(self) -> str: return "Navigate to a specific URL in the browser."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"url": {"type": "STRING", "description": "URL to navigate to"}, "browser": {"type": "STRING", "description": "Target browser (optional)"}}, "required": ["url"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().navigate(parameters["url"], browser=parameters.get("browser"), player=player)

class BrowserNavNavigateToDomain(Action):
    @property
    def name(self) -> str: return "browser_nav_navigate_to_domain"
    @property
    def description(self) -> str: return "Navigate to a domain name (auto-adds https://)."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"domain": {"type": "STRING", "description": "Domain name"}}, "required": ["domain"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().navigate(parameters["domain"], browser=parameters.get("browser"), player=player)

class BrowserNavSearchGoogle(Action):
    @property
    def name(self) -> str: return "browser_nav_search_google"
    @property
    def description(self) -> str: return "Search Google for a query."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"query": {"type": "STRING", "description": "Search query"}}, "required": ["query"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().search(parameters["query"], "google", browser=parameters.get("browser"), player=player)

class BrowserNavRefreshPage(Action):
    @property
    def name(self) -> str: return "browser_nav_refresh_page"
    @property
    def description(self) -> str: return "Refresh/reload the current page."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().refresh(browser=parameters.get("browser"), player=player)

class BrowserNavGoBack(Action):
    @property
    def name(self) -> str: return "browser_nav_go_back"
    @property
    def description(self) -> str: return "Navigate back in browser history."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().go_back(browser=parameters.get("browser"), player=player)

for cls in [BrowserNavNavigateToUrl, BrowserNavNavigateToDomain, BrowserNavSearchGoogle, BrowserNavRefreshPage, BrowserNavGoBack]:
    ActionRegistry.register(cls)
