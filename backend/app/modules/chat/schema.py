from __future__ import annotations

from pydantic import BaseModel, Field
from datetime import datetime


class ChatMessageCreate(BaseModel):
    room_name: str = Field(min_length=2, max_length=80)
    message: str = Field(min_length=1, max_length=1000)


class ChatMessageRead(BaseModel):
    id: int
    room_name: str
    display_name: str
    message: str
    is_system: bool
    author_id: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatEvent(BaseModel):
    type: str
    message: ChatMessageRead | None = None
    messages: list[ChatMessageRead] | None = None
