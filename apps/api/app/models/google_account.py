import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class GoogleAccount(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One connected Google account per user (Calendar + Gmail scopes). Tokens are
    Fernet-encrypted at rest via app/core/crypto.py, same as MCP server env vars."""

    __tablename__ = "google_accounts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )
    google_email: Mapped[str] = mapped_column(String(255), nullable=False)
    access_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    token_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scopes: Mapped[str] = mapped_column(Text, nullable=False, default="")
