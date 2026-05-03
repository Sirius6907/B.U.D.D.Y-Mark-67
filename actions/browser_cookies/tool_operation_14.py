from core.tools.registry import register_tool
from pydantic import BaseModel, Field


class BrowserCookiesOperation14Input(BaseModel):
    params: dict = Field(default_factory=dict, description="Parameters for browser_cookies operation")


@register_tool(
    name="browser_cookies_operation_14",
    description="Browser automation tool for browser_cookies - operation_14",
    domain="browser_cookies",
)
def browser_cookies_operation_14(params: BrowserCookiesOperation14Input) -> str:
    """
    Execute browser_cookies operation.
    """
    return f"Successfully executed browser_cookies_operation_14"
