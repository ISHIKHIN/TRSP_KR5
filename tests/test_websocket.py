import pytest
from fastapi.testclient import TestClient
from app.main import app
import json


@pytest.fixture
def client():
    return TestClient(app)


def test_websocket_connect(client):
    with client.websocket_connect("/ws/rooms/test?username=alice") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "system"
        assert "alice" in data["message"]


def test_websocket_invalid_username(client):
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/rooms/test?username="):
            pass


def test_websocket_send_message(client):
    with client.websocket_connect("/ws/rooms/test?username=alice") as websocket:
        websocket.receive_json()

        websocket.send_json({"type": "message", "text": "Hello World"})
        response = websocket.receive_json()
        assert response["type"] == "message"
        assert response["text"] == "Hello World"
        assert response["username"] == "alice"


def test_two_clients_same_room(client):
    with client.websocket_connect("/ws/rooms/test?username=alice") as ws1, \
            client.websocket_connect("/ws/rooms/test?username=bob") as ws2:

        ws1.receive_json()
        ws2.receive_json()

        ws1.send_json({"type": "message", "text": "Hello everyone"})


        def get_message(ws, expected_username=None):
            while True:
                msg = ws.receive_json()
                if msg["type"] == "message":
                    if expected_username is None or msg["username"] == expected_username:
                        return msg

        msg1 = get_message(ws1, "alice")
        msg2 = get_message(ws2, "alice")

        assert msg1["text"] == "Hello everyone"
        assert msg2["text"] == "Hello everyone"
        assert msg1["username"] == "alice"
        assert msg2["username"] == "alice"


def test_different_rooms(client):
    with client.websocket_connect("/ws/rooms/room1?username=alice") as ws1, \
            client.websocket_connect("/ws/rooms/room2?username=bob") as ws2:
        ws1.receive_json()
        ws2.receive_json()

        ws1.send_json({"type": "message", "text": "Message in room1"})

        msg1 = ws1.receive_json()
        assert msg1["text"] == "Message in room1"

        with pytest.raises(Exception):
            ws2.receive_json(timeout=1)


def test_message_too_long(client):
    with client.websocket_connect("/ws/rooms/test?username=alice") as websocket:
        websocket.receive_json()

        long_text = "x" * 301
        websocket.send_json({"type": "message", "text": long_text})
        response = websocket.receive_json()
        assert response["type"] == "error"
        assert "too long" in response["detail"].lower()


def test_room_users_endpoint(client):
    with client.websocket_connect("/ws/rooms/test?username=alice") as ws1, \
            client.websocket_connect("/ws/rooms/test?username=bob") as ws2:
        ws1.receive_json()
        ws2.receive_json()

        response = client.get("/rooms/test/users")
        assert response.status_code == 200
        data = response.json()
        assert set(data["users"]) == {"alice", "bob"}