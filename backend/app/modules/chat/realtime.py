from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.rooms: dict[str, set[WebSocket]] = {}

    async def connect(self, room_name: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.rooms.setdefault(room_name, set()).add(websocket)

    def disconnect(self, room_name: str, websocket: WebSocket) -> None:
        room = self.rooms.get(room_name)
        if not room:
            return
        room.discard(websocket)
        if not room:
            self.rooms.pop(room_name, None)

    async def send_to_room(self, room_name: str, payload: dict[str, Any]) -> None:
        for websocket in list(self.rooms.get(room_name, set())):
            await websocket.send_json(payload)


manager = ConnectionManager()
