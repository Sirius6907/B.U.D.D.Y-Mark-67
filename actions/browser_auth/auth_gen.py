"""Auto-generated browser_auth tools — DO NOT EDIT MANUALLY."""
from actions.base import Action, ActionRegistry
from typing import Any


class BrowserAuthLogout(Action):
    @property
    def name(self) -> str: return "browser_auth_logout"
    @property
    def description(self) -> str: return "Click logout/sign-out on current page."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().logout(browser=parameters.get("browser"), player=player)


class BrowserAuthFillSignupForm(Action):
    @property
    def name(self) -> str: return "browser_auth_fill_signup_form"
    @property
    def description(self) -> str: return "Fill a registration/signup form."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"email": {"type": "STRING"}, "password": {"type": "STRING"}}, "required": ["email", "password"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().fill_signup(parameters["email"], parameters["password"], browser=parameters.get("browser"), player=player)


class BrowserAuthDetect2fa(Action):
    @property
    def name(self) -> str: return "browser_auth_detect_2fa"
    @property
    def description(self) -> str: return "Detect if 2FA/MFA is requested."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().detect_2fa(browser=parameters.get("browser"), player=player)


class BrowserAuthFillOtp(Action):
    @property
    def name(self) -> str: return "browser_auth_fill_otp"
    @property
    def description(self) -> str: return "Fill a one-time password field."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"code": {"type": "STRING"}}, "required": ["code"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().fill_otp(parameters["code"], browser=parameters.get("browser"), player=player)


class BrowserAuthAcceptTerms(Action):
    @property
    def name(self) -> str: return "browser_auth_accept_terms"
    @property
    def description(self) -> str: return "Accept terms and conditions checkbox."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().accept_terms(browser=parameters.get("browser"), player=player)


class BrowserAuthSaveSession(Action):
    @property
    def name(self) -> str: return "browser_auth_save_session"
    @property
    def description(self) -> str: return "Save current session/cookies to file."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"path": {"type": "STRING"}}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().save_session(parameters["path"], browser=parameters.get("browser"), player=player)


class BrowserAuthLoadSession(Action):
    @property
    def name(self) -> str: return "browser_auth_load_session"
    @property
    def description(self) -> str: return "Load session/cookies from file."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"path": {"type": "STRING"}}, "required": ["path"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().load_session(parameters["path"], browser=parameters.get("browser"), player=player)


class BrowserAuthClearCookies(Action):
    @property
    def name(self) -> str: return "browser_auth_clear_cookies"
    @property
    def description(self) -> str: return "Clear all cookies."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().clear_cookies(browser=parameters.get("browser"), player=player)


class BrowserAuthClearCache(Action):
    @property
    def name(self) -> str: return "browser_auth_clear_cache"
    @property
    def description(self) -> str: return "Clear browser cache."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {}, "required": []}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().clear_cache(browser=parameters.get("browser"), player=player)


class BrowserAuthSetUserAgent(Action):
    @property
    def name(self) -> str: return "browser_auth_set_user_agent"
    @property
    def description(self) -> str: return "Set a custom user agent string."
    @property
    def parameters_schema(self) -> dict:
        return {"type": "OBJECT", "properties": {"user_agent": {"type": "STRING"}}, "required": ["user_agent"]}
    def execute(self, parameters: dict, player=None, speak=None, **kw) -> Any:
        from runtime.browser.engine import BrowserEngine
        return BrowserEngine().set_ua(parameters["user_agent"], browser=parameters.get("browser"), player=player)


for _cls in [BrowserAuthLogout, BrowserAuthFillSignupForm, BrowserAuthDetect2fa, BrowserAuthFillOtp, BrowserAuthAcceptTerms, BrowserAuthSaveSession, BrowserAuthLoadSession, BrowserAuthClearCookies, BrowserAuthClearCache, BrowserAuthSetUserAgent]:
    ActionRegistry.register(_cls)
