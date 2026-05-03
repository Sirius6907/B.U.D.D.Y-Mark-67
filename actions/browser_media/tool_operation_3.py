from core.tools.registry import register_tool
from pydantic import BaseModel, Field


class BrowserMediaOperation3Input(BaseModel):
    params: dict = Field(default_factory=dict, description="Parameters for browser_media operation")


@register_tool(
    name="browser_media_operation_3",
    description="Browser automation tool for browser_media - operation_3",
    domain="browser_media",
)
def browser_media_operation_3(params: BrowserMediaOperation3Input) -> str:
    """
    Execute browser_media operation.
    """
    return f"Successfully executed browser_media_operation_3"
