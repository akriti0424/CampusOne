from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class LostFoundItem(Base):
    __tablename__ = "lost_found_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(140), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(400), nullable=True)
    location: Mapped[str] = mapped_column(String(140), nullable=False)
    kind: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    similarity_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    verification_code_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    verification_code_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    desk_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    owner = relationship("User", back_populates="lost_items")
    matches = relationship(
        "LostFoundMatch",
        back_populates="source_item",
        cascade="all, delete-orphan",
        foreign_keys="LostFoundMatch.source_item_id",
    )


class LostFoundMatch(Base):
    __tablename__ = "lost_found_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_item_id: Mapped[int] = mapped_column(ForeignKey("lost_found_items.id"), nullable=False)
    candidate_item_id: Mapped[int] = mapped_column(ForeignKey("lost_found_items.id"), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="suggested", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    source_item = relationship("LostFoundItem", foreign_keys=[source_item_id], back_populates="matches")
