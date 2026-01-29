"""Memory API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from farm.core.indexer import Indexer
from farm.core.memory import MemoryManager
from farm.models.schemas import (
    Memory,
    MemoryCreate,
    MemoryUpdate,
    SearchQuery,
    SearchResult,
)

router = APIRouter()


def get_memory_manager(request: Request) -> MemoryManager:
    """Get memory manager from app state."""
    return request.app.state.memory_manager


def get_indexer(request: Request) -> Indexer:
    """Get indexer from app state."""
    return request.app.state.indexer


@router.post("", response_model=Memory, status_code=201)
async def create_memory(
    data: MemoryCreate,
    manager: Annotated[MemoryManager, Depends(get_memory_manager)],
    indexer: Annotated[Indexer, Depends(get_indexer)],
) -> Memory:
    """Create a new memory."""
    memory = await manager.create(data)
    indexer.add(
        content=memory.content,
        source_id=memory.id,
        source_type="memory",
        metadata={"tags": ",".join(memory.tags)} if memory.tags else None,
    )
    return memory


@router.get("", response_model=list[Memory])
async def list_memories(
    manager: Annotated[MemoryManager, Depends(get_memory_manager)],
    tag: str | None = None,
) -> list[Memory]:
    """List all memories."""
    tags = [tag] if tag else None
    return await manager.list_all(tags=tags)


@router.get("/{memory_id}", response_model=Memory)
async def get_memory(
    memory_id: str,
    manager: Annotated[MemoryManager, Depends(get_memory_manager)],
) -> Memory:
    """Get a memory by ID."""
    memory = await manager.get(memory_id)
    if memory is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memory


@router.patch("/{memory_id}", response_model=Memory)
async def update_memory(
    memory_id: str,
    data: MemoryUpdate,
    manager: Annotated[MemoryManager, Depends(get_memory_manager)],
    indexer: Annotated[Indexer, Depends(get_indexer)],
) -> Memory:
    """Update a memory."""
    memory = await manager.update(memory_id, data)
    if memory is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    if data.content is not None:
        indexer.remove(memory_id)
        indexer.add(
            content=memory.content,
            source_id=memory.id,
            source_type="memory",
            metadata={"tags": ",".join(memory.tags)} if memory.tags else None,
        )
    return memory


@router.delete("/{memory_id}", status_code=204)
async def delete_memory(
    memory_id: str,
    manager: Annotated[MemoryManager, Depends(get_memory_manager)],
    indexer: Annotated[Indexer, Depends(get_indexer)],
) -> None:
    """Delete a memory."""
    if not await manager.delete(memory_id):
        raise HTTPException(status_code=404, detail="Memory not found")
    indexer.remove(memory_id)


@router.post("/search", response_model=list[SearchResult])
async def search_memories(
    query: SearchQuery,
    indexer: Annotated[Indexer, Depends(get_indexer)],
) -> list[SearchResult]:
    """Search memories using semantic, text, or hybrid search."""
    source_type = "memory" if query.source_type is None else query.source_type

    if query.mode == "text":
        return indexer.search_text(
            query=query.query,
            limit=query.limit,
            source_type=source_type,
        )
    elif query.mode == "hybrid":
        return indexer.search_hybrid(
            query=query.query,
            limit=query.limit,
            source_type=source_type,
            vector_weight=query.vector_weight,
        )
    else:  # semantic (default)
        return indexer.search(
            query=query.query,
            limit=query.limit,
            source_type=source_type,
        )
