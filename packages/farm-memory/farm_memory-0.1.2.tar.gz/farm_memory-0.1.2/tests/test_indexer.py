"""Tests for the file indexer."""

from pathlib import Path

import pytest

from farm.core.indexer import Indexer


@pytest.fixture
def indexer(tmp_path: Path) -> Indexer:
    """Create an indexer with temporary storage."""
    return Indexer(tmp_path / "duckdb")


def test_add_and_search(indexer: Indexer) -> None:
    """Test adding content and searching."""
    indexer.add(
        content="Python is a programming language",
        source_id="doc1",
        source_type="memory",
    )
    indexer.add(
        content="JavaScript runs in browsers",
        source_id="doc2",
        source_type="memory",
    )

    results = indexer.search("programming language", limit=5)
    assert len(results) > 0
    assert results[0].id == "doc1"
    assert results[0].score > 0


def test_search_with_filter(indexer: Indexer) -> None:
    """Test searching with source type filter."""
    indexer.add(
        content="Memory about Python",
        source_id="mem1",
        source_type="memory",
    )
    indexer.add(
        content="File about Python",
        source_id="file1",
        source_type="file",
    )

    memory_results = indexer.search("Python", source_type="memory")
    assert len(memory_results) == 1
    assert memory_results[0].source_type == "memory"

    file_results = indexer.search("Python", source_type="file")
    assert len(file_results) == 1
    assert file_results[0].source_type == "file"


def test_search_text(indexer: Indexer) -> None:
    """Test full-text search using BM25."""
    indexer.add(
        content="Python is a popular programming language",
        source_id="doc1",
        source_type="memory",
    )
    indexer.add(
        content="JavaScript is used for web development",
        source_id="doc2",
        source_type="memory",
    )

    results = indexer.search_text("Python programming", limit=5)
    assert len(results) > 0
    assert results[0].id == "doc1"


def test_search_hybrid(indexer: Indexer) -> None:
    """Test hybrid search combining vector and full-text."""
    indexer.add(
        content="Machine learning with Python",
        source_id="doc1",
        source_type="memory",
    )
    indexer.add(
        content="Web development with JavaScript",
        source_id="doc2",
        source_type="memory",
    )

    results = indexer.search_hybrid(
        "Python machine learning", limit=5, vector_weight=0.5
    )
    assert len(results) > 0
    assert results[0].id == "doc1"


def test_search_hybrid_with_different_weights(indexer: Indexer) -> None:
    """Test hybrid search with different vector weights."""
    indexer.add(
        content="Deep learning neural networks",
        source_id="doc1",
        source_type="memory",
    )
    indexer.add(
        content="Machine learning algorithms",
        source_id="doc2",
        source_type="memory",
    )

    # Test with high vector weight
    results_vector = indexer.search_hybrid("deep learning", vector_weight=0.9)
    assert len(results_vector) > 0

    # Test with high text weight
    results_text = indexer.search_hybrid("deep learning", vector_weight=0.1)
    assert len(results_text) > 0


def test_remove(indexer: Indexer) -> None:
    """Test removing indexed content."""
    indexer.add(
        content="Test content",
        source_id="doc1",
        source_type="memory",
    )

    results_before = indexer.search("Test content")
    assert len(results_before) == 1

    indexer.remove("doc1")

    results_after = indexer.search("Test content")
    assert len(results_after) == 0


def test_clear(indexer: Indexer) -> None:
    """Test clearing all indexed content."""
    indexer.add(content="Doc 1", source_id="d1", source_type="memory")
    indexer.add(content="Doc 2", source_id="d2", source_type="file")

    indexer.clear()

    results = indexer.search("Doc")
    assert len(results) == 0


def test_add_with_metadata(indexer: Indexer) -> None:
    """Test adding content with metadata."""
    indexer.add(
        content="Test content with metadata",
        source_id="doc1",
        source_type="memory",
        metadata={"tags": "test,example"},
    )

    results = indexer.search("Test content")
    assert len(results) == 1
    assert results[0].metadata.get("tags") == "test,example"


def test_chinese_content(indexer: Indexer) -> None:
    """Test indexing and searching Chinese content."""
    indexer.add(
        content="这是一条测试记忆",
        source_id="doc1",
        source_type="memory",
    )
    indexer.add(
        content="Python 是一种编程语言",
        source_id="doc2",
        source_type="memory",
    )

    # Semantic search for Chinese content
    results = indexer.search("测试")
    assert len(results) > 0
    assert results[0].id == "doc1"
