# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FARM (Filesystem As Remote Memory) is a Python-based agent memory storage system that provides CLI, REST API, and MCP server interfaces for managing memories with semantic search capabilities.

## Commands

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest
uv run pytest -v                    # Verbose
uv run pytest tests/test_memory.py  # Single file
uv run pytest -k "test_create"      # Pattern match

# Lint and format
ruff check .
ruff format .

# Development
uv run farm init                    # Initialize .farm/ storage
uv run farm serve                   # Start API server (localhost:8000)
uv run farm mcp                     # Start MCP server

# CLI operations
uv run farm add "content" --tag tag1
uv run farm list
uv run farm search "query" --semantic
```

## Architecture

```
src/farm/
├── api/           # FastAPI REST layer
│   ├── app.py     # Application factory
│   └── routes/    # Endpoint modules (memory.py, files.py)
├── cli/           # Typer CLI (main.py)
├── core/          # Business logic
│   ├── memory.py  # MemoryManager - CRUD operations
│   ├── storage.py # FileStorage, JsonStorage - async file I/O
│   └── indexer.py # Indexer - ChromaDB vector search
├── mcp/           # Model Context Protocol server
├── models/        # Pydantic v2 schemas
└── utils/         # Helpers
```

**Key patterns:**
- All three interfaces (CLI, API, MCP) share the same core layer
- Async/await throughout - all storage operations are non-blocking
- Storage uses `.farm/` directory with JSON files for memories and ChromaDB for vector search
- Pydantic v2 models with `MemoryCreate`/`MemoryUpdate` for request validation

## MCP Integration

The MCP server exposes 9 tools: `memory_create`, `memory_get`, `memory_update`, `memory_delete`, `memory_list`, `memory_search`, `file_read`, `file_write`, `file_list`.

Claude config:
```json
{
  "mcpServers": {
    "farm": {
      "command": "uv",
      "args": ["run", "farm", "mcp"]
    }
  }
}
```

## Testing

Tests are async by default (`asyncio_mode = "auto"`). Uses `pytest-asyncio` with `httpx.AsyncClient` for API testing.

Test structure:
- `test_memory.py` - MemoryManager unit tests
- `test_api.py` - REST endpoint integration tests
- `test_indexer.py` - ChromaDB/vector search tests
