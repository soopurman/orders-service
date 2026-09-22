import os
import uuid

import httpx


BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")


def test_crud_lifecycle_against_running_service():
    """Exercise health, every CRUD path, validation conflict, and the final 404."""
    name = f"test-{uuid.uuid4().hex}"
    with httpx.Client(base_url=BASE_URL, timeout=10) as client:
        index = client.get("/")
        assert index.status_code == 200
        assert index.json()["routes"]["items"].endswith("/items")

        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        created = client.post("/items", json={"name": name, "description": "before"})
        assert created.status_code == 201
        item_id = created.json()["id"]

        assert client.post("/items", json={"name": name, "description": "duplicate"}).status_code == 409
        assert client.get(f"/items/{item_id}").json()["description"] == "before"

        changed = client.put(f"/items/{item_id}", json={"name": name, "description": "after"})
        assert changed.status_code == 200
        assert changed.json()["description"] == "after"
        assert any(item["id"] == item_id for item in client.get("/items").json())

        assert client.delete(f"/items/{item_id}").status_code == 204
        assert client.get(f"/items/{item_id}").status_code == 404
