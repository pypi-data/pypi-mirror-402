"""CLI interface for FARM."""

import asyncio
from pathlib import Path
from typing import Annotated

import typer

from farm.core.indexer import Indexer
from farm.core.memory import MemoryManager
from farm.core.storage import JsonStorage
from farm.models.schemas import MemoryCreate

app = typer.Typer(
    name="farm",
    help="FARM - Filesystem As Remote Memory",
    no_args_is_help=True,
)


def get_root_path() -> Path:
    """Get the FARM storage root path."""
    return Path.cwd() / ".farm"


@app.command()
def init(
    path: Annotated[Path | None, typer.Argument(help="Storage path")] = None,
) -> None:
    """Initialize a new FARM storage directory."""
    root = path or get_root_path()
    root.mkdir(parents=True, exist_ok=True)
    (root / "memories").mkdir(exist_ok=True)
    typer.echo(f"Initialized FARM storage at: {root}")


@app.command()
def add(
    content: Annotated[str, typer.Argument(help="Memory content")],
    tags: Annotated[list[str] | None, typer.Option("--tag", "-t", help="Tags")] = None,
) -> None:
    """Add a new memory."""

    async def _add() -> None:
        manager = MemoryManager(JsonStorage(get_root_path()))
        memory = await manager.create(MemoryCreate(content=content, tags=tags or []))
        indexer = Indexer(get_root_path() / "duckdb")
        indexer.add(
            content=memory.content,
            source_id=memory.id,
            source_type="memory",
            metadata={"tags": ",".join(memory.tags)} if memory.tags else None,
        )
        typer.echo(f"Created memory: {memory.id}")

    asyncio.run(_add())


@app.command()
def get(
    memory_id: Annotated[str, typer.Argument(help="Memory ID")],
) -> None:
    """Get a memory by ID."""

    async def _get() -> None:
        manager = MemoryManager(JsonStorage(get_root_path()))
        memory = await manager.get(memory_id)
        if memory:
            typer.echo(f"ID: {memory.id}")
            typer.echo(f"Content: {memory.content}")
            typer.echo(f"Tags: {', '.join(memory.tags) or 'none'}")
            typer.echo(f"Created: {memory.created_at}")
        else:
            typer.echo(f"Memory not found: {memory_id}", err=True)
            raise typer.Exit(1)

    asyncio.run(_get())


@app.command("list")
def list_memories(
    tag: Annotated[
        str | None, typer.Option("--tag", "-t", help="Filter by tag")
    ] = None,
) -> None:
    """List all memories."""

    async def _list() -> None:
        manager = MemoryManager(JsonStorage(get_root_path()))
        tags = [tag] if tag else None
        memories = await manager.list_all(tags=tags)
        if not memories:
            typer.echo("No memories found.")
            return
        for memory in memories:
            tag_str = f" [{', '.join(memory.tags)}]" if memory.tags else ""
            content = memory.content
            preview = content[:50] + "..." if len(content) > 50 else content
            typer.echo(f"{memory.id}: {preview}{tag_str}")

    asyncio.run(_list())


@app.command()
def search(
    query: Annotated[str, typer.Argument(help="Search query")],
    limit: Annotated[int, typer.Option("--limit", "-n")] = 10,
    mode: Annotated[
        str, typer.Option("--mode", "-m", help="Search mode: semantic, text, hybrid")
    ] = "semantic",
    vector_weight: Annotated[
        float, typer.Option("--vector-weight", "-w", help="Vector weight for hybrid")
    ] = 0.5,
) -> None:
    """Search memories using semantic, text, or hybrid search."""

    async def _search() -> None:
        indexer = Indexer(get_root_path() / "duckdb")

        if mode == "text":
            results = indexer.search_text(query, limit=limit, source_type="memory")
        elif mode == "hybrid":
            results = indexer.search_hybrid(
                query, limit=limit, source_type="memory", vector_weight=vector_weight
            )
        else:  # semantic (default)
            results = indexer.search(query, limit=limit, source_type="memory")

        if not results:
            typer.echo("No results found.")
            return
        for result in results:
            content = result.content
            preview = content[:50] + "..." if len(content) > 50 else content
            typer.echo(f"[{result.score:.2f}] {result.id}: {preview}")

    asyncio.run(_search())


@app.command()
def delete(
    memory_id: Annotated[str, typer.Argument(help="Memory ID")],
    force: Annotated[bool, typer.Option("--force", "-f")] = False,
) -> None:
    """Delete a memory."""

    async def _delete() -> None:
        manager = MemoryManager(JsonStorage(get_root_path()))
        memory = await manager.get(memory_id)
        if not memory:
            typer.echo(f"Memory not found: {memory_id}", err=True)
            raise typer.Exit(1)

        if not force:
            typer.confirm(f"Delete memory {memory_id}?", abort=True)

        await manager.delete(memory_id)
        indexer = Indexer(get_root_path() / "duckdb")
        indexer.remove(memory_id)
        typer.echo(f"Deleted memory: {memory_id}")

    asyncio.run(_delete())


@app.command()
def serve(
    host: Annotated[str, typer.Option("--host", "-h", help="Host")] = "127.0.0.1",
    port: Annotated[int, typer.Option("--port", "-p", help="Port")] = 8000,
) -> None:
    """Start the REST API server."""
    import uvicorn

    from farm.api.app import create_app

    app = create_app(get_root_path())
    uvicorn.run(app, host=host, port=port)


@app.command()
def mcp() -> None:
    """Start the MCP server."""
    from farm.mcp.server import run_server

    run_server(get_root_path())


if __name__ == "__main__":
    app()
