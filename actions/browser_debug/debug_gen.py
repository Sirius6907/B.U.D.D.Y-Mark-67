"""Auto-generated browser_debug tools — DO NOT EDIT MANUALLY."""
from actions.base import Action, ActionRegistry
from typing import Any


class BrowserDebugEnableDevtools(Action):
    @property
    def name(self) -> str: return "browser_debug_enable_devtools"
    @property
    def description(self) -> str: return "Enable developer tools overlay."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().enable_devtools(browser=parameters.get("browser"), player=player)


class BrowserDebugTakeDomSnapshot(Action):
    @property
    def name(self) -> str: return "browser_debug_take_dom_snapshot"
    @property
    def description(self) -> str: return "Take a full DOM snapshot."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().dom_snapshot(browser=parameters.get("browser"), player=player)


class BrowserDebugListEventListeners(Action):
    @property
    def name(self) -> str: return "browser_debug_list_event_listeners"
    @property
    def description(self) -> str: return "List event listeners on element."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}}, "required": ["selector"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().list_listeners(parameters["selector"], browser=parameters.get("browser"), player=player)


class BrowserDebugEmulateMobile(Action):
    @property
    def name(self) -> str: return "browser_debug_emulate_mobile"
    @property
    def description(self) -> str: return "Emulate a mobile device."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"device": {"type": "STRING"}}, "required": ["device"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().emulate_mobile(parameters["device"], browser=parameters.get("browser"), player=player)


class BrowserDebugEmulateGeolocation(Action):
    @property
    def name(self) -> str: return "browser_debug_emulate_geolocation"
    @property
    def description(self) -> str: return "Set geolocation."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"lat": {"type": "STRING"}, "lon": {"type": "STRING"}}, "required": ["lat", "lon"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().set_geo(parameters["lat"], parameters["lon"], browser=parameters.get("browser"), player=player)


class BrowserDebugToggleOffline(Action):
    @property
    def name(self) -> str: return "browser_debug_toggle_offline"
    @property
    def description(self) -> str: return "Toggle offline mode."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().toggle_offline(browser=parameters.get("browser"), player=player)


class BrowserDebugThrottleNetwork(Action):
    @property
    def name(self) -> str: return "browser_debug_throttle_network"
    @property
    def description(self) -> str: return "Throttle network speed."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"profile": {"type": "STRING"}}, "required": ["profile"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().throttle(parameters["profile"], browser=parameters.get("browser"), player=player)


class BrowserDebugClearAllData(Action):
    @property
    def name(self) -> str: return "browser_debug_clear_all_data"
    @property
    def description(self) -> str: return "Clear all browsing data."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().clear_all(browser=parameters.get("browser"), player=player)


class BrowserDebugGetAccessibilityTree(Action):
    @property
    def name(self) -> str: return "browser_debug_get_accessibility_tree"
    @property
    def description(self) -> str: return "Get accessibility tree."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().a11y_tree(browser=parameters.get("browser"), player=player)


class BrowserDebugCheckPageErrors(Action):
    @property
    def name(self) -> str: return "browser_debug_check_page_errors"
    @property
    def description(self) -> str: return "Check page for JS errors."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().check_errors(browser=parameters.get("browser"), player=player)


for _cls in [BrowserDebugEnableDevtools, BrowserDebugTakeDomSnapshot, BrowserDebugListEventListeners, BrowserDebugEmulateMobile, BrowserDebugEmulateGeolocation, BrowserDebugToggleOffline, BrowserDebugThrottleNetwork, BrowserDebugClearAllData, BrowserDebugGetAccessibilityTree, BrowserDebugCheckPageErrors]:
    ActionRegistry.register(_cls)
