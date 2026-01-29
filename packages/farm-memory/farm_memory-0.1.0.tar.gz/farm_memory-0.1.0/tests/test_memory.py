"""Tests for memory management."""

from pathlib import Path

import pytest

from farm.core.memory import MemoryManager
from farm.core.storage import JsonStorage
from farm.models.schemas import MemoryCreate, MemoryUpdate


@pytest.fixture
def storage(tmp_path: Path) -> JsonStorage:
    """Create a temporary storage."""
    return JsonStorage(tmp_path)


@pytest.fixture
def memory_manager(storage: JsonStorage) -> MemoryManager:
    """Create a memory manager with temporary storage."""
    return MemoryManager(storage)


async def test_create_memory(memory_manager: MemoryManager) -> None:
    """Test creating a memory."""
    data = MemoryCreate(content="Test memory", tags=["test"])
    memory = await memory_manager.create(data)

    assert memory.id is not None
    assert memory.content == "Test memory"
    assert memory.tags == ["test"]
    assert memory.created_at is not None


async def test_get_memory(memory_manager: MemoryManager) -> None:
    """Test getting a memory by ID."""
    data = MemoryCreate(content="Test memory")
    created = await memory_manager.create(data)

    memory = await memory_manager.get(created.id)
    assert memory is not None
    assert memory.id == created.id
    assert memory.content == "Test memory"


async def test_get_nonexistent_memory(memory_manager: MemoryManager) -> None:
    """Test getting a nonexistent memory."""
    memory = await memory_manager.get("nonexistent-id")
    assert memory is None


async def test_update_memory(memory_manager: MemoryManager) -> None:
    """Test updating a memory."""
    data = MemoryCreate(content="Original content")
    memory = await memory_manager.create(data)

    update_data = MemoryUpdate(content="Updated content", tags=["updated"])
    updated = await memory_manager.update(memory.id, update_data)

    assert updated is not None
    assert updated.content == "Updated content"
    assert updated.tags == ["updated"]
    assert updated.updated_at > memory.created_at


async def test_delete_memory(memory_manager: MemoryManager) -> None:
    """Test deleting a memory."""
    data = MemoryCreate(content="To delete")
    memory = await memory_manager.create(data)

    result = await memory_manager.delete(memory.id)
    assert result is True

    deleted = await memory_manager.get(memory.id)
    assert deleted is None


async def test_list_memories(memory_manager: MemoryManager) -> None:
    """Test listing all memories."""
    await memory_manager.create(MemoryCreate(content="Memory 1", tags=["a"]))
    await memory_manager.create(MemoryCreate(content="Memory 2", tags=["b"]))
    await memory_manager.create(MemoryCreate(content="Memory 3", tags=["a", "b"]))

    all_memories = await memory_manager.list_all()
    assert len(all_memories) == 3

    tag_a = await memory_manager.list_all(tags=["a"])
    assert len(tag_a) == 2

    tag_b = await memory_manager.list_all(tags=["b"])
    assert len(tag_b) == 2


async def test_search_by_content(memory_manager: MemoryManager) -> None:
    """Test text search in memory content."""
    await memory_manager.create(MemoryCreate(content="Python programming"))
    await memory_manager.create(MemoryCreate(content="JavaScript tutorial"))
    await memory_manager.create(MemoryCreate(content="Python web framework"))

    results = await memory_manager.search_by_content("python")
    assert len(results) == 2
    assert all("python" in r.content.lower() for r in results)
