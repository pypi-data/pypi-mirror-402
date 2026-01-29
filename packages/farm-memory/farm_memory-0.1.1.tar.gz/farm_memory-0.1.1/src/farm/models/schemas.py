"""Pydantic models for FARM."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Memory(BaseModel):
    """A memory entry stored in the filesystem."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Unique memory identifier")
    content: str = Field(..., description="Memory content")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now, description="Last update timestamp"
    )


class MemoryCreate(BaseModel):
    """Request model for creating a memory."""

    content: str = Field(..., description="Memory content")
    metadata: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class MemoryUpdate(BaseModel):
    """Request model for updating a memory."""

    content: str | None = Field(None, description="New content")
    metadata: dict[str, Any] | None = Field(None, description="New metadata")
    tags: list[str] | None = Field(None, description="New tags")


class File(BaseModel):
    """A file stored in the filesystem."""

    model_config = ConfigDict(from_attributes=True)

    path: str = Field(..., description="File path relative to storage root")
    name: str = Field(..., description="File name")
    content_hash: str = Field(..., description="SHA-256 hash of content")
    size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(default="text/plain", description="MIME type")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Index(BaseModel):
    """Index entry for semantic search."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Index entry ID")
    source_id: str = Field(..., description="Source memory or file ID")
    source_type: str = Field(..., description="Type: 'memory' or 'file'")
    content: str = Field(..., description="Indexed content")
    embedding: list[float] | None = Field(None, description="Vector embedding")
    created_at: datetime = Field(default_factory=datetime.now)


class SearchResult(BaseModel):
    """Search result with relevance score."""

    id: str = Field(..., description="Source ID")
    source_type: str = Field(..., description="Type: 'memory' or 'file'")
    content: str = Field(..., description="Content snippet")
    score: float = Field(..., description="Relevance score (0-1)")
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchQuery(BaseModel):
    """Search query parameters."""

    query: str = Field(..., description="Search query text")
    limit: int = Field(10, ge=1, le=100, description="Maximum results")
    tags: list[str] | None = Field(None, description="Filter by tags")
    source_type: str | None = Field(None, description="Filter by source type")
    mode: str = Field(
        "semantic",
        description="Search mode: 'semantic' (vector), 'text' (full-text), 'hybrid'",
    )
    vector_weight: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Weight for vector search in hybrid mode (0-1)",
    )
