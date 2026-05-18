import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.storage import get_storage
from app.dependencies import get_storage as dep_get_storage


@pytest.fixture
def client():
    storage = get_storage()
    storage.clear()
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {"X-User-Id": "10"}


def test_create_task_success(client, auth_headers):
    response = client.post(
        "/tasks/",
        json={
            "title": "Test Task",
            "description": "Test Description",
            "status": "todo",
            "priority": 3
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["owner_id"] == 10
    assert "id" in data


def test_create_task_invalid_title(client, auth_headers):
    response = client.post(
        "/tasks/",
        json={
            "title": "ab",
            "description": "Test",
            "status": "todo",
            "priority": 3
        },
        headers=auth_headers
    )
    assert response.status_code == 422


def test_create_task_no_auth(client):
    response = client.post(
        "/tasks/",
        json={
            "title": "Test Task",
            "description": "Test",
            "status": "todo",
            "priority": 3
        }
    )
    assert response.status_code == 401


def test_user_sees_only_own_tasks(client):
    client.post("/tasks/", json={"title": "Task 1", "status": "todo", "priority": 3},
                headers={"X-User-Id": "10"})
    client.post("/tasks/", json={"title": "Task 2", "status": "todo", "priority": 4},
                headers={"X-User-Id": "10"})

    client.post("/tasks/", json={"title": "Task 3", "status": "todo", "priority": 3},
                headers={"X-User-Id": "20"})

    response = client.get("/tasks/", headers={"X-User-Id": "10"})
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 2
    assert all(t["owner_id"] == 10 for t in tasks)


def test_filter_tasks(client):
    client.post("/tasks/", json={"title": "Task 1", "status": "todo", "priority": 2},
                headers={"X-User-Id": "10"})
    client.post("/tasks/", json={"title": "Task 2", "status": "in_progress", "priority": 4},
                headers={"X-User-Id": "10"})
    client.post("/tasks/", json={"title": "Task 3", "status": "done", "priority": 5},
                headers={"X-User-Id": "10"})

    response = client.get("/tasks/?status=in_progress&min_priority=3",
                          headers={"X-User-Id": "10"})
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 1
    assert tasks[0]["status"] == "in_progress"


def test_update_task_status_success(client):
    create_resp = client.post("/tasks/", json={"title": "Task", "status": "todo", "priority": 3},
                              headers={"X-User-Id": "10"})
    task_id = create_resp.json()["id"]

    response = client.patch(f"/tasks/{task_id}/status", json={"status": "done"},
                            headers={"X-User-Id": "10"})
    assert response.status_code == 200
    assert response.json()["status"] == "done"


def test_access_foreign_task_404(client):
    create_resp = client.post("/tasks/", json={"title": "Task", "status": "todo", "priority": 3},
                              headers={"X-User-Id": "10"})
    task_id = create_resp.json()["id"]

    response = client.get(f"/tasks/{task_id}", headers={"X-User-Id": "20"})
    assert response.status_code == 404


def test_delete_task_success(client):
    create_resp = client.post("/tasks/", json={"title": "Task", "status": "todo", "priority": 3},
                              headers={"X-User-Id": "10"})
    task_id = create_resp.json()["id"]

    response = client.delete(f"/tasks/{task_id}", headers={"X-User-Id": "10"})
    assert response.status_code == 204

    get_resp = client.get(f"/tasks/{task_id}", headers={"X-User-Id": "10"})
    assert get_resp.status_code == 404


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}