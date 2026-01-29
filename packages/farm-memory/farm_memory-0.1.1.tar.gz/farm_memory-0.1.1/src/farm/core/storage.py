"""Storage backend abstraction for FARM."""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import aiofiles

from farm.utils.helpers import ensure_dir


class Storage(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    async def read(self, key: str) -> str | None:
        """Read content by key."""
        ...

    @abstractmethod
    async def write(self, key: str, content: str) -> None:
        """Write content to key."""
        ...

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete content by key. Returns True if deleted."""
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        ...

    @abstractmethod
    async def list_keys(self, prefix: str = "") -> list[str]:
        """List all keys with optional prefix filter."""
        ...


class FileStorage(Storage):
    """File system based storage backend."""

    def __init__(self, root_path: Path | str):
        self.root = Path(root_path)
        ensure_dir(self.root)

    def _key_to_path(self, key: str) -> Path:
        """Convert key to file path."""
        safe_key = key.replace("..", "").lstrip("/")
        return self.root / safe_key

    async def read(self, key: str) -> str | None:
        """Read file content by key."""
        path = self._key_to_path(key)
        if not path.exists():
            return None
        async with aiofiles.open(path, encoding="utf-8") as f:
            return await f.read()

    async def write(self, key: str, content: str) -> None:
        """Write content to file."""
        path = self._key_to_path(key)
        ensure_dir(path.parent)
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(content)

    async def delete(self, key: str) -> bool:
        """Delete file by key."""
        path = self._key_to_path(key)
        if path.exists():
            path.unlink()
            return True
        return False

    async def exists(self, key: str) -> bool:
        """Check if file exists."""
        return self._key_to_path(key).exists()

    async def list_keys(self, prefix: str = "") -> list[str]:
        """List all keys (file paths) with optional prefix filter."""
        keys = []
        search_path = self.root / prefix if prefix else self.root
        if not search_path.exists():
            return keys
        for path in search_path.rglob("*"):
            if path.is_file():
                rel_path = path.relative_to(self.root)
                keys.append(str(rel_path))
        return sorted(keys)


class JsonStorage(FileStorage):
    """JSON file storage with automatic serialization."""

    async def read_json(self, key: str) -> dict[str, Any] | None:
        """Read and parse JSON content."""
        content = await self.read(key)
        if content is None:
            return None
        return json.loads(content)

    async def write_json(self, key: str, data: dict[str, Any]) -> None:
        """Serialize and write JSON content."""
        content = json.dumps(data, ensure_ascii=False, indent=2, default=str)
        await self.write(key, content)
