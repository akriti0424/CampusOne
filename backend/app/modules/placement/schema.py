from __future__ import annotations

from pydantic import BaseModel, Field


class QuestionProgressUpdate(BaseModel):
    status: str = Field(pattern="^(solved|needs_revision|unsolved)$")
    bookmarked: bool | None = None


class AnswerSubmission(BaseModel):
    answer: str = Field(min_length=1)


class AttemptAnswerSubmission(BaseModel):
    question_id: int
    answer: str = Field(min_length=1)
    time_spent_seconds: int = Field(default=0, ge=0)


class TestGenerationRequest(BaseModel):
    company: str = "Campus Practice"
    duration_minutes: int = Field(default=60, ge=15, le=180)
    questions_per_pillar: int = Field(default=2, ge=1, le=10)
    negative_marking: bool = False
    section_switching: bool = True

