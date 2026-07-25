from pydantic import BaseModel, Field
from datetime import datetime


class LostFoundCreate(BaseModel):
    title: str = Field(min_length=2, max_length=140)
    description: str = Field(min_length=10, max_length=4000)
    image_url: str | None = None
    location: str = Field(min_length=2, max_length=140)
    kind: str = Field(pattern="^(lost|found)$")


class LostFoundRead(BaseModel):
    id: int
    title: str
    description: str
    image_url: str | None
    location: str
    kind: str
    status: str
    similarity_score: float
    verified_at: datetime | None = None
    resolved_at: datetime | None = None
    closed_at: datetime | None = None
    desk_notes: str | None = None

    model_config = {"from_attributes": True}


class MatchRead(BaseModel):
    id: int
    source_item_id: int
    candidate_item_id: int
    score: float
    status: str

    model_config = {"from_attributes": True}


class VerificationRequestRead(BaseModel):
    item_id: int
    status: str
    verification_code: str


class VerificationSubmit(BaseModel):
    verification_code: str = Field(min_length=4, max_length=16)
    desk_notes: str | None = None


class StatusChange(BaseModel):
    status: str = Field(pattern="^(open|matched|verified|resolved|closed)$")
