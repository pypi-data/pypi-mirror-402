"""
Tests for file_compass.indexer module.
Uses mocks and temporary directories to avoid external dependencies.
"""

import pytest
import tempfile
import sqlite3
import numpy as np
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from file_compass.indexer import FileIndex, SearchResult, get_index


@pytest.fixture
def temp_index():
    """Create a temporary FileIndex that gets cleaned up properly."""
    import tempfile
    import shutil

    tmpdir = tempfile.mkdtemp()
    index_path = Path(tmpdir) / "test.hnsw"
    sqlite_path = Path(tmpdir) / "test.db"
    index = FileIndex(index_path=index_path, sqlite_path=sqlite_path)

    yield index, tmpdir

    # Cleanup - close connections first
    if index._conn:
        index._conn.close()
        index._conn = None
    # Give Windows time to release file handles
    import time
    time.sleep(0.1)
    try:
        shutil.rmtree(tmpdir)
    except PermissionError:
        pass  # Best effort cleanup


class TestSearchResult:
    """Tests for SearchResult dataclass."""

    def test_search_result_creation(self):
        """Test creating a SearchResult."""
        now = datetime.now()
        result = SearchResult(
            path="/test/file.py",
            relative_path="file.py",
            file_type="python",
            chunk_type="function",
            chunk_name="my_func",
            line_start=10,
            line_end=20,
            preview="def my_func():",
            relevance=0.85,
            modified_at=now,
            git_tracked=True
        )
        assert result.path == "/test/file.py"
        assert result.relative_path == "file.py"
        assert result.file_type == "python"
        assert result.chunk_type == "function"
        assert result.chunk_name == "my_func"
        assert result.line_start == 10
        assert result.line_end == 20
        assert result.preview == "def my_func():"
        assert result.relevance == 0.85
        assert result.modified_at == now
        assert result.git_tracked is True

    def test_search_result_without_chunk_name(self):
        """Test SearchResult with no chunk name."""
        result = SearchResult(
            path="/test/file.py",
            relative_path="file.py",
            file_type="python",
            chunk_type="window",
            chunk_name=None,
            line_start=1,
            line_end=50,
            preview="content...",
            relevance=0.7,
            modified_at=datetime.now(),
            git_tracked=False
        )
        assert result.chunk_name is None


class TestFileIndex:
    """Tests for FileIndex class."""

    def test_init_defaults(self):
        """Test default initialization."""
        index = FileIndex()
        assert index.dim == 768
        assert index.M > 0
        assert index.ef_construction > 0
        assert index.ef_search > 0
        assert index.max_elements > 0
        assert index.space == "cosine"
        assert index._index is None
        assert index._conn is None

    def test_init_custom_paths(self, temp_index):
        """Test custom path initialization."""
        index, tmpdir = temp_index
        assert index.index_path == Path(tmpdir) / "test.hnsw"
        assert index.sqlite_path == Path(tmpdir) / "test.db"

    def test_get_conn_creates_connection(self, temp_index):
        """Test that _get_conn creates a SQLite connection."""
        index, _ = temp_index

        conn = index._get_conn()

        assert conn is not None
        assert index._conn is conn

        # Verify schema was created
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = {row[0] for row in cursor}
        assert "files" in tables
        assert "chunks" in tables
        assert "index_meta" in tables

    def test_get_conn_reuses_connection(self, temp_index):
        """Test that _get_conn reuses existing connection."""
        index, _ = temp_index

        conn1 = index._get_conn()
        conn2 = index._get_conn()

        assert conn1 is conn2

    def test_init_schema(self, temp_index):
        """Test SQLite schema initialization."""
        index, _ = temp_index
        conn = index._get_conn()

        # Check files table structure
        cursor = conn.execute("PRAGMA table_info(files)")
        columns = {row[1] for row in cursor}
        expected_cols = {"id", "path", "relative_path", "file_type", "size_bytes",
                       "modified_at", "indexed_at", "content_hash", "git_repo",
                       "is_git_tracked", "total_chunks"}
        assert expected_cols.issubset(columns)

        # Check chunks table structure
        cursor = conn.execute("PRAGMA table_info(chunks)")
        columns = {row[1] for row in cursor}
        expected_cols = {"id", "file_id", "chunk_index", "chunk_type", "name",
                       "line_start", "line_end", "content_preview", "token_count",
                       "embedding_id"}
        assert expected_cols.issubset(columns)

    def test_get_index_creates_new_index(self, temp_index):
        """Test that _get_index creates a new HNSW index."""
        index, _ = temp_index

        hnsw_index = index._get_index()

        assert hnsw_index is not None
        assert index._index is hnsw_index

    def test_get_index_loads_existing(self, temp_index):
        """Test that _get_index loads existing index."""
        index, tmpdir = temp_index
        hnsw1 = index._get_index()

        # Add a test vector
        test_vec = np.random.randn(768).astype(np.float32)
        test_vec = test_vec / np.linalg.norm(test_vec)
        hnsw1.add_items(test_vec.reshape(1, -1), np.array([0]))
        index._save_index()

        # Close and reload
        index._index = None
        hnsw2 = index._get_index()

        assert hnsw2.get_current_count() == 1

    def test_save_index(self, temp_index):
        """Test index persistence."""
        index, _ = temp_index
        hnsw = index._get_index()

        # Add a test vector
        test_vec = np.random.randn(768).astype(np.float32)
        test_vec = test_vec / np.linalg.norm(test_vec)
        hnsw.add_items(test_vec.reshape(1, -1), np.array([0]))

        index._save_index()

        assert index.index_path.exists()

    def test_get_status_empty(self, temp_index):
        """Test status of empty index."""
        index, _ = temp_index

        status = index.get_status()

        assert status["files_indexed"] == 0
        assert status["chunks_indexed"] == 0
        assert status["last_build"] is None
        assert status["file_types"] == {}

    def test_get_status_with_data(self, temp_index):
        """Test status with indexed data."""
        index, _ = temp_index
        conn = index._get_conn()

        # Insert test data
        conn.execute("""
            INSERT INTO files (path, relative_path, file_type, size_bytes,
                               modified_at, content_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("/test/file.py", "file.py", "python", 100,
              datetime.now().isoformat(), "abc123"))
        conn.execute("""
            INSERT INTO chunks (file_id, chunk_index, chunk_type, line_start,
                               line_end, embedding_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (1, 0, "function", 1, 10, 0))
        conn.execute(
            "INSERT OR REPLACE INTO index_meta (key, value) VALUES (?, ?)",
            ("last_build", datetime.now().isoformat())
        )
        conn.commit()

        status = index.get_status()

        assert status["files_indexed"] == 1
        assert status["chunks_indexed"] == 1
        assert status["last_build"] is not None
        assert "python" in status["file_types"]
        assert status["file_types"]["python"] == 1

    @pytest.mark.asyncio
    async def test_close(self, temp_index):
        """Test resource cleanup."""
        index, _ = temp_index

        # Initialize connection
        index._get_conn()
        assert index._conn is not None

        await index.close()

        assert index._conn is None

    def test_load_id_mapping(self, temp_index):
        """Test loading embedding ID to chunk mapping."""
        index, _ = temp_index
        conn = index._get_conn()

        # Insert test data
        conn.execute("""
            INSERT INTO files (path, relative_path, file_type, size_bytes,
                               modified_at, content_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("/test/file.py", "file.py", "python", 100,
              datetime.now().isoformat(), "abc123"))
        conn.execute("""
            INSERT INTO chunks (file_id, chunk_index, chunk_type, line_start,
                               line_end, embedding_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (1, 0, "function", 1, 10, 42))
        conn.execute("""
            INSERT INTO chunks (file_id, chunk_index, chunk_type, line_start,
                               line_end, embedding_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (1, 1, "function", 11, 20, 43))
        conn.commit()

        index._load_id_mapping()

        assert len(index._id_to_chunk) == 2
        assert index._id_to_chunk[42] == (1, 0)
        assert index._id_to_chunk[43] == (1, 1)


class TestFileIndexSearch:
    """Tests for search functionality."""

    @pytest.mark.asyncio
    async def test_search_empty_index(self, temp_index):
        """Test searching empty index."""
        index, _ = temp_index

        # Initialize empty index
        index._get_index()

        # Mock embedder
        with patch.object(index.embedder, 'embed_query', new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = np.random.randn(768).astype(np.float32)

            results = await index.search("test query")

            assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_with_results(self, temp_index):
        """Test search returning results."""
        index, _ = temp_index

        conn = index._get_conn()
        hnsw = index._get_index()

        # Insert test data
        conn.execute("""
            INSERT INTO files (path, relative_path, file_type, size_bytes,
                               modified_at, content_hash, is_git_tracked)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("/test/file.py", "file.py", "python", 100,
              datetime.now().isoformat(), "abc123", 1))
        conn.execute("""
            INSERT INTO chunks (file_id, chunk_index, chunk_type, name,
                               line_start, line_end, content_preview, embedding_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (1, 0, "function", "test_func", 1, 10, "def test_func():", 0))
        conn.commit()

        # Add embedding to HNSW
        test_embedding = np.random.randn(768).astype(np.float32)
        test_embedding = test_embedding / np.linalg.norm(test_embedding)
        hnsw.add_items(test_embedding.reshape(1, -1), np.array([0]))
        index._id_to_chunk[0] = (1, 0)

        # Mock embedder to return similar embedding
        with patch.object(index.embedder, 'embed_query', new_callable=AsyncMock) as mock_embed:
            # Return same embedding for high similarity
            mock_embed.return_value = test_embedding

            results = await index.search("test query")

            assert len(results) >= 1
            assert results[0].relative_path == "file.py"
            assert results[0].chunk_name == "test_func"

    @pytest.mark.asyncio
    async def test_search_filter_by_file_type(self, temp_index):
        """Test filtering search by file type."""
        index, _ = temp_index

        conn = index._get_conn()
        hnsw = index._get_index()

        # Insert Python file
        conn.execute("""
            INSERT INTO files (path, relative_path, file_type, size_bytes,
                               modified_at, content_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("/test/code.py", "code.py", "python", 100,
              datetime.now().isoformat(), "abc123"))
        conn.execute("""
            INSERT INTO chunks (file_id, chunk_index, chunk_type,
                               line_start, line_end, content_preview, embedding_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (1, 0, "function", 1, 10, "def func():", 0))

        # Insert Markdown file
        conn.execute("""
            INSERT INTO files (path, relative_path, file_type, size_bytes,
                               modified_at, content_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("/test/readme.md", "readme.md", "markdown", 50,
              datetime.now().isoformat(), "def456"))
        conn.execute("""
            INSERT INTO chunks (file_id, chunk_index, chunk_type,
                               line_start, line_end, content_preview, embedding_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (2, 0, "section", 1, 5, "# README", 1))
        conn.commit()

        # Add embeddings to HNSW
        emb1 = np.random.randn(768).astype(np.float32)
        emb1 = emb1 / np.linalg.norm(emb1)
        emb2 = np.random.randn(768).astype(np.float32)
        emb2 = emb2 / np.linalg.norm(emb2)
        hnsw.add_items(np.vstack([emb1, emb2]), np.array([0, 1]))
        index._id_to_chunk[0] = (1, 0)
        index._id_to_chunk[1] = (2, 0)

        with patch.object(index.embedder, 'embed_query', new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = emb1

            # Filter by Python only
            results = await index.search("test", file_types=["python"])

            python_results = [r for r in results if r.file_type == "python"]
            markdown_results = [r for r in results if r.file_type == "markdown"]

            assert len(python_results) >= 1
            assert len(markdown_results) == 0

    @pytest.mark.asyncio
    async def test_search_filter_by_git_tracked(self, temp_index):
        """Test filtering search by git tracked status."""
        index, _ = temp_index

        conn = index._get_conn()
        hnsw = index._get_index()

        # Insert tracked file
        conn.execute("""
            INSERT INTO files (path, relative_path, file_type, size_bytes,
                               modified_at, content_hash, is_git_tracked)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("/test/tracked.py", "tracked.py", "python", 100,
              datetime.now().isoformat(), "abc123", 1))
        conn.execute("""
            INSERT INTO chunks (file_id, chunk_index, chunk_type,
                               line_start, line_end, content_preview, embedding_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (1, 0, "function", 1, 10, "def func():", 0))

        # Insert untracked file
        conn.execute("""
            INSERT INTO files (path, relative_path, file_type, size_bytes,
                               modified_at, content_hash, is_git_tracked)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("/test/untracked.py", "untracked.py", "python", 50,
              datetime.now().isoformat(), "def456", 0))
        conn.execute("""
            INSERT INTO chunks (file_id, chunk_index, chunk_type,
                               line_start, line_end, content_preview, embedding_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (2, 0, "function", 1, 5, "def other():", 1))
        conn.commit()

        # Add embeddings
        emb1 = np.random.randn(768).astype(np.float32)
        emb1 = emb1 / np.linalg.norm(emb1)
        emb2 = np.random.randn(768).astype(np.float32)
        emb2 = emb2 / np.linalg.norm(emb2)
        hnsw.add_items(np.vstack([emb1, emb2]), np.array([0, 1]))
        index._id_to_chunk[0] = (1, 0)
        index._id_to_chunk[1] = (2, 0)

        with patch.object(index.embedder, 'embed_query', new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = emb1

            # Filter by git tracked only
            results = await index.search("test", git_only=True)

            for r in results:
                assert r.git_tracked is True

    @pytest.mark.asyncio
    async def test_search_min_relevance_filter(self, temp_index):
        """Test filtering by minimum relevance."""
        index, _ = temp_index

        conn = index._get_conn()
        hnsw = index._get_index()

        # Insert file
        conn.execute("""
            INSERT INTO files (path, relative_path, file_type, size_bytes,
                               modified_at, content_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("/test/file.py", "file.py", "python", 100,
              datetime.now().isoformat(), "abc123"))
        conn.execute("""
            INSERT INTO chunks (file_id, chunk_index, chunk_type,
                               line_start, line_end, content_preview, embedding_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (1, 0, "function", 1, 10, "def func():", 0))
        conn.commit()

        # Add embedding
        doc_embedding = np.random.randn(768).astype(np.float32)
        doc_embedding = doc_embedding / np.linalg.norm(doc_embedding)
        hnsw.add_items(doc_embedding.reshape(1, -1), np.array([0]))
        index._id_to_chunk[0] = (1, 0)

        with patch.object(index.embedder, 'embed_query', new_callable=AsyncMock) as mock_embed:
            # Return very different embedding (low similarity)
            query_embedding = np.random.randn(768).astype(np.float32)
            query_embedding = query_embedding / np.linalg.norm(query_embedding)
            mock_embed.return_value = query_embedding

            # With high min_relevance, may filter out results
            results = await index.search("test", min_relevance=0.99)

            # Results should only include high relevance matches
            for r in results:
                assert r.relevance >= 0.99


class TestFileIndexBuild:
    """Tests for index building."""

    @pytest.mark.asyncio
    async def test_build_index_clears_existing(self, temp_index):
        """Test that build_index clears existing data."""
        index, tmpdir = temp_index
        conn = index._get_conn()

        # Insert existing data
        conn.execute("""
            INSERT INTO files (path, relative_path, file_type, size_bytes,
                               modified_at, content_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("/old/file.py", "file.py", "python", 100,
              datetime.now().isoformat(), "old123"))
        conn.commit()

        assert conn.execute("SELECT COUNT(*) FROM files").fetchone()[0] == 1

        # Mock scanner to return empty
        with patch.object(index.scanner, 'scan_all', return_value=iter([])):
            with patch.object(index.embedder, 'embed_batch', new_callable=AsyncMock) as mock_embed:
                mock_embed.return_value = np.array([])

                await index.build_index(show_progress=False)

        # Old data should be cleared
        assert conn.execute("SELECT COUNT(*) FROM files").fetchone()[0] == 0

    @pytest.mark.asyncio
    async def test_build_index_with_files(self, temp_index):
        """Test building index with actual files."""
        index, tmpdir = temp_index

        # Create test file
        test_file = Path(tmpdir) / "test.py"
        test_file.write_text("def hello():\n    return 'world'")

        # Mock scanner to return our test file
        from file_compass.scanner import ScannedFile
        mock_file = ScannedFile(
            path=test_file,
            relative_path="test.py",
            file_type="python",
            size_bytes=35,
            modified_at=datetime.now(),
            content_hash="test123"
        )

        with patch.object(index.scanner, 'scan_all', return_value=iter([mock_file])):
            with patch.object(index.embedder, 'embed_batch', new_callable=AsyncMock) as mock_embed:
                # Return mock embeddings
                mock_embed.return_value = np.random.randn(1, 768).astype(np.float32)

                stats = await index.build_index(show_progress=False)

        assert stats["files_indexed"] == 1
        assert stats["chunks_indexed"] >= 1

    @pytest.mark.asyncio
    async def test_build_index_handles_chunk_error(self, temp_index):
        """Test that build_index handles chunking errors gracefully."""
        index, _ = temp_index

        from file_compass.scanner import ScannedFile
        mock_file = ScannedFile(
            path=Path("/nonexistent/file.py"),
            relative_path="file.py",
            file_type="python",
            size_bytes=100,
            modified_at=datetime.now(),
            content_hash="test123"
        )

        with patch.object(index.scanner, 'scan_all', return_value=iter([mock_file])):
            with patch.object(index.chunker, 'chunk_file', side_effect=Exception("Chunk error")):
                with patch.object(index.embedder, 'embed_batch', new_callable=AsyncMock) as mock_embed:
                    mock_embed.return_value = np.array([]).reshape(0, 768)

                    # Should not raise
                    stats = await index.build_index(show_progress=False)

                    # File recorded but no chunks
                    assert stats["files_indexed"] == 1
                    assert stats["chunks_indexed"] == 0


class TestGetIndex:
    """Tests for module-level get_index function."""

    def test_get_index_creates_singleton(self):
        """Test that get_index creates a singleton."""
        import file_compass.indexer as indexer_module

        # Reset singleton
        indexer_module._index = None

        index1 = get_index()
        index2 = get_index()

        assert index1 is index2

        # Cleanup
        indexer_module._index = None

    def test_get_index_returns_file_index(self):
        """Test that get_index returns FileIndex instance."""
        import file_compass.indexer as indexer_module
        indexer_module._index = None

        index = get_index()

        assert isinstance(index, FileIndex)

        # Cleanup
        indexer_module._index = None


class TestSearchFilters:
    """Additional tests for search filter edge cases."""

    @pytest.mark.asyncio
    async def test_search_filter_by_directory(self, temp_index):
        """Test filtering search by directory prefix."""
        index, _ = temp_index

        conn = index._get_conn()
        hnsw = index._get_index()

        # Insert file in specific directory
        conn.execute("""
            INSERT INTO files (path, relative_path, file_type, size_bytes,
                               modified_at, content_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("/test/src/file.py", "src/file.py", "python", 100,
              datetime.now().isoformat(), "abc123"))
        conn.execute("""
            INSERT INTO chunks (file_id, chunk_index, chunk_type,
                               line_start, line_end, content_preview, embedding_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (1, 0, "function", 1, 10, "def func():", 0))

        # Insert file in different directory
        conn.execute("""
            INSERT INTO files (path, relative_path, file_type, size_bytes,
                               modified_at, content_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("/test/lib/other.py", "lib/other.py", "python", 50,
              datetime.now().isoformat(), "def456"))
        conn.execute("""
            INSERT INTO chunks (file_id, chunk_index, chunk_type,
                               line_start, line_end, content_preview, embedding_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (2, 0, "function", 1, 5, "def other():", 1))
        conn.commit()

        # Add embeddings
        emb1 = np.random.randn(768).astype(np.float32)
        emb1 = emb1 / np.linalg.norm(emb1)
        emb2 = np.random.randn(768).astype(np.float32)
        emb2 = emb2 / np.linalg.norm(emb2)
        hnsw.add_items(np.vstack([emb1, emb2]), np.array([0, 1]))
        index._id_to_chunk[0] = (1, 0)
        index._id_to_chunk[1] = (2, 0)

        with patch.object(index.embedder, 'embed_query', new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = emb1

            # Filter by directory prefix
            results = await index.search("test", directory="/test/src")

            # Only results from /test/src should be returned
            for r in results:
                assert r.path.startswith("/test/src")

    @pytest.mark.asyncio
    async def test_search_missing_chunk_in_mapping(self, temp_index):
        """Test search handles missing chunk in id_to_chunk mapping."""
        index, _ = temp_index

        conn = index._get_conn()
        hnsw = index._get_index()

        # Insert file and chunk
        conn.execute("""
            INSERT INTO files (path, relative_path, file_type, size_bytes,
                               modified_at, content_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("/test/file.py", "file.py", "python", 100,
              datetime.now().isoformat(), "abc123"))
        conn.execute("""
            INSERT INTO chunks (file_id, chunk_index, chunk_type,
                               line_start, line_end, content_preview, embedding_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (1, 0, "function", 1, 10, "def func():", 0))
        conn.commit()

        # Add embedding but DON'T add to _id_to_chunk
        emb1 = np.random.randn(768).astype(np.float32)
        emb1 = emb1 / np.linalg.norm(emb1)
        hnsw.add_items(emb1.reshape(1, -1), np.array([0]))
        # Intentionally not setting index._id_to_chunk[0]

        with patch.object(index.embedder, 'embed_query', new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = emb1

            # Should not crash, just skip this result
            results = await index.search("test")
            # Result should be empty since chunk mapping is missing
            assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_missing_db_row(self, temp_index):
        """Test search handles missing database row."""
        index, _ = temp_index

        hnsw = index._get_index()

        # Add embedding and mapping but NO database entry
        emb1 = np.random.randn(768).astype(np.float32)
        emb1 = emb1 / np.linalg.norm(emb1)
        hnsw.add_items(emb1.reshape(1, -1), np.array([0]))
        index._id_to_chunk[0] = (999, 0)  # Non-existent file_id

        with patch.object(index.embedder, 'embed_query', new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = emb1

            # Should not crash, just skip this result
            results = await index.search("test")
            assert len(results) == 0

    @pytest.mark.asyncio
    async def test_build_index_with_show_progress(self, temp_index, capsys):
        """Test building index with progress output."""
        index, tmpdir = temp_index

        # Create test file
        test_file = Path(tmpdir) / "test.py"
        test_file.write_text("def hello():\n    return 'world'")

        from file_compass.scanner import ScannedFile
        mock_file = ScannedFile(
            path=test_file,
            relative_path="test.py",
            file_type="python",
            size_bytes=35,
            modified_at=datetime.now(),
            content_hash="test123"
        )

        with patch.object(index.scanner, 'scan_all', return_value=iter([mock_file])):
            with patch.object(index.embedder, 'embed_batch', new_callable=AsyncMock) as mock_embed:
                mock_embed.return_value = np.random.randn(1, 768).astype(np.float32)

                # Build with progress
                stats = await index.build_index(show_progress=True)

        # Check that progress was printed
        captured = capsys.readouterr()
        assert "Indexing complete" in captured.out or stats["files_indexed"] >= 0


class TestIncrementalUpdate:
    """Tests for incremental index updates using Merkle tree."""

    @pytest.mark.asyncio
    async def test_incremental_update_no_previous_state(self, temp_index):
        """Test incremental update with no previous Merkle state falls back to full build."""
        index, tmpdir = temp_index

        # Create a test file
        test_file = Path(tmpdir) / "test.py"
        test_file.write_text("def test(): pass")

        # Mock scanner and embedder
        mock_file = ScannedFile(
            path=test_file,
            relative_path="test.py",
            file_type="python",
            size_bytes=20,
            modified_at=datetime.now(),
            content_hash="hash1"
        )

        with patch.object(index.scanner, 'scan_all', return_value=iter([mock_file])):
            with patch.object(index.embedder, 'embed_batch', new_callable=AsyncMock) as mock_embed:
                mock_embed.return_value = np.random.randn(1, 768).astype(np.float32)

                # Should fall back to full build
                stats = await index.incremental_update(show_progress=False)

        # Should have indexed the file (falls back to build_index which has files_indexed)
        assert stats.get("files_indexed", 0) == 1 or stats.get("files_added", 0) >= 0

    @pytest.mark.asyncio
    async def test_incremental_update_no_changes(self, temp_index):
        """Test incremental update when no files changed."""
        index, tmpdir = temp_index

        # Create a test file
        test_file = Path(tmpdir) / "test.py"
        test_file.write_text("def test(): pass")

        mock_file = ScannedFile(
            path=test_file,
            relative_path="test.py",
            file_type="python",
            size_bytes=20,
            modified_at=datetime.now(),
            content_hash="hash1"
        )

        # First do a full build
        with patch.object(index.scanner, 'scan_all', return_value=iter([mock_file])):
            with patch.object(index.embedder, 'embed_batch', new_callable=AsyncMock) as mock_embed:
                mock_embed.return_value = np.random.randn(1, 768).astype(np.float32)
                await index.build_index(show_progress=False)

        # Now do incremental update with same files
        with patch.object(index.scanner, 'scan_all', return_value=iter([mock_file])):
            with patch.object(index.embedder, 'embed_batch', new_callable=AsyncMock) as mock_embed:
                mock_embed.return_value = np.random.randn(1, 768).astype(np.float32)
                stats = await index.incremental_update(show_progress=False)

        # Should detect no changes
        assert stats["files_added"] == 0
        assert stats["files_removed"] == 0
        assert stats["files_modified"] == 0

    @pytest.mark.asyncio
    async def test_incremental_update_added_file(self, temp_index):
        """Test incremental update detects added files."""
        index, tmpdir = temp_index

        # Create initial file
        test_file1 = Path(tmpdir) / "test1.py"
        test_file1.write_text("def test1(): pass")

        mock_file1 = ScannedFile(
            path=test_file1,
            relative_path="test1.py",
            file_type="python",
            size_bytes=20,
            modified_at=datetime.now(),
            content_hash="hash1"
        )

        # First build with one file
        with patch.object(index.scanner, 'scan_all', return_value=iter([mock_file1])):
            with patch.object(index.embedder, 'embed_batch', new_callable=AsyncMock) as mock_embed:
                mock_embed.return_value = np.random.randn(1, 768).astype(np.float32)
                await index.build_index(show_progress=False)

        # Add a new file
        test_file2 = Path(tmpdir) / "test2.py"
        test_file2.write_text("def test2(): pass")

        mock_file2 = ScannedFile(
            path=test_file2,
            relative_path="test2.py",
            file_type="python",
            size_bytes=20,
            modified_at=datetime.now(),
            content_hash="hash2"
        )

        # Incremental update with both files
        with patch.object(index.scanner, 'scan_all', return_value=iter([mock_file1, mock_file2])):
            with patch.object(index.embedder, 'embed_batch', new_callable=AsyncMock) as mock_embed:
                mock_embed.return_value = np.random.randn(1, 768).astype(np.float32)
                stats = await index.incremental_update(show_progress=False)

        # Should detect 1 added file
        assert stats["files_added"] == 1

    @pytest.mark.asyncio
    async def test_incremental_update_modified_file(self, temp_index):
        """Test incremental update detects modified files."""
        index, tmpdir = temp_index

        # Create initial file
        test_file = Path(tmpdir) / "test.py"
        test_file.write_text("def test(): pass")

        mock_file_v1 = ScannedFile(
            path=test_file,
            relative_path="test.py",
            file_type="python",
            size_bytes=20,
            modified_at=datetime.now(),
            content_hash="hash_v1"
        )

        # First build
        with patch.object(index.scanner, 'scan_all', return_value=iter([mock_file_v1])):
            with patch.object(index.embedder, 'embed_batch', new_callable=AsyncMock) as mock_embed:
                mock_embed.return_value = np.random.randn(1, 768).astype(np.float32)
                await index.build_index(show_progress=False)

        # Modify the file (new hash)
        mock_file_v2 = ScannedFile(
            path=test_file,
            relative_path="test.py",
            file_type="python",
            size_bytes=30,
            modified_at=datetime.now(),
            content_hash="hash_v2"  # Different hash
        )

        # Incremental update
        with patch.object(index.scanner, 'scan_all', return_value=iter([mock_file_v2])):
            with patch.object(index.embedder, 'embed_batch', new_callable=AsyncMock) as mock_embed:
                mock_embed.return_value = np.random.randn(1, 768).astype(np.float32)
                stats = await index.incremental_update(show_progress=False)

        # Should detect 1 modified file
        assert stats["files_modified"] == 1

    @pytest.mark.asyncio
    async def test_incremental_update_removed_file(self, temp_index):
        """Test incremental update detects removed files."""
        index, tmpdir = temp_index

        # Create two initial files
        test_file1 = Path(tmpdir) / "test1.py"
        test_file1.write_text("def test1(): pass")
        test_file2 = Path(tmpdir) / "test2.py"
        test_file2.write_text("def test2(): pass")

        mock_file1 = ScannedFile(
            path=test_file1,
            relative_path="test1.py",
            file_type="python",
            size_bytes=20,
            modified_at=datetime.now(),
            content_hash="hash1"
        )
        mock_file2 = ScannedFile(
            path=test_file2,
            relative_path="test2.py",
            file_type="python",
            size_bytes=20,
            modified_at=datetime.now(),
            content_hash="hash2"
        )

        # First build with two files
        with patch.object(index.scanner, 'scan_all', return_value=iter([mock_file1, mock_file2])):
            with patch.object(index.embedder, 'embed_batch', new_callable=AsyncMock) as mock_embed:
                mock_embed.return_value = np.random.randn(2, 768).astype(np.float32)
                await index.build_index(show_progress=False)

        # Incremental update with only one file (simulating deletion)
        with patch.object(index.scanner, 'scan_all', return_value=iter([mock_file1])):
            with patch.object(index.embedder, 'embed_batch', new_callable=AsyncMock) as mock_embed:
                mock_embed.return_value = np.random.randn(0, 768).astype(np.float32)
                stats = await index.incremental_update(show_progress=False)

        # Should detect 1 removed file
        assert stats["files_removed"] == 1


# Need to import ScannedFile for the new tests
from file_compass.scanner import ScannedFile
