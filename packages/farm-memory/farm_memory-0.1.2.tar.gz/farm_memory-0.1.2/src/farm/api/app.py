"""FastAPI application for FARM."""

from pathlib import Path
from typing import Any

from fastapi import FastAPI

from farm.api.routes import files, memory
from farm.core.indexer import Indexer
from farm.core.memory import MemoryManager
from farm.core.storage import JsonStorage


def create_app(root_path: Path | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    root = root_path or Path.cwd() / ".farm"

    app = FastAPI(
        title="FARM API",
        description="Filesystem As Remote Memory - REST API",
        version="0.1.0",
    )

    storage = JsonStorage(root)
    memory_manager = MemoryManager(storage)
    indexer = Indexer(root / "duckdb")

    app.state.storage = storage
    app.state.memory_manager = memory_manager
    app.state.indexer = indexer

    app.include_router(memory.router, prefix="/api/v1/memories", tags=["memories"])
    app.include_router(files.router, prefix="/api/v1/files", tags=["files"])

    @app.get("/health")
    async def health_check() -> dict[str, Any]:
        return {"status": "healthy", "version": "0.1.0"}

    return app


app = create_app()
