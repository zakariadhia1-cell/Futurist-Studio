from sqlalchemy import Boolean, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import UUIDPrimaryKeyMixin


class ModelConfig(UUIDPrimaryKeyMixin, Base):
    """A selectable (provider, model) pair. Model IDs are configuration, never hard-coded."""

    __tablename__ = "model_configs"

    provider: Mapped[str] = mapped_column(String(32), nullable=False)  # 'openai' | 'anthropic' | 'ollama'
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    capabilities: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cost_per_1k_input: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    cost_per_1k_output: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
