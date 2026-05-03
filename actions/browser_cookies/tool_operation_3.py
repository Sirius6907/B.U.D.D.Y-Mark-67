from core.tools.registry import register_tool
from pydantic import BaseModel, Field


class BrowserCookiesOperation3Input(BaseModel):
    params: dict = Field(default_factory=dict, description="Parameters for browser_cookies operation")


@register_tool(
    name="browser_cookies_operation_3",
    description="Browser automation tool for browser_cookies - operation_3",
    domain="browser_cookies",
)
def browser_cookies_operation_3(params: BrowserCookiesOperation3Input) -> str:
    """
    Execute browser_cookies operation.
    """
    return f"Successfully executed browser_cookies_operation_3"
