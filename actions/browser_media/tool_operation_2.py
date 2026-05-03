from core.tools.registry import register_tool
from pydantic import BaseModel, Field


class BrowserMediaOperation2Input(BaseModel):
    params: dict = Field(default_factory=dict, description="Parameters for browser_media operation")


@register_tool(
    name="browser_media_operation_2",
    description="Browser automation tool for browser_media - operation_2",
    domain="browser_media",
)
def browser_media_operation_2(params: BrowserMediaOperation2Input) -> str:
    """
    Execute browser_media operation.
    """
    return f"Successfully executed browser_media_operation_2"
