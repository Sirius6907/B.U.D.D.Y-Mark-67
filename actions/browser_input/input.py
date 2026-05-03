"""Real browser_input tools — type, fill_form, select, upload, scroll."""
from actions.base import Action, ActionRegistry
from typing import Any
from runtime.results.builder import build_tool_result
from runtime.contracts.models import RiskLevel


class BrowserInputTypeText(Action):
    @property
    def name(self) -> str: return "browser_input_type_text"
    @property
    def description(self) -> str: return "Type text into a focused or selected input field."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}, "text": {"type": "STRING"}, "clear_first": {"type": "BOOLEAN", "description": "Clear the field before typing"}}, "required": ["selector", "text"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().type_text(parameters["selector"], parameters["text"], parameters.get("clear_first", True), browser=parameters.get("browser"), player=player)

class BrowserInputFillField(Action):
    @property
    def name(self) -> str: return "browser_input_fill_field"
    @property
    def description(self) -> str: return "Fill a field by label text (finds associated input)."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"label": {"type": "STRING"}, "value": {"type": "STRING"}}, "required": ["label", "value"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().fill_by_label(parameters["label"], parameters["value"], browser=parameters.get("browser"), player=player)

class BrowserInputSelectDropdown(Action):
    @property
    def name(self) -> str: return "browser_input_select_dropdown"
    @property
    def description(self) -> str: return "Select an option from a dropdown by value or label."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}, "value": {"type": "STRING"}}, "required": ["selector", "value"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().select_option(parameters["selector"], parameters["value"], browser=parameters.get("browser"), player=player)

class BrowserInputUploadFile(Action):
    @property
    def name(self) -> str: return "browser_input_upload_file"
    @property
    def description(self) -> str: return "Upload a file using a file input element."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}, "file_path": {"type": "STRING"}}, "required": ["selector", "file_path"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().upload_file(parameters["selector"], parameters["file_path"], browser=parameters.get("browser"), player=player)

class BrowserInputScrollPage(Action):
    @property
    def name(self) -> str: return "browser_input_scroll_page"
    @property
    def description(self) -> str: return "Scroll the page up or down."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"direction": {"type": "STRING", "description": "up or down"}, "amount": {"type": "INTEGER", "description": "Pixels to scroll (default 500)"}}, "required": ["direction"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().scroll(parameters["direction"], parameters.get("amount", 500), browser=parameters.get("browser"), player=player)

for cls in [BrowserInputTypeText, BrowserInputFillField, BrowserInputSelectDropdown, BrowserInputUploadFile, BrowserInputScrollPage]:
    ActionRegistry.register(cls)
