from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.modules.auth.model import User
from app.modules.chat.model import ChatMessage
from app.modules.chat.schema import ChatMessageCreate, ChatMessageRead


def create_room_message(db: Session, current_user: User, room_name: str, message_text: str, is_system: bool = False) -> ChatMessage:
    message = ChatMessage(
        room_name=room_name.strip().lower(),
        display_name=f"{current_user.full_name.split()[0]} ({current_user.branch})",
        message=message_text.strip(),
        is_system=is_system,
        author_id=current_user.id,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def create_message(db: Session, current_user: User, payload: ChatMessageCreate) -> ChatMessage:
    return create_room_message(db, current_user, payload.room_name, payload.message)


def list_messages(db: Session, room_name: str) -> list[ChatMessage]:
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.room_name == room_name.strip().lower())
        .order_by(ChatMessage.created_at.asc())
        .all()
    )


def serialize_message(message: ChatMessage) -> ChatMessageRead:
    return ChatMessageRead.model_validate(message)


def build_history_payload(messages: list[ChatMessage]) -> dict[str, object]:
    return {
        "type": "history",
        "messages": [serialize_message(message).model_dump(mode="json") for message in messages],
    }


def build_message_payload(message: ChatMessage) -> dict[str, object]:
    return {
        "type": "message",
        "message": serialize_message(message).model_dump(mode="json"),
    }
