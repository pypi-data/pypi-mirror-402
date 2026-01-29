"""File indexer for semantic and full-text search using DuckDB."""

from pathlib import Path
from typing import Any

from farm.models.schemas import Index, SearchResult
from farm.utils.helpers import generate_id


class Indexer:
    """Indexes content for semantic and full-text search using DuckDB."""

    EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
    EMBEDDING_DIM = 512  # bge-small-zh-v1.5 outputs 512 dimensions

    def __init__(self, persist_path: Path | str | None = None):
        if persist_path:
            self.persist_path = Path(persist_path)
        else:
            self.persist_path = Path.cwd() / ".farm" / "duckdb"
        self._conn: Any = None
        self._model: Any = None

    def _ensure_connection(self) -> None:
        """Lazily initialize DuckDB connection and setup tables."""
        if self._conn is not None:
            return

        import duckdb

        self.persist_path.mkdir(parents=True, exist_ok=True)
        db_file = self.persist_path / "index.duckdb"
        self._conn = duckdb.connect(str(db_file))

        # Install and load extensions
        self._conn.execute("INSTALL vss")
        self._conn.execute("LOAD vss")
        self._conn.execute("INSTALL fts")
        self._conn.execute("LOAD fts")

        # Enable experimental HNSW persistence for persistent databases
        self._conn.execute("SET hnsw_enable_experimental_persistence = true")

        # Create documents table if not exists
        self._conn.execute(f"""
            CREATE TABLE IF NOT EXISTS documents (
                id VARCHAR PRIMARY KEY,
                source_id VARCHAR NOT NULL,
                source_type VARCHAR NOT NULL,
                content TEXT NOT NULL,
                embedding FLOAT[{self.EMBEDDING_DIM}],
                metadata JSON,
                created_at TIMESTAMP DEFAULT now()
            )
        """)

        # Create HNSW index for vector search if not exists
        try:
            self._conn.execute("""
                CREATE INDEX idx_embedding ON documents
                USING HNSW (embedding)
                WITH (metric = 'cosine')
            """)
        except duckdb.CatalogException:
            pass  # Index already exists

        # Create FTS index if not exists
        try:
            self._conn.execute("""
                PRAGMA create_fts_index('documents', 'id', 'content', stemmer='porter')
            """)
        except duckdb.CatalogException:
            pass  # Index already exists

    def _ensure_model(self) -> None:
        """Lazily initialize the embedding model."""
        if self._model is not None:
            return

        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(self.EMBEDDING_MODEL)

    def _get_embedding(self, text: str) -> list[float]:
        """Generate embedding for text."""
        self._ensure_model()
        embedding = self._model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def add(
        self,
        content: str,
        source_id: str,
        source_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> Index:
        """Add content to the index."""
        self._ensure_connection()
        index_id = generate_id()

        embedding = self._get_embedding(content)
        metadata_json = metadata if metadata else {}

        self._conn.execute(
            """
            INSERT INTO documents
                (id, source_id, source_type, content, embedding, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [index_id, source_id, source_type, content, embedding, metadata_json],
        )

        return Index(
            id=index_id,
            source_id=source_id,
            source_type=source_type,
            content=content,
        )

    def search(
        self,
        query: str,
        limit: int = 10,
        source_type: str | None = None,
    ) -> list[SearchResult]:
        """Search the index using vector similarity (semantic search)."""
        self._ensure_connection()

        query_embedding = self._get_embedding(query)

        # Build WHERE clause for source_type filter
        where_clause = ""
        params: list[Any] = [query_embedding, limit]
        if source_type:
            where_clause = "WHERE source_type = ?"
            params = [query_embedding, source_type, limit]

        # Use array_cosine_distance for similarity search
        dim = self.EMBEDDING_DIM
        if source_type:
            results = self._conn.execute(
                f"""
                SELECT
                    source_id, source_type, content, metadata,
                    1 - array_cosine_distance(embedding, ?::FLOAT[{dim}]) AS score
                FROM documents
                {where_clause}
                ORDER BY score DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
        else:
            results = self._conn.execute(
                f"""
                SELECT
                    source_id, source_type, content, metadata,
                    1 - array_cosine_distance(embedding, ?::FLOAT[{dim}]) AS score
                FROM documents
                ORDER BY score DESC
                LIMIT ?
                """,
                params,
            ).fetchall()

        return self._format_results(results)

    def search_text(
        self,
        query: str,
        limit: int = 10,
        source_type: str | None = None,
    ) -> list[SearchResult]:
        """Search the index using full-text search (keyword matching)."""
        self._ensure_connection()

        # Split query into keywords for matching
        keywords = query.lower().split()
        if not keywords:
            return []

        # Build LIKE conditions for each keyword
        like_conditions = " AND ".join(
            ["LOWER(content) LIKE '%' || ? || '%'" for _ in keywords]
        )

        # Build WHERE clause
        where_clause = f"WHERE {like_conditions}"
        params: list[Any] = keywords.copy()

        if source_type:
            where_clause += " AND source_type = ?"
            params.append(source_type)

        params.append(limit)

        # Calculate a simple relevance score based on keyword frequency
        results = self._conn.execute(
            f"""
            SELECT
                source_id,
                source_type,
                content,
                metadata,
                1.0 AS score
            FROM documents
            {where_clause}
            LIMIT ?
            """,
            params,
        ).fetchall()

        return self._format_results(results)

    def search_hybrid(
        self,
        query: str,
        limit: int = 10,
        source_type: str | None = None,
        vector_weight: float = 0.5,
    ) -> list[SearchResult]:
        """Search using hybrid (vector + keyword) with weighted scoring."""
        self._ensure_connection()

        query_embedding = self._get_embedding(query)
        text_weight = 1.0 - vector_weight

        # Build text match condition
        keywords = query.lower().split()
        text_match = "0"
        if keywords:
            # Simple text matching score: 1 if all keywords match, 0 otherwise
            like_conditions = " AND ".join(
                [f"LOWER(content) LIKE '%{kw}%'" for kw in keywords]
            )
            text_match = f"CASE WHEN {like_conditions} THEN 1 ELSE 0 END"

        # Build WHERE clause for source_type filter
        where_clause = ""
        params: list[Any] = [vector_weight, query_embedding, text_weight, limit]
        if source_type:
            where_clause = "WHERE source_type = ?"
            params = [vector_weight, query_embedding, text_weight, source_type, limit]

        # Hybrid search combining vector similarity and text matching
        dim = self.EMBEDDING_DIM
        results = self._conn.execute(
            f"""
            SELECT
                source_id, source_type, content, metadata,
                (? * (1 - array_cosine_distance(embedding, ?::FLOAT[{dim}]))
                 + ? * {text_match}) AS score
            FROM documents
            {where_clause}
            ORDER BY score DESC
            LIMIT ?
            """,
            params,
        ).fetchall()

        return self._format_results(results)

    def _format_results(self, results: list[tuple]) -> list[SearchResult]:
        """Format database results into SearchResult objects."""
        import json

        search_results = []
        for row in results:
            source_id, source_type, content, metadata, score = row

            # Handle metadata - could be dict, str (JSON), or None
            if isinstance(metadata, dict):
                extra = metadata
            elif isinstance(metadata, str):
                try:
                    extra = json.loads(metadata)
                except (json.JSONDecodeError, TypeError):
                    extra = {}
            else:
                extra = {}

            search_results.append(
                SearchResult(
                    id=source_id,
                    source_type=source_type,
                    content=content,
                    score=float(score) if score else 0.0,
                    metadata=extra,
                )
            )
        return search_results

    def remove(self, source_id: str) -> bool:
        """Remove all index entries for a source."""
        self._ensure_connection()
        try:
            result = self._conn.execute(
                "DELETE FROM documents WHERE source_id = ? RETURNING id",
                [source_id],
            ).fetchall()
            return len(result) > 0
        except Exception:
            return False

    def clear(self) -> None:
        """Clear all indexed content."""
        self._ensure_connection()
        self._conn.execute("DELETE FROM documents")
