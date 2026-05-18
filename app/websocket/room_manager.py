from typing import Dict, Any
from fastapi import WebSocket


class RoomManager:

    def __init__(self):
        self._rooms: Dict[str, Dict[str, WebSocket]] = {}

    async def connect(self, room_id: str, username: str, websocket: WebSocket) -> None:
        await websocket.accept()

        if room_id not in self._rooms:
            self._rooms[room_id] = {}

        self._rooms[room_id][username] = websocket

        await self.broadcast(
            room_id,
            {
                "type": "system",
                "message": f"{username} подключился к комнате",
                "username": username
            }
        )

    async def disconnect(self, room_id: str, username: str, websocket: WebSocket) -> None:

        if room_id in self._rooms:

            if username in self._rooms[room_id]:
                del self._rooms[room_id][username]

                await self.broadcast(
                    room_id,
                    {
                        "type": "system",
                        "message": f"{username} покинул комнату",
                        "username": username
                    }
                )

            if not self._rooms[room_id]:
                del self._rooms[room_id]

    async def broadcast(self, room_id: str, payload: dict) -> None:
        if room_id in self._rooms:
            for username, connection in self._rooms[room_id].items():
                try:
                    await connection.send_json(payload)
                except Exception:
                    pass

    async def send_to_user(self, room_id: str, username: str, payload: dict) -> None:
        if room_id in self._rooms and username in self._rooms[room_id]:
            try:
                await self._rooms[room_id][username].send_json(payload)
            except Exception:
                pass

    def get_users(self, room_id: str) -> list:
        if room_id in self._rooms:
            return list(self._rooms[room_id].keys())
        return []


room_manager = RoomManager()