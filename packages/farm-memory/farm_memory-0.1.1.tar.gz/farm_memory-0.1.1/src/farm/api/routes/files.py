"""File API routes."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from farm.core.indexer import Indexer
from farm.core.storage import FileStorage
from farm.models.schemas import File, SearchQuery, SearchResult
from farm.utils.helpers import hash_content

router = APIRouter()


def get_storage(request: Request) -> FileStorage:
    """Get file storage from app state."""
    return request.app.state.storage


def get_indexer(request: Request) -> Indexer:
    """Get indexer from app state."""
    return request.app.state.indexer


@router.get("", response_model=list[str])
async def list_files(
    storage: Annotated[FileStorage, Depends(get_storage)],
    prefix: str = "",
) -> list[str]:
    """List all files."""
    return await storage.list_keys(prefix)


@router.get("/{file_path:path}/content")
async def get_file_content(
    file_path: str,
    storage: Annotated[FileStorage, Depends(get_storage)],
) -> dict[str, str]:
    """Get file content."""
    content = await storage.read(file_path)
    if content is None:
        raise HTTPException(status_code=404, detail="File not found")
    return {"content": content}


@router.get("/{file_path:path}", response_model=File)
async def get_file(
    file_path: str,
    storage: Annotated[FileStorage, Depends(get_storage)],
) -> File:
    """Get file metadata."""
    content = await storage.read(file_path)
    if content is None:
        raise HTTPException(status_code=404, detail="File not found")

    path_obj = storage._key_to_path(file_path)
    return File(
        path=file_path,
        name=path_obj.name,
        content_hash=hash_content(content),
        size=len(content.encode("utf-8")),
        created_at=datetime.fromtimestamp(path_obj.stat().st_ctime),
        updated_at=datetime.fromtimestamp(path_obj.stat().st_mtime),
    )


@router.put("/{file_path:path}")
async def write_file(
    file_path: str,
    content: str,
    storage: Annotated[FileStorage, Depends(get_storage)],
    indexer: Annotated[Indexer, Depends(get_indexer)],
) -> dict[str, str]:
    """Write content to a file."""
    await storage.write(file_path, content)
    indexer.add(
        content=content,
        source_id=file_path,
        source_type="file",
    )
    return {"path": file_path, "status": "created"}


@router.delete("/{file_path:path}", status_code=204)
async def delete_file(
    file_path: str,
    storage: Annotated[FileStorage, Depends(get_storage)],
    indexer: Annotated[Indexer, Depends(get_indexer)],
) -> None:
    """Delete a file."""
    if not await storage.delete(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    indexer.remove(file_path)


@router.post("/search", response_model=list[SearchResult])
async def search_files(
    query: SearchQuery,
    indexer: Annotated[Indexer, Depends(get_indexer)],
) -> list[SearchResult]:
    """Search files using semantic search."""
    return indexer.search(
        query=query.query,
        limit=query.limit,
        source_type="file",
    )
