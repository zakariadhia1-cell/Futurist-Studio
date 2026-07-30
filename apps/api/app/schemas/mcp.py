import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator


class McpServerCreate(BaseModel):
    name: str
    transport: str  # stdio|sse
    command: str | None = None
    args: list[str] = []
    env: dict[str, str] = {}
    url: str | None = None

    @model_validator(mode="after")
    def _check_transport_fields(self) -> "McpServerCreate":
        if self.transport not in ("stdio", "sse"):
            raise ValueError("transport muss 'stdio' oder 'sse' sein.")
        if self.transport == "stdio" and not self.command:
            raise ValueError("stdio-Server brauchen ein 'command'.")
        if self.transport == "sse" and not self.url:
            raise ValueError("sse-Server brauchen eine 'url'.")
        return self


class McpServerUpdate(BaseModel):
    name: str | None = None
    enabled: bool | None = None


class McpServerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    transport: str
    command: str | None
    args: list
    url: str | None
    enabled: bool
    created_at: datetime
    updated_at: datetime


class McpToolInfo(BaseModel):
    name: str
    description: str | None = None
