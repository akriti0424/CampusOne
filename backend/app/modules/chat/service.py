import re
from fastapi import HTTPException
from sqlalchemy import func, or_
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.modules.auth.model import User
from app.modules.product.model import Product
from app.modules.chat.model import ChatMessage
from app.modules.chat.schema import ChatMessageCreate, ChatMessageRead


def create_room_message(db: Session, current_user: User, room_name: str, message_text: str, is_system: bool = False) -> ChatMessage:
    room_name = authorize_room(db, current_user, room_name)
    if not message_text.strip() or len(message_text.strip()) > 1000:
        raise HTTPException(422, "Messages must contain 1 to 1000 characters")
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


def authorize_room(db: Session, user: User, room_name: str) -> str:
    room = room_name.strip().lower()
    if room.startswith("product-"):
        match = re.fullmatch(r"product-([1-9][0-9]*)-buyer-([1-9][0-9]*)", room)
        if not match:
            raise HTTPException(400, "Invalid product conversation")
        product_id, buyer_id = map(int, match.groups())
        product = db.get(Product, product_id)
        if not product or not db.get(User, buyer_id):
            raise HTTPException(404, "Product or buyer not found")
        if buyer_id == product.seller_id or user.id not in (buyer_id, product.seller_id):
            raise HTTPException(403, "This product conversation is private")
    if room.startswith("dm-"):
        match = re.fullmatch(r"dm-([1-9][0-9]*)-([1-9][0-9]*)", room)
        if not match:
            raise HTTPException(400, "Invalid private conversation")
        first, second = map(int, match.groups())
        if first >= second or user.id not in (first, second):
            raise HTTPException(403, "This conversation is private")
        if db.query(User).filter(User.id.in_([first, second])).count() != 2:
            raise HTTPException(404, "Conversation participant not found")
    return room


def list_direct_conversations(db: Session, user: User):
    latest = (db.query(func.max(ChatMessage.id).label("id"))
        .filter(or_(ChatMessage.room_name.like(f"dm-{user.id}-%"),
                    ChatMessage.room_name.like(f"dm-%-{user.id}")))
        .group_by(ChatMessage.room_name).subquery())
    messages = (db.query(ChatMessage).join(latest, ChatMessage.id == latest.c.id)
                .order_by(ChatMessage.id.desc()).all())
    result = []
    for message in messages:
        match = re.fullmatch(r"dm-([1-9][0-9]*)-([1-9][0-9]*)", message.room_name)
        if not match:
            continue
        ids = list(map(int, match.groups()))
        if ids[0] >= ids[1] or user.id not in ids:
            continue
        other = db.get(User, ids[1] if ids[0] == user.id else ids[0])
        if other:
            result.append(dict(room_name=message.room_name, other_user_name=other.full_name,
                               last_message=message.message, created_at=message.created_at))
    return result


def list_product_conversations(db: Session, user: User, product_id: int):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    query = db.query(func.max(ChatMessage.id).label("id"))
    if user.id == product.seller_id:
        query = query.filter(ChatMessage.room_name.like(f"product-{product_id}-buyer-%"))
    else:
        query = query.filter(ChatMessage.room_name == f"product-{product_id}-buyer-{user.id}")
    latest = query.group_by(ChatMessage.room_name).subquery()
    messages = db.query(ChatMessage).join(latest, ChatMessage.id == latest.c.id).order_by(ChatMessage.id.desc()).all()
    result = []
    for message in messages:
        match = re.fullmatch(r"product-([1-9][0-9]*)-buyer-([1-9][0-9]*)", message.room_name)
        if not match:
            continue
        buyer_id = int(match[2])
        other = db.get(User, buyer_id if user.id == product.seller_id else product.seller_id)
        if other:
            result.append(dict(room_name=message.room_name, other_user_name=other.full_name,
                               last_message=message.message, created_at=message.created_at))
    return result
