"""Auto-generated browser_extract tools — DO NOT EDIT MANUALLY."""
from actions.base import Action, ActionRegistry
from typing import Any


class BrowserExtractGetMeta(Action):
    @property
    def name(self) -> str: return "browser_extract_get_meta"
    @property
    def description(self) -> str: return "Get page meta tags."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().get_meta(browser=parameters.get("browser"), player=player)


class BrowserExtractGetImages(Action):
    @property
    def name(self) -> str: return "browser_extract_get_images"
    @property
    def description(self) -> str: return "Get all image URLs from page."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().get_images(browser=parameters.get("browser"), player=player)


class BrowserExtractGetHeadings(Action):
    @property
    def name(self) -> str: return "browser_extract_get_headings"
    @property
    def description(self) -> str: return "Get all heading elements."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().get_headings(browser=parameters.get("browser"), player=player)


class BrowserExtractGetTables(Action):
    @property
    def name(self) -> str: return "browser_extract_get_tables"
    @property
    def description(self) -> str: return "Extract table data as structured JSON."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().get_tables(browser=parameters.get("browser"), player=player)


class BrowserExtractGetForms(Action):
    @property
    def name(self) -> str: return "browser_extract_get_forms"
    @property
    def description(self) -> str: return "Get all form elements and their inputs."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().get_forms(browser=parameters.get("browser"), player=player)


class BrowserExtractGetCookies(Action):
    @property
    def name(self) -> str: return "browser_extract_get_cookies"
    @property
    def description(self) -> str: return "Get all cookies for current domain."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().get_cookies(browser=parameters.get("browser"), player=player)


class BrowserExtractGetLocalStorage(Action):
    @property
    def name(self) -> str: return "browser_extract_get_local_storage"
    @property
    def description(self) -> str: return "Get local storage data."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().get_local_storage(browser=parameters.get("browser"), player=player)


class BrowserExtractGetSessionStorage(Action):
    @property
    def name(self) -> str: return "browser_extract_get_session_storage"
    @property
    def description(self) -> str: return "Get session storage data."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().get_session_storage(browser=parameters.get("browser"), player=player)


class BrowserExtractGetConsoleLogs(Action):
    @property
    def name(self) -> str: return "browser_extract_get_console_logs"
    @property
    def description(self) -> str: return "Get browser console logs."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().get_console(browser=parameters.get("browser"), player=player)


class BrowserExtractGetNetworkRequests(Action):
    @property
    def name(self) -> str: return "browser_extract_get_network_requests"
    @property
    def description(self) -> str: return "Get network request log."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().get_network(browser=parameters.get("browser"), player=player)


class BrowserExtractGetPageMetrics(Action):
    @property
    def name(self) -> str: return "browser_extract_get_page_metrics"
    @property
    def description(self) -> str: return "Get page performance metrics."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().get_metrics(browser=parameters.get("browser"), player=player)


class BrowserExtractGetComputedStyle(Action):
    @property
    def name(self) -> str: return "browser_extract_get_computed_style"
    @property
    def description(self) -> str: return "Get computed CSS of element."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"selector": {"type": "STRING"}}, "required": ["selector"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().get_style(parameters["selector"], browser=parameters.get("browser"), player=player)


class BrowserExtractPdfPage(Action):
    @property
    def name(self) -> str: return "browser_extract_pdf_page"
    @property
    def description(self) -> str: return "Save current page as PDF."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"path": {"type": "STRING"}}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().pdf(parameters["path"], browser=parameters.get("browser"), player=player)


class BrowserExtractGetSelection(Action):
    @property
    def name(self) -> str: return "browser_extract_get_selection"
    @property
    def description(self) -> str: return "Get currently selected text."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().get_selection(browser=parameters.get("browser"), player=player)


class BrowserExtractGetPageSize(Action):
    @property
    def name(self) -> str: return "browser_extract_get_page_size"
    @property
    def description(self) -> str: return "Get page dimensions."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().get_page_size(browser=parameters.get("browser"), player=player)


for _cls in [BrowserExtractGetMeta, BrowserExtractGetImages, BrowserExtractGetHeadings, BrowserExtractGetTables, BrowserExtractGetForms, BrowserExtractGetCookies, BrowserExtractGetLocalStorage, BrowserExtractGetSessionStorage, BrowserExtractGetConsoleLogs, BrowserExtractGetNetworkRequests, BrowserExtractGetPageMetrics, BrowserExtractGetComputedStyle, BrowserExtractPdfPage, BrowserExtractGetSelection, BrowserExtractGetPageSize]:
    ActionRegistry.register(_cls)
