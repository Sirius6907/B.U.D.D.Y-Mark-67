"""Auto-generated browser_dom tools — DO NOT EDIT MANUALLY."""
from actions.base import Action, ActionRegistry
from typing import Any


class BrowserDomDoubleClick(Action):
    @property
    def name(self) -> str: return "browser_dom_double_click"
    @property
    def description(self) -> str: return "Double click an element."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}}, "required": ["selector"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().double_click(parameters["selector"], browser=parameters.get("browser"), player=player)


class BrowserDomRightClick(Action):
    @property
    def name(self) -> str: return "browser_dom_right_click"
    @property
    def description(self) -> str: return "Right-click (context menu) an element."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}}, "required": ["selector"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().right_click(parameters["selector"], browser=parameters.get("browser"), player=player)


class BrowserDomHoverElement(Action):
    @property
    def name(self) -> str: return "browser_dom_hover_element"
    @property
    def description(self) -> str: return "Hover over an element."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}}, "required": ["selector"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().hover(parameters["selector"], browser=parameters.get("browser"), player=player)


class BrowserDomFocusElement(Action):
    @property
    def name(self) -> str: return "browser_dom_focus_element"
    @property
    def description(self) -> str: return "Focus an element."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}}, "required": ["selector"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().focus(parameters["selector"], browser=parameters.get("browser"), player=player)


class BrowserDomCheckElementExists(Action):
    @property
    def name(self) -> str: return "browser_dom_check_element_exists"
    @property
    def description(self) -> str: return "Check if an element exists on page."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}}, "required": ["selector"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().element_exists(parameters["selector"], browser=parameters.get("browser"), player=player)


class BrowserDomGetElementText(Action):
    @property
    def name(self) -> str: return "browser_dom_get_element_text"
    @property
    def description(self) -> str: return "Get text content of a specific element."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}}, "required": ["selector"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().get_element_text(parameters["selector"], browser=parameters.get("browser"), player=player)


class BrowserDomGetElementAttr(Action):
    @property
    def name(self) -> str: return "browser_dom_get_element_attr"
    @property
    def description(self) -> str: return "Get an attribute of an element."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}, "attribute": {"type": "STRING"}}, "required": ["selector", "attribute"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().get_attribute(parameters["selector"], parameters["attribute"], browser=parameters.get("browser"), player=player)


class BrowserDomCountElements(Action):
    @property
    def name(self) -> str: return "browser_dom_count_elements"
    @property
    def description(self) -> str: return "Count elements matching a selector."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}}, "required": ["selector"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().count_elements(parameters["selector"], browser=parameters.get("browser"), player=player)


class BrowserDomGetElementValue(Action):
    @property
    def name(self) -> str: return "browser_dom_get_element_value"
    @property
    def description(self) -> str: return "Get the value of a form element."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}}, "required": ["selector"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().get_value(parameters["selector"], browser=parameters.get("browser"), player=player)


class BrowserDomIsVisible(Action):
    @property
    def name(self) -> str: return "browser_dom_is_visible"
    @property
    def description(self) -> str: return "Check if an element is visible."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}}, "required": ["selector"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().is_visible(parameters["selector"], browser=parameters.get("browser"), player=player)


class BrowserDomIsEnabled(Action):
    @property
    def name(self) -> str: return "browser_dom_is_enabled"
    @property
    def description(self) -> str: return "Check if an element is enabled."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}}, "required": ["selector"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().is_enabled(parameters["selector"], browser=parameters.get("browser"), player=player)


class BrowserDomIsChecked(Action):
    @property
    def name(self) -> str: return "browser_dom_is_checked"
    @property
    def description(self) -> str: return "Check if a checkbox/radio is checked."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}}, "required": ["selector"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().is_checked(parameters["selector"], browser=parameters.get("browser"), player=player)


class BrowserDomScrollToElement(Action):
    @property
    def name(self) -> str: return "browser_dom_scroll_to_element"
    @property
    def description(self) -> str: return "Scroll until element is visible."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}}, "required": ["selector"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().scroll_to(parameters["selector"], browser=parameters.get("browser"), player=player)


class BrowserDomDragAndDrop(Action):
    @property
    def name(self) -> str: return "browser_dom_drag_and_drop"
    @property
    def description(self) -> str: return "Drag element to target."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"source": {"type": "STRING"}, "target": {"type": "STRING"}}, "required": ["source", "target"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().drag_drop(parameters["source"], parameters["target"], browser=parameters.get("browser"), player=player)


class BrowserDomGetBoundingBox(Action):
    @property
    def name(self) -> str: return "browser_dom_get_bounding_box"
    @property
    def description(self) -> str: return "Get element position and dimensions."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}}, "required": ["selector"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().bounding_box(parameters["selector"], browser=parameters.get("browser"), player=player)


for _cls in [BrowserDomDoubleClick, BrowserDomRightClick, BrowserDomHoverElement, BrowserDomFocusElement, BrowserDomCheckElementExists, BrowserDomGetElementText, BrowserDomGetElementAttr, BrowserDomCountElements, BrowserDomGetElementValue, BrowserDomIsVisible, BrowserDomIsEnabled, BrowserDomIsChecked, BrowserDomScrollToElement, BrowserDomDragAndDrop, BrowserDomGetBoundingBox]:
    ActionRegistry.register(_cls)
