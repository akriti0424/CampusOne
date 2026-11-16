from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class PlacementQuestion(Base):
    __tablename__ = "placement_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pillar: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    topic: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    question_format: Mapped[str] = mapped_column(String(20), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    correct_answer: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    constraints: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sample_input: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sample_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hints: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    optimal_approach: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    time_complexity: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    space_complexity: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    difficulty: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    company_tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    is_top_question: Mapped[bool] = mapped_column(default=False, nullable=False)
    top_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_quiz_question: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class PlacementProgress(Base):
    __tablename__ = "placement_progress"
    __table_args__ = (UniqueConstraint("user_id", "question_id", name="uq_placement_progress_user_question"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey("placement_questions.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="unsolved", nullable=False)
    bookmarked: Mapped[bool] = mapped_column(default=False, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    correct_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class PlacementTest(Base):
    __tablename__ = "placement_tests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    company: Mapped[str] = mapped_column(String(80), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    negative_marking: Mapped[bool] = mapped_column(default=False, nullable=False)
    section_switching: Mapped[bool] = mapped_column(default=True, nullable=False)
    question_ids: Mapped[list[int]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class PlacementAttempt(Base):
    __tablename__ = "placement_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    test_id: Mapped[int] = mapped_column(ForeignKey("placement_tests.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="in_progress", nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    wrong_answers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    section_stats: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class PlacementAnswer(Base):
    __tablename__ = "placement_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("placement_attempts.id"), nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey("placement_questions.id"), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(default=False, nullable=False)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
