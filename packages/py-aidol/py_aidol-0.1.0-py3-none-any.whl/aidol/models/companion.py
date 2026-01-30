"""
Companion database model

Uses aioia_core.models.BaseModel which provides:
- id: Mapped[str] (primary key, UUID default)
- created_at: Mapped[datetime]
- updated_at: Mapped[datetime]
"""

from aioia_core.models import BaseModel
from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column


class DBCompanion(BaseModel):
    """Companion (member) database model"""

    __tablename__ = "companions"

    # id, created_at, updated_at inherited from BaseModel
    aidol_id: Mapped[str | None] = mapped_column(ForeignKey("aidols.id"), nullable=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    biography: Mapped[str | None] = mapped_column(Text, nullable=True)
    profile_picture_url: Mapped[str | None] = mapped_column(String, nullable=True)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (Index("ix_companions_aidol_id", "aidol_id"),)
