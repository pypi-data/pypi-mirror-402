"""Memory management for FARM."""

from datetime import datetime
from pathlib import Path

from farm.core.storage import JsonStorage
from farm.models.schemas import Memory, MemoryCreate, MemoryUpdate
from farm.utils.helpers import generate_id


class MemoryManager:
    """Manages memory storage and retrieval."""

    MEMORIES_DIR = "memories"

    def __init__(
        self,
        storage: JsonStorage | None = None,
        root_path: Path | str | None = None,
    ):
        if storage is not None:
            self.storage = storage
        elif root_path is not None:
            self.storage = JsonStorage(root_path)
        else:
            self.storage = JsonStorage(Path.cwd() / ".farm")

    def _memory_key(self, memory_id: str) -> str:
        """Get storage key for a memory."""
        return f"{self.MEMORIES_DIR}/{memory_id}.json"

    async def create(self, data: MemoryCreate) -> Memory:
        """Create a new memory."""
        memory = Memory(
            id=generate_id(),
            content=data.content,
            metadata=data.metadata,
            tags=data.tags,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        await self.storage.write_json(
            self._memory_key(memory.id), memory.model_dump(mode="json")
        )
        return memory

    async def get(self, memory_id: str) -> Memory | None:
        """Get a memory by ID."""
        data = await self.storage.read_json(self._memory_key(memory_id))
        if data is None:
            return None
        return Memory.model_validate(data)

    async def update(self, memory_id: str, data: MemoryUpdate) -> Memory | None:
        """Update an existing memory."""
        memory = await self.get(memory_id)
        if memory is None:
            return None

        update_data = data.model_dump(exclude_none=True)
        for field, value in update_data.items():
            setattr(memory, field, value)
        memory.updated_at = datetime.now()

        await self.storage.write_json(
            self._memory_key(memory.id), memory.model_dump(mode="json")
        )
        return memory

    async def delete(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        return await self.storage.delete(self._memory_key(memory_id))

    async def list_all(self, tags: list[str] | None = None) -> list[Memory]:
        """List all memories, optionally filtered by tags."""
        keys = await self.storage.list_keys(self.MEMORIES_DIR)
        memories = []
        for key in keys:
            if key.endswith(".json"):
                data = await self.storage.read_json(key)
                if data:
                    memory = Memory.model_validate(data)
                    if tags is None or any(t in memory.tags for t in tags):
                        memories.append(memory)
        return sorted(memories, key=lambda m: m.created_at, reverse=True)

    async def search_by_content(self, query: str, limit: int = 10) -> list[Memory]:
        """Simple text search in memory content."""
        memories = await self.list_all()
        query_lower = query.lower()
        results = [m for m in memories if query_lower in m.content.lower()]
        return results[:limit]
