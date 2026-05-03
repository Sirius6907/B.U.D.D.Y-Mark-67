from core.tools.registry import register_tool
from pydantic import BaseModel, Field


class BrowserDomOperation3Input(BaseModel):
    params: dict = Field(default_factory=dict, description="Parameters for browser_dom operation")


@register_tool(
    name="browser_dom_operation_3",
    description="Browser automation tool for browser_dom - operation_3",
    domain="browser_dom",
)
def browser_dom_operation_3(params: BrowserDomOperation3Input) -> str:
    """
    Execute browser_dom operation.
    """
    return f"Successfully executed browser_dom_operation_3"
