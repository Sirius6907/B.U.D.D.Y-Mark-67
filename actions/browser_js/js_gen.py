"""Auto-generated browser_js tools — DO NOT EDIT MANUALLY."""
from actions.base import Action, ActionRegistry
from typing import Any


class BrowserJsExecute(Action):
    @property
    def name(self) -> str: return "browser_js_execute"
    @property
    def description(self) -> str: return "Execute JavaScript code in page."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"code": {"type": "STRING"}}, "required": ["code"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().execute_js(parameters["code"], browser=parameters.get("browser"), player=player)


class BrowserJsEvaluate(Action):
    @property
    def name(self) -> str: return "browser_js_evaluate"
    @property
    def description(self) -> str: return "Evaluate JS and return result."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"expression": {"type": "STRING"}}, "required": ["expression"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().evaluate_js(parameters["expression"], browser=parameters.get("browser"), player=player)


class BrowserJsInjectCss(Action):
    @property
    def name(self) -> str: return "browser_js_inject_css"
    @property
    def description(self) -> str: return "Inject CSS styles into page."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"css": {"type": "STRING"}}, "required": ["css"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().inject_css(parameters["css"], browser=parameters.get("browser"), player=player)


class BrowserJsInjectScript(Action):
    @property
    def name(self) -> str: return "browser_js_inject_script"
    @property
    def description(self) -> str: return "Inject a script tag into page."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"src": {"type": "STRING"}}, "required": ["src"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().inject_script(parameters["src"], browser=parameters.get("browser"), player=player)


class BrowserJsRemoveElement(Action):
    @property
    def name(self) -> str: return "browser_js_remove_element"
    @property
    def description(self) -> str: return "Remove element from DOM via JS."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}}, "required": ["selector"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().remove_element(parameters["selector"], browser=parameters.get("browser"), player=player)


class BrowserJsSetAttribute(Action):
    @property
    def name(self) -> str: return "browser_js_set_attribute"
    @property
    def description(self) -> str: return "Set element attribute via JS."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}, "attr": {"type": "STRING"}, "value": {"type": "STRING"}}, "required": ["selector", "attr", "value"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().set_attr(parameters["selector"], parameters["attr"], parameters["value"], browser=parameters.get("browser"), player=player)


class BrowserJsAddClass(Action):
    @property
    def name(self) -> str: return "browser_js_add_class"
    @property
    def description(self) -> str: return "Add CSS class to element."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}, "class_name": {"type": "STRING"}}, "required": ["selector", "class_name"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().add_class(parameters["selector"], parameters["class_name"], browser=parameters.get("browser"), player=player)


class BrowserJsRemoveClass(Action):
    @property
    def name(self) -> str: return "browser_js_remove_class"
    @property
    def description(self) -> str: return "Remove CSS class from element."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}, "class_name": {"type": "STRING"}}, "required": ["selector", "class_name"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().remove_class(parameters["selector"], parameters["class_name"], browser=parameters.get("browser"), player=player)


class BrowserJsSetInnerHtml(Action):
    @property
    def name(self) -> str: return "browser_js_set_inner_html"
    @property
    def description(self) -> str: return "Set innerHTML of element."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}, "html": {"type": "STRING"}}, "required": ["selector", "html"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().set_html(parameters["selector"], parameters["html"], browser=parameters.get("browser"), player=player)


class BrowserJsGetComputedProperty(Action):
    @property
    def name(self) -> str: return "browser_js_get_computed_property"
    @property
    def description(self) -> str: return "Get computed CSS property."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}, "property": {"type": "STRING"}}, "required": ["selector", "property"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().get_css(parameters["selector"], parameters["property"], browser=parameters.get("browser"), player=player)


for _cls in [BrowserJsExecute, BrowserJsEvaluate, BrowserJsInjectCss, BrowserJsInjectScript, BrowserJsRemoveElement, BrowserJsSetAttribute, BrowserJsAddClass, BrowserJsRemoveClass, BrowserJsSetInnerHtml, BrowserJsGetComputedProperty]:
    ActionRegistry.register(_cls)
