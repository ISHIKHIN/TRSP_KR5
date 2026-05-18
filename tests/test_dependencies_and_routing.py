import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.storage import get_storage


@pytest.fixture
def client():
    storage = get_storage()
    storage.clear()
    return TestClient(app)


def test_users_me_returns_current_user(client):
    response = client.get("/users/me", headers={"X-User-Id": "10", "X-User-Role": "user"})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 10
    assert data["role"] == "user"


def test_no_x_user_id_returns_401(client):
    response = client.get("/users/me")
    assert response.status_code == 401


def test_regular_user_cannot_access_admin_stats(client):
    response = client.get("/admin/stats", headers={"X-User-Id": "10", "X-User-Role": "user"})
    assert response.status_code == 403


def test_admin_can_access_stats(client):
    client.post("/tasks/", json={"title": "Task 1", "status": "todo", "priority": 3},
                headers={"X-User-Id": "10"})
    client.post("/tasks/", json={"title": "Task 2", "status": "done", "priority": 4},
                headers={"X-User-Id": "20"})

    response = client.get("/admin/stats", headers={"X-User-Id": "1", "X-User-Role": "admin"})
    assert response.status_code == 200
    data = response.json()
    assert data["total_tasks"] == 2
    assert "todo" in data["by_status"]
    assert "done" in data["by_status"]


def test_regular_user_cannot_delete_foreign_task(client):
    create_resp = client.post("/tasks/", json={"title": "Task", "status": "todo", "priority": 3},
                              headers={"X-User-Id": "10"})
    task_id = create_resp.json()["id"]

    response = client.delete(f"/tasks/{task_id}", headers={"X-User-Id": "20", "X-User-Role": "user"})
    assert response.status_code == 404


def test_admin_can_delete_any_task(client):
    create_resp = client.post("/tasks/", json={"title": "Task", "status": "todo", "priority": 3},
                              headers={"X-User-Id": "10"})
    task_id = create_resp.json()["id"]

    response = client.delete(f"/admin/tasks/{task_id}",
                             headers={"X-User-Id": "1", "X-User-Role": "admin"})
    assert response.status_code == 204

    get_resp = client.get(f"/tasks/{task_id}", headers={"X-User-Id": "10"})
    assert get_resp.status_code == 404