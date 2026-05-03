from core.tools.registry import register_tool
from pydantic import BaseModel, Field


class BrowserNavOperation1Input(BaseModel):
    params: dict = Field(default_factory=dict, description="Parameters for browser_nav operation")


@register_tool(
    name="browser_nav_operation_1",
    description="Browser automation tool for browser_nav - operation_1",
    domain="browser_nav",
)
def browser_nav_operation_1(params: BrowserNavOperation1Input) -> str:
    """
    Execute browser_nav operation.
    """
    return f"Successfully executed browser_nav_operation_1"
