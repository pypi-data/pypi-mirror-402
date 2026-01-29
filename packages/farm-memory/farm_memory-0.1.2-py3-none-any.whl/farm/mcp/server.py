"""MCP Server for FARM."""

import asyncio
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from farm.core.indexer import Indexer
from farm.core.memory import MemoryManager
from farm.core.storage import JsonStorage
from farm.models.schemas import MemoryCreate, MemoryUpdate


def create_server(root_path: Path) -> Server:
    """Create and configure the MCP server."""
    server = Server("farm")
    storage = JsonStorage(root_path)
    memory_manager = MemoryManager(storage)
    indexer = Indexer(root_path / "duckdb")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="memory_create",
                description="Create a new memory entry",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Memory content"},
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Tags for categorization",
                        },
                    },
                    "required": ["content"],
                },
            ),
            Tool(
                name="memory_get",
                description="Get a memory by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Memory ID"},
                    },
                    "required": ["id"],
                },
            ),
            Tool(
                name="memory_update",
                description="Update an existing memory",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Memory ID"},
                        "content": {"type": "string", "description": "New content"},
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "New tags",
                        },
                    },
                    "required": ["id"],
                },
            ),
            Tool(
                name="memory_delete",
                description="Delete a memory",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Memory ID"},
                    },
                    "required": ["id"],
                },
            ),
            Tool(
                name="memory_list",
                description="List all memories",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by tags",
                        },
                    },
                },
            ),
            Tool(
                name="memory_search",
                description="Search memories using semantic, text, or hybrid search",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "limit": {
                            "type": "integer",
                            "description": "Maximum results",
                            "default": 10,
                        },
                        "mode": {
                            "type": "string",
                            "description": "Search mode: semantic, text, or hybrid",
                            "default": "semantic",
                            "enum": ["semantic", "text", "hybrid"],
                        },
                        "vector_weight": {
                            "type": "number",
                            "description": "Vector weight for hybrid mode (0-1)",
                            "default": 0.5,
                        },
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="file_read",
                description="Read file content",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path"},
                    },
                    "required": ["path"],
                },
            ),
            Tool(
                name="file_write",
                description="Write content to file",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path"},
                        "content": {"type": "string", "description": "File content"},
                    },
                    "required": ["path", "content"],
                },
            ),
            Tool(
                name="file_list",
                description="List files in storage",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prefix": {
                            "type": "string",
                            "description": "Path prefix filter",
                        },
                    },
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        result: str = ""

        if name == "memory_create":
            memory = await memory_manager.create(
                MemoryCreate(
                    content=arguments["content"],
                    tags=arguments.get("tags", []),
                )
            )
            indexer.add(
                content=memory.content,
                source_id=memory.id,
                source_type="memory",
            )
            result = f"Created memory: {memory.id}"

        elif name == "memory_get":
            memory = await memory_manager.get(arguments["id"])
            if memory:
                result = (
                    f"ID: {memory.id}\nContent: {memory.content}\nTags: {memory.tags}"
                )
            else:
                result = "Memory not found"

        elif name == "memory_update":
            update_data = MemoryUpdate(
                content=arguments.get("content"),
                tags=arguments.get("tags"),
            )
            memory = await memory_manager.update(arguments["id"], update_data)
            if memory:
                if arguments.get("content"):
                    indexer.remove(memory.id)
                    indexer.add(
                        content=memory.content,
                        source_id=memory.id,
                        source_type="memory",
                    )
                result = f"Updated memory: {memory.id}"
            else:
                result = "Memory not found"

        elif name == "memory_delete":
            if await memory_manager.delete(arguments["id"]):
                indexer.remove(arguments["id"])
                result = f"Deleted memory: {arguments['id']}"
            else:
                result = "Memory not found"

        elif name == "memory_list":
            memories = await memory_manager.list_all(tags=arguments.get("tags"))
            if memories:
                lines = [f"- {m.id}: {m.content[:50]}..." for m in memories]
                result = "\n".join(lines)
            else:
                result = "No memories found"

        elif name == "memory_search":
            mode = arguments.get("mode", "semantic")
            limit = arguments.get("limit", 10)
            vector_weight = arguments.get("vector_weight", 0.5)

            if mode == "text":
                results = indexer.search_text(
                    query=arguments["query"],
                    limit=limit,
                    source_type="memory",
                )
            elif mode == "hybrid":
                results = indexer.search_hybrid(
                    query=arguments["query"],
                    limit=limit,
                    source_type="memory",
                    vector_weight=vector_weight,
                )
            else:  # semantic (default)
                results = indexer.search(
                    query=arguments["query"],
                    limit=limit,
                    source_type="memory",
                )

            if results:
                lines = [
                    f"[{r.score:.2f}] {r.id}: {r.content[:50]}..." for r in results
                ]
                result = "\n".join(lines)
            else:
                result = "No results found"

        elif name == "file_read":
            content = await storage.read(arguments["path"])
            result = content if content else "File not found"

        elif name == "file_write":
            await storage.write(arguments["path"], arguments["content"])
            indexer.add(
                content=arguments["content"],
                source_id=arguments["path"],
                source_type="file",
            )
            result = f"Written to: {arguments['path']}"

        elif name == "file_list":
            files = await storage.list_keys(arguments.get("prefix", ""))
            result = "\n".join(files) if files else "No files found"

        return [TextContent(type="text", text=result)]

    return server


def run_server(root_path: Path) -> None:
    """Run the MCP server."""
    server = create_server(root_path)

    async def main() -> None:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )

    asyncio.run(main())
