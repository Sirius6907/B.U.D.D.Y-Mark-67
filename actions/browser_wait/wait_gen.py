"""Auto-generated browser_wait tools — DO NOT EDIT MANUALLY."""
from actions.base import Action, ActionRegistry
from typing import Any


class BrowserWaitForText(Action):
    @property
    def name(self) -> str: return "browser_wait_for_text"
    @property
    def description(self) -> str: return "Wait until text appears on page."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"text": {"type": "STRING"}}, "required": ["text"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().wait_text(parameters["text"], browser=parameters.get("browser"), player=player)


class BrowserWaitForUrlChange(Action):
    @property
    def name(self) -> str: return "browser_wait_for_url_change"
    @property
    def description(self) -> str: return "Wait for URL to change."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().wait_url(browser=parameters.get("browser"), player=player)


class BrowserWaitForDownload(Action):
    @property
    def name(self) -> str: return "browser_wait_for_download"
    @property
    def description(self) -> str: return "Wait for a download to complete."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().wait_download(browser=parameters.get("browser"), player=player)


class BrowserWaitSeconds(Action):
    @property
    def name(self) -> str: return "browser_wait_seconds"
    @property
    def description(self) -> str: return "Wait for N seconds."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"seconds": {"type": "INTEGER"}}, "required": ["seconds"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().wait_seconds(parameters["seconds"], browser=parameters.get("browser"), player=player)


class BrowserWaitForNetworkIdle(Action):
    @property
    def name(self) -> str: return "browser_wait_for_network_idle"
    @property
    def description(self) -> str: return "Wait for network to be idle."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().wait_network(browser=parameters.get("browser"), player=player)


class BrowserWaitForElementGone(Action):
    @property
    def name(self) -> str: return "browser_wait_for_element_gone"
    @property
    def description(self) -> str: return "Wait for element to disappear."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}}, "required": ["selector"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().wait_gone(parameters["selector"], browser=parameters.get("browser"), player=player)


class BrowserWaitForNavigation(Action):
    @property
    def name(self) -> str: return "browser_wait_for_navigation"
    @property
    def description(self) -> str: return "Wait for navigation to complete."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().wait_navigation(browser=parameters.get("browser"), player=player)


class BrowserWaitForPopup(Action):
    @property
    def name(self) -> str: return "browser_wait_for_popup"
    @property
    def description(self) -> str: return "Wait for popup/dialog to appear."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().wait_popup(browser=parameters.get("browser"), player=player)


class BrowserWaitForFrame(Action):
    @property
    def name(self) -> str: return "browser_wait_for_frame"
    @property
    def description(self) -> str: return "Wait for iframe to load."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}}, "required": ["selector"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().wait_frame(parameters["selector"], browser=parameters.get("browser"), player=player)


class BrowserWaitForValue(Action):
    @property
    def name(self) -> str: return "browser_wait_for_value"
    @property
    def description(self) -> str: return "Wait for input to have specific value."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}, "value": {"type": "STRING"}}, "required": ["selector", "value"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().wait_value(parameters["selector"], parameters["value"], browser=parameters.get("browser"), player=player)


for _cls in [BrowserWaitForText, BrowserWaitForUrlChange, BrowserWaitForDownload, BrowserWaitSeconds, BrowserWaitForNetworkIdle, BrowserWaitForElementGone, BrowserWaitForNavigation, BrowserWaitForPopup, BrowserWaitForFrame, BrowserWaitForValue]:
    ActionRegistry.register(_cls)
