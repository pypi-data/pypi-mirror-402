"""Tests for the REST API."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from farm.api.app import create_app


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    """Create a test client with temporary storage."""
    app = create_app(tmp_path)
    return TestClient(app)


def test_health_check(client: TestClient) -> None:
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_create_memory(client: TestClient) -> None:
    """Test creating a memory via API."""
    response = client.post(
        "/api/v1/memories",
        json={"content": "Test memory", "tags": ["test"]},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "Test memory"
    assert data["tags"] == ["test"]
    assert "id" in data


def test_get_memory(client: TestClient) -> None:
    """Test getting a memory by ID."""
    create_response = client.post(
        "/api/v1/memories",
        json={"content": "Test memory"},
    )
    memory_id = create_response.json()["id"]

    response = client.get(f"/api/v1/memories/{memory_id}")
    assert response.status_code == 200
    assert response.json()["id"] == memory_id


def test_get_nonexistent_memory(client: TestClient) -> None:
    """Test getting a nonexistent memory."""
    response = client.get("/api/v1/memories/nonexistent-id")
    assert response.status_code == 404


def test_list_memories(client: TestClient) -> None:
    """Test listing memories."""
    client.post("/api/v1/memories", json={"content": "Memory 1"})
    client.post("/api/v1/memories", json={"content": "Memory 2"})

    response = client.get("/api/v1/memories")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_update_memory(client: TestClient) -> None:
    """Test updating a memory."""
    create_response = client.post(
        "/api/v1/memories",
        json={"content": "Original"},
    )
    memory_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/memories/{memory_id}",
        json={"content": "Updated"},
    )
    assert response.status_code == 200
    assert response.json()["content"] == "Updated"


def test_delete_memory(client: TestClient) -> None:
    """Test deleting a memory."""
    create_response = client.post(
        "/api/v1/memories",
        json={"content": "To delete"},
    )
    memory_id = create_response.json()["id"]

    response = client.delete(f"/api/v1/memories/{memory_id}")
    assert response.status_code == 204

    get_response = client.get(f"/api/v1/memories/{memory_id}")
    assert get_response.status_code == 404


def test_search_memories(client: TestClient) -> None:
    """Test searching memories."""
    client.post("/api/v1/memories", json={"content": "Python programming"})
    client.post("/api/v1/memories", json={"content": "JavaScript tutorial"})

    response = client.post(
        "/api/v1/memories/search",
        json={"query": "programming", "limit": 10},
    )
    assert response.status_code == 200
    results = response.json()
    assert len(results) > 0


def test_file_operations(client: TestClient) -> None:
    """Test file CRUD operations."""
    write_response = client.put(
        "/api/v1/files/test/file.txt",
        params={"content": "File content"},
    )
    assert write_response.status_code == 200

    list_response = client.get("/api/v1/files")
    assert list_response.status_code == 200

    content_response = client.get("/api/v1/files/test/file.txt/content")
    assert content_response.status_code == 200
    assert content_response.json()["content"] == "File content"

    delete_response = client.delete("/api/v1/files/test/file.txt")
    assert delete_response.status_code == 204
