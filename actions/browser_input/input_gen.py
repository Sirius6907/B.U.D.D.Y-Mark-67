"""Auto-generated browser_input tools — DO NOT EDIT MANUALLY."""
from actions.base import Action, ActionRegistry
from typing import Any


class BrowserInputClearField(Action):
    @property
    def name(self) -> str: return "browser_input_clear_field"
    @property
    def description(self) -> str: return "Clear the value of an input field."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}}, "required": ["selector"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().clear_field(parameters["selector"], browser=parameters.get("browser"), player=player)


class BrowserInputCheckCheckbox(Action):
    @property
    def name(self) -> str: return "browser_input_check_checkbox"
    @property
    def description(self) -> str: return "Check a checkbox."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}}, "required": ["selector"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().check(parameters["selector"], browser=parameters.get("browser"), player=player)


class BrowserInputUncheckCheckbox(Action):
    @property
    def name(self) -> str: return "browser_input_uncheck_checkbox"
    @property
    def description(self) -> str: return "Uncheck a checkbox."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}}, "required": ["selector"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().uncheck(parameters["selector"], browser=parameters.get("browser"), player=player)


class BrowserInputToggleCheckbox(Action):
    @property
    def name(self) -> str: return "browser_input_toggle_checkbox"
    @property
    def description(self) -> str: return "Toggle checkbox state."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}}, "required": ["selector"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().toggle(parameters["selector"], browser=parameters.get("browser"), player=player)


class BrowserInputSelectRadio(Action):
    @property
    def name(self) -> str: return "browser_input_select_radio"
    @property
    def description(self) -> str: return "Select a radio button."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}}, "required": ["selector"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().select_radio(parameters["selector"], browser=parameters.get("browser"), player=player)


class BrowserInputSetDate(Action):
    @property
    def name(self) -> str: return "browser_input_set_date"
    @property
    def description(self) -> str: return "Set a date input value."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}, "date": {"type": "STRING"}}, "required": ["selector", "date"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().set_date(parameters["selector"], parameters["date"], browser=parameters.get("browser"), player=player)


class BrowserInputSetRange(Action):
    @property
    def name(self) -> str: return "browser_input_set_range"
    @property
    def description(self) -> str: return "Set a range/slider value."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}, "value": {"type": "STRING"}}, "required": ["selector", "value"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().set_range(parameters["selector"], parameters["value"], browser=parameters.get("browser"), player=player)


class BrowserInputSubmitForm(Action):
    @property
    def name(self) -> str: return "browser_input_submit_form"
    @property
    def description(self) -> str: return "Submit a form."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}}, "required": ["selector"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().submit_form(parameters["selector"], browser=parameters.get("browser"), player=player)


class BrowserInputPressEnter(Action):
    @property
    def name(self) -> str: return "browser_input_press_enter"
    @property
    def description(self) -> str: return "Press Enter key."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().press_enter(browser=parameters.get("browser"), player=player)


class BrowserInputPressTab(Action):
    @property
    def name(self) -> str: return "browser_input_press_tab"
    @property
    def description(self) -> str: return "Press Tab key."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().press_tab(browser=parameters.get("browser"), player=player)


class BrowserInputPressEscape(Action):
    @property
    def name(self) -> str: return "browser_input_press_escape"
    @property
    def description(self) -> str: return "Press Escape key."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().press_escape(browser=parameters.get("browser"), player=player)


class BrowserInputKeyboardShortcut(Action):
    @property
    def name(self) -> str: return "browser_input_keyboard_shortcut"
    @property
    def description(self) -> str: return "Execute a keyboard shortcut."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"keys": {"type": "STRING"}}, "required": ["keys"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().shortcut(parameters["keys"], browser=parameters.get("browser"), player=player)


class BrowserInputTypeSlowly(Action):
    @property
    def name(self) -> str: return "browser_input_type_slowly"
    @property
    def description(self) -> str: return "Type text character by character."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}, "text": {"type": "STRING"}}, "required": ["selector", "text"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().type_slowly(parameters["selector"], parameters["text"], browser=parameters.get("browser"), player=player)


class BrowserInputPasteText(Action):
    @property
    def name(self) -> str: return "browser_input_paste_text"
    @property
    def description(self) -> str: return "Paste text from clipboard into field."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}, "text": {"type": "STRING"}}, "required": ["selector", "text"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().paste_text(parameters["selector"], parameters["text"], browser=parameters.get("browser"), player=player)


class BrowserInputScrollUp(Action):
    @property
    def name(self) -> str: return "browser_input_scroll_up"
    @property
    def description(self) -> str: return "Scroll page up."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().scroll_up(browser=parameters.get("browser"), player=player)


class BrowserInputScrollDown(Action):
    @property
    def name(self) -> str: return "browser_input_scroll_down"
    @property
    def description(self) -> str: return "Scroll page down."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().scroll_down(browser=parameters.get("browser"), player=player)


class BrowserInputScrollToTop(Action):
    @property
    def name(self) -> str: return "browser_input_scroll_to_top"
    @property
    def description(self) -> str: return "Scroll to top of page."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().scroll_top(browser=parameters.get("browser"), player=player)


class BrowserInputScrollToBottom(Action):
    @property
    def name(self) -> str: return "browser_input_scroll_to_bottom"
    @property
    def description(self) -> str: return "Scroll to bottom of page."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().scroll_bottom(browser=parameters.get("browser"), player=player)


for _cls in [BrowserInputClearField, BrowserInputCheckCheckbox, BrowserInputUncheckCheckbox, BrowserInputToggleCheckbox, BrowserInputSelectRadio, BrowserInputSetDate, BrowserInputSetRange, BrowserInputSubmitForm, BrowserInputPressEnter, BrowserInputPressTab, BrowserInputPressEscape, BrowserInputKeyboardShortcut, BrowserInputTypeSlowly, BrowserInputPasteText, BrowserInputScrollUp, BrowserInputScrollDown, BrowserInputScrollToTop, BrowserInputScrollToBottom]:
    ActionRegistry.register(_cls)
