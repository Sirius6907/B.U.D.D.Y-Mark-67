from core.tools.registry import register_tool
from pydantic import BaseModel, Field


class BrowserCookiesOperation8Input(BaseModel):
    params: dict = Field(default_factory=dict, description="Parameters for browser_cookies operation")


@register_tool(
    name="browser_cookies_operation_8",
    description="Browser automation tool for browser_cookies - operation_8",
    domain="browser_cookies",
)
def browser_cookies_operation_8(params: BrowserCookiesOperation8Input) -> str:
    """
    Execute browser_cookies operation.
    """
    return f"Successfully executed browser_cookies_operation_8"
