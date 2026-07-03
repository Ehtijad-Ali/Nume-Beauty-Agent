"""Competitor model — tracked competitors."""

from __future__ import annotations

from sqlalchemy import Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDPKMixin


class Competitor(Base, UUIDPKMixin, TimestampMixin):
    """A tracked competitor."""

    __tablename__ = "competitors"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    logo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    share_of_voice: Mapped[float] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    traffic: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    keywords_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ads_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Competitor {self.name}>"
