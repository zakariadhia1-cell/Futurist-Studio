import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class McpServer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A user-configured MCP server. This *is* FUTURIST OS's plugin system: rather than a
    separate Python-plugin-loader mechanism alongside this, third-party capabilities are
    added by pointing an agent at an MCP server (stdio subprocess or SSE endpoint) - the
    same integration point any other MCP client (e.g. Claude Desktop) uses. See
    app/mcp/client.py and app/orchestrator/tools/mcp_tools.py."""

    __tablename__ = "mcp_servers"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    transport: Mapped[str] = mapped_column(String(8), nullable=False)  # stdio|sse
    command: Mapped[str | None] = mapped_column(String(255), nullable=True)  # stdio
    args: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)  # stdio
    env: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)  # stdio
    url: Mapped[str | None] = mapped_column(String(512), nullable=True)  # sse
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
