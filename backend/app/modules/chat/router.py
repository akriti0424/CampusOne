from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.dependencies import get_current_user
from app.db.session import get_db
from app.modules.auth.model import User
from app.modules.chat.realtime import manager
from app.modules.chat.schema import ChatEvent, ChatMessageCreate, ChatMessageRead, ConversationRead
from app.modules.chat.service import list_product_conversations, authorize_room, build_history_payload, build_message_payload, create_message, create_room_message, list_direct_conversations, list_messages, serialize_message


router = APIRouter(prefix="/api/chat", tags=["chat"])



@router.get("/conversations", response_model=list[ConversationRead])
def conversations(product_id: int | None = Query(default=None, ge=1), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if product_id is not None:
        return list_product_conversations(db, current_user, product_id)
    return list_direct_conversations(db, current_user)


@router.get("/{room_name}", response_model=list[ChatMessageRead])
def read_room(room_name: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    room_name = authorize_room(db, current_user, room_name)
    return list_messages(db, room_name)


@router.post("", response_model=ChatMessageRead)
async def send_message(payload: ChatMessageCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    message = create_message(db, current_user, payload)
    await manager.send_to_room(message.room_name, build_message_payload(message))
    return message


def _get_user_from_token(db: Session, token: str) -> User:
    try:
        payload = decode_token(token)
        subject = payload.get("sub")
        if not subject:
            raise ValueError("Missing subject")
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials") from error

    user = db.query(User).filter(User.id == int(subject)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


@router.websocket("/ws/{room_name}")
async def websocket_room(
    room_name: str,
    websocket: WebSocket,
    token: str = Query(default=""),
    db: Session = Depends(get_db),
):
    if not token:
        await websocket.close(code=1008)
        return

    try:
        user = _get_user_from_token(db, token)
        room_name = authorize_room(db, user, room_name)
        await manager.connect(room_name, websocket)

        history = list_messages(db, room_name)
        await websocket.send_json(build_history_payload(history))

        while True:
            data = await websocket.receive_json()
            message_text = str(data.get("message", "")).strip()
            if not message_text:
                continue

            message = create_room_message(db, user, room_name, message_text)
            await manager.send_to_room(room_name, build_message_payload(message))
    except WebSocketDisconnect:
        manager.disconnect(room_name, websocket)
    except HTTPException:
        await websocket.close(code=1008)

    finally:
        manager.disconnect(room_name, websocket)
