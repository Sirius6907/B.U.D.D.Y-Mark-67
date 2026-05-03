"""Real browser_auth tools — login, detect, captcha, logout, cookie consent."""
from actions.base import Action, ActionRegistry
from typing import Any
from runtime.results.builder import build_tool_result
from runtime.contracts.models import RiskLevel


class BrowserAuthLoginWithCredentials(Action):
    @property
    def name(self) -> str: return "browser_auth_login_with_credentials"
    @property
    def description(self) -> str: return "Fill and submit a login form with username and password."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"username": {"type": "STRING"}, "password": {"type": "STRING"}, "username_selector": {"type": "STRING", "description": "CSS selector for username field (optional)"}, "password_selector": {"type": "STRING", "description": "CSS selector for password field (optional)"}, "submit_selector": {"type": "STRING", "description": "CSS selector for submit button (optional)"}}, "required": ["username", "password"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        engine = BrowserEngine()
        u_sel = parameters.get("username_selector", "input[type='email'], input[type='text'], input[name='username'], input[name='email']")
        p_sel = parameters.get("password_selector", "input[type='password']")
        r1 = engine.type_text(u_sel, parameters["username"], True, browser=parameters.get("browser"), player=player)
        r2 = engine.type_text(p_sel, parameters["password"], True, browser=parameters.get("browser"), player=player)
        sub = parameters.get("submit_selector")
        if sub:
            r3 = engine.click(selector=sub, browser=parameters.get("browser"), player=player)
        else:
            r3 = engine.press_key("Enter", browser=parameters.get("browser"), player=player)
        return build_tool_result(tool_name=self.name, operation="login", risk_level=RiskLevel.HIGH, status="success" if r3.get("status") == "success" else "partial", summary="Login form filled and submitted", structured_data={"steps": [r1.get("status"), r2.get("status"), r3.get("status")]}, preconditions=["login_page_visible"], postconditions=["user_authenticated"])

class BrowserAuthDetectLoginPage(Action):
    @property
    def name(self) -> str: return "browser_auth_detect_login_page"
    @property
    def description(self) -> str: return "Detect if the current page contains a login form."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        result = BrowserEngine().get_page_text(browser=parameters.get("browser"), player=player)
        text = result.get("structured_data", {}).get("text", "").lower()
        has_login = any(w in text for w in ["sign in", "log in", "login", "username", "password"])
        return build_tool_result(tool_name=self.name, operation="detect_login", risk_level=RiskLevel.LOW, status="success", summary=f"Login page detected: {has_login}", structured_data={"is_login_page": has_login}, idempotent=True, preconditions=["browser_session_active"], postconditions=[])

class BrowserAuthDetectCaptcha(Action):
    @property
    def name(self) -> str: return "browser_auth_detect_captcha"
    @property
    def description(self) -> str: return "Detect if a CAPTCHA is present on the current page."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        result = BrowserEngine().get_page_text(browser=parameters.get("browser"), player=player)
        text = result.get("structured_data", {}).get("text", "").lower()
        has_captcha = any(w in text for w in ["captcha", "recaptcha", "hcaptcha", "verify you are human", "i'm not a robot"])
        return build_tool_result(tool_name=self.name, operation="detect_captcha", risk_level=RiskLevel.LOW, status="success", summary=f"CAPTCHA detected: {has_captcha}", structured_data={"has_captcha": has_captcha}, idempotent=True, preconditions=["browser_session_active"], postconditions=[])

class BrowserAuthHandleCookieConsent(Action):
    @property
    def name(self) -> str: return "browser_auth_handle_cookie_consent"
    @property
    def description(self) -> str: return "Accept cookie consent banner if present."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        engine = BrowserEngine()
        for text in ["Accept all", "Accept", "I agree", "OK", "Got it", "Allow all"]:
            r = engine.click(text=text, browser=parameters.get("browser"), player=player)
            if r.get("status") == "success":
                return build_tool_result(tool_name=self.name, operation="cookie_consent", risk_level=RiskLevel.LOW, status="success", summary=f"Accepted cookies via: {text}", structured_data={"clicked_text": text}, preconditions=["cookie_banner_visible"], postconditions=["cookie_banner_dismissed"])
        return build_tool_result(tool_name=self.name, operation="cookie_consent", risk_level=RiskLevel.LOW, status="not_found", summary="No cookie consent banner found", structured_data={}, preconditions=[], postconditions=[])

class BrowserAuthDismissPopup(Action):
    @property
    def name(self) -> str: return "browser_auth_dismiss_popup"
    @property
    def description(self) -> str: return "Dismiss any modal/popup dialog on the page."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        engine = BrowserEngine()
        for text in ["Close", "✕", "×", "No thanks", "Dismiss", "Not now", "Maybe later"]:
            r = engine.click(text=text, browser=parameters.get("browser"), player=player)
            if r.get("status") == "success":
                return build_tool_result(tool_name=self.name, operation="dismiss_popup", risk_level=RiskLevel.LOW, status="success", summary=f"Dismissed via: {text}", structured_data={"clicked_text": text}, preconditions=[], postconditions=["popup_dismissed"])
        r = engine.press_key("Escape", browser=parameters.get("browser"), player=player)
        return build_tool_result(tool_name=self.name, operation="dismiss_popup", risk_level=RiskLevel.LOW, status="attempted", summary="Pressed Escape to dismiss", structured_data={}, preconditions=[], postconditions=[])

for cls in [BrowserAuthLoginWithCredentials, BrowserAuthDetectLoginPage, BrowserAuthDetectCaptcha, BrowserAuthHandleCookieConsent, BrowserAuthDismissPopup]:
    ActionRegistry.register(cls)
