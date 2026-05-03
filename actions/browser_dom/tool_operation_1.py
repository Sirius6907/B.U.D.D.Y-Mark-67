from core.tools.registry import register_tool
from pydantic import BaseModel, Field


class BrowserDomOperation1Input(BaseModel):
    params: dict = Field(default_factory=dict, description="Parameters for browser_dom operation")


@register_tool(
    name="browser_dom_operation_1",
    description="Browser automation tool for browser_dom - operation_1",
    domain="browser_dom",
)
def browser_dom_operation_1(params: BrowserDomOperation1Input) -> str:
    """
    Execute browser_dom operation.
    """
    return f"Successfully executed browser_dom_operation_1"
