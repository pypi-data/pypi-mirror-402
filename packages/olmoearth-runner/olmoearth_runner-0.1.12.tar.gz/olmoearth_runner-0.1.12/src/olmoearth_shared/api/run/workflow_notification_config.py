from pydantic import BaseModel, Field


class WorkflowNotificationConfig(BaseModel):
    """Per-Workflow configuration for emitting notifications"""

    url: str | None = Field(description="The URL to send the callback to.")
    headers: dict[str, str] | None = Field(default=None, description="The HTTP headers to use.")
