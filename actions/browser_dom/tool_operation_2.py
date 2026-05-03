from core.tools.registry import register_tool
from pydantic import BaseModel, Field


class BrowserDomOperation2Input(BaseModel):
    params: dict = Field(default_factory=dict, description="Parameters for browser_dom operation")


@register_tool(
    name="browser_dom_operation_2",
    description="Browser automation tool for browser_dom - operation_2",
    domain="browser_dom",
)
def browser_dom_operation_2(params: BrowserDomOperation2Input) -> str:
    """
    Execute browser_dom operation.
    """
    return f"Successfully executed browser_dom_operation_2"
