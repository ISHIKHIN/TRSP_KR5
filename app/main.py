from fastapi import FastAPI, WebSocket, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.routers import tasks, users, admin
from app.storage import get_storage
from app.websocket.room_manager import room_manager, RoomManager

app = FastAPI(title="Task Manager API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router)
app.include_router(users.router)
app.include_router(admin.router)


@app.websocket("/ws/rooms/{room_id}")
async def websocket_room(
    websocket: WebSocket,
    room_id: str,
    username: str = Query(...)
):
    if not username or not username.strip():
        await websocket.close(code=1008)
        return

    username = username.strip()

    try:
        await room_manager.connect(room_id, username, websocket)

        while True:
            data = await websocket.receive_json()

            if data.get("type") == "message":
                text = data.get("text", "")

                if len(text) > 300:
                    await room_manager.send_to_user(
                        room_id, username,
                        {"type": "error", "detail": "Message is too long"}
                    )
                else:
                    await room_manager.broadcast(
                        room_id,
                        {
                            "type": "message",
                            "room_id": room_id,
                            "username": username,
                            "text": text
                        }
                    )

    except Exception as e:
        await room_manager.disconnect(room_id, username, websocket)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/rooms/{room_id}/users")
async def get_room_users(room_id: str):
    users_list = room_manager.get_users(room_id)
    return {"room_id": room_id, "users": users_list}