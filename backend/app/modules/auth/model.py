from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    scholar_id: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    branch: Mapped[str] = mapped_column(String(80), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_otp_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email_otp_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    role: Mapped[str] = mapped_column(String(30), default="student", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    products = relationship("Product", back_populates="seller", cascade="all, delete-orphan")
    lost_items = relationship("LostFoundItem", back_populates="owner", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="author", cascade="all, delete-orphan")


class PendingRegistration(Base):
    __tablename__ = "pending_registrations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    scholar_id: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    branch: Mapped[str] = mapped_column(String(80), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email_otp_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email_otp_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
