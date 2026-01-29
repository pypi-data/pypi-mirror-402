"""
File Compass - Indexer Module
HNSW index management with SQLite metadata storage.
"""

import sqlite3
import asyncio
import hnswlib
import numpy as np
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import logging
import json

from . import DEFAULT_DB_PATH, DEFAULT_INDEX_PATH, DEFAULT_SQLITE_PATH
from .config import get_config
from .embedder import Embedder
from .scanner import FileScanner, ScannedFile
from .chunker import FileChunker, Chunk
from .merkle import MerkleTree, compute_chunk_hash

logger = logging.getLogger(__name__)

# Default path for Merkle tree state
DEFAULT_MERKLE_PATH = DEFAULT_DB_PATH / "merkle_state.json"


@dataclass
class SearchResult:
    """Result from semantic search."""
    path: str
    relative_path: str
    file_type: str
    chunk_type: str
    chunk_name: Optional[str]
    line_start: int
    line_end: int
    preview: str
    relevance: float
    modified_at: datetime
    git_tracked: bool


class FileIndex:
    """
    HNSW-based semantic file index with SQLite metadata.
    """

    def __init__(
        self,
        db_path: Optional[Path] = None,
        index_path: Optional[Path] = None,
        sqlite_path: Optional[Path] = None,
        merkle_path: Optional[Path] = None
    ):
        config = get_config()

        self.db_path = db_path or DEFAULT_DB_PATH
        self.index_path = index_path or DEFAULT_INDEX_PATH
        self.sqlite_path = sqlite_path or DEFAULT_SQLITE_PATH
        self.merkle_path = merkle_path or DEFAULT_MERKLE_PATH

        # HNSW config
        self.dim = config.embedding_dim
        self.M = config.hnsw_m
        self.ef_construction = config.hnsw_ef_construction
        self.ef_search = config.hnsw_ef_search
        self.max_elements = config.hnsw_max_elements
        self.space = config.hnsw_space

        # Components
        self.embedder = Embedder()
        self.scanner = FileScanner()
        self.chunker = FileChunker()

        # Index state
        self._index: Optional[hnswlib.Index] = None
        self._conn: Optional[sqlite3.Connection] = None
        self._id_to_chunk: Dict[int, Tuple[int, int]] = {}  # embedding_id -> (file_id, chunk_idx)
        self._merkle: Optional[MerkleTree] = None  # For incremental updates

    def _get_conn(self) -> sqlite3.Connection:
        """Get or create SQLite connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.sqlite_path))
            self._conn.row_factory = sqlite3.Row
            self._init_schema()
        return self._conn

    def _init_schema(self):
        """Initialize SQLite schema."""
        conn = self._conn
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                relative_path TEXT NOT NULL,
                file_type TEXT NOT NULL,
                size_bytes INTEGER,
                modified_at TIMESTAMP,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                content_hash TEXT,
                git_repo TEXT,
                is_git_tracked INTEGER DEFAULT 0,
                total_chunks INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                chunk_type TEXT,
                name TEXT,
                line_start INTEGER,
                line_end INTEGER,
                content_preview TEXT,
                token_count INTEGER,
                embedding_id INTEGER,
                FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS index_meta (
                key TEXT PRIMARY KEY,
                value TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_files_path ON files(path);
            CREATE INDEX IF NOT EXISTS idx_files_type ON files(file_type);
            CREATE INDEX IF NOT EXISTS idx_files_hash ON files(content_hash);
            CREATE INDEX IF NOT EXISTS idx_chunks_file ON chunks(file_id);
            CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON chunks(embedding_id);
        """)
        conn.commit()

    def _get_index(self) -> hnswlib.Index:
        """Get or create HNSW index."""
        if self._index is None:
            self._index = hnswlib.Index(space=self.space, dim=self.dim)

            if self.index_path.exists():
                logger.info(f"Loading existing index from {self.index_path}")
                self._index.load_index(str(self.index_path), max_elements=self.max_elements)
                self._index.set_ef(self.ef_search)
                self._load_id_mapping()
            else:
                logger.info("Creating new HNSW index")
                self._index.init_index(
                    max_elements=self.max_elements,
                    ef_construction=self.ef_construction,
                    M=self.M
                )
                self._index.set_ef(self.ef_search)

        return self._index

    def _load_id_mapping(self):
        """Load embedding_id -> (file_id, chunk_idx) mapping from SQLite."""
        conn = self._get_conn()
        cursor = conn.execute("""
            SELECT embedding_id, file_id, chunk_index
            FROM chunks
            WHERE embedding_id IS NOT NULL
        """)
        self._id_to_chunk = {
            row["embedding_id"]: (row["file_id"], row["chunk_index"])
            for row in cursor
        }
        logger.info(f"Loaded {len(self._id_to_chunk)} chunk mappings")

    def _save_index(self):
        """Persist HNSW index to disk."""
        if self._index is not None:
            self._index.save_index(str(self.index_path))
            logger.info(f"Saved index to {self.index_path}")

    async def build_index(
        self,
        directories: Optional[List[str]] = None,
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        Build or rebuild the complete index.

        Args:
            directories: Directories to index (uses config if not specified)
            show_progress: Print progress updates

        Returns:
            Statistics about the indexing process
        """
        start_time = datetime.now()

        if directories:
            self.scanner = FileScanner(directories=directories)

        # Clear existing data
        conn = self._get_conn()
        conn.execute("DELETE FROM chunks")
        conn.execute("DELETE FROM files")
        conn.commit()

        # Re-create HNSW index
        self._index = hnswlib.Index(space=self.space, dim=self.dim)
        self._index.init_index(
            max_elements=self.max_elements,
            ef_construction=self.ef_construction,
            M=self.M
        )
        self._index.set_ef(self.ef_search)
        self._id_to_chunk = {}

        # Scan and process files
        files_indexed = 0
        chunks_indexed = 0
        embedding_id = 0

        all_files = list(self.scanner.scan_all())
        total_files = len(all_files)

        if show_progress:
            print(f"Found {total_files} files to index")

        # Process in batches for embedding efficiency
        batch_size = 50
        all_texts = []
        all_metadata = []  # (file_id, chunk_idx, chunk)

        # Build Merkle tree for incremental updates
        merkle = MerkleTree()

        for i, scanned_file in enumerate(all_files):
            # Insert file record
            cursor = conn.execute("""
                INSERT INTO files (path, relative_path, file_type, size_bytes,
                                   modified_at, content_hash, git_repo, is_git_tracked)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(scanned_file.path),
                scanned_file.relative_path,
                scanned_file.file_type,
                scanned_file.size_bytes,
                scanned_file.modified_at.isoformat(),
                scanned_file.content_hash,
                scanned_file.git_repo,
                1 if scanned_file.is_git_tracked else 0
            ))
            file_id = cursor.lastrowid

            # Chunk the file
            try:
                chunks = self.chunker.chunk_file(scanned_file.path)
            except Exception as e:
                logger.warning(f"Failed to chunk {scanned_file.path}: {e}")
                chunks = []

            # Update total_chunks
            conn.execute(
                "UPDATE files SET total_chunks = ? WHERE id = ?",
                (len(chunks), file_id)
            )

            # Collect chunks for batch embedding
            chunk_hashes = []
            for chunk_idx, chunk in enumerate(chunks):
                # Create embedding text: filename + chunk content
                embed_text = f"File: {scanned_file.relative_path}\n{chunk.content}"
                all_texts.append(embed_text)
                all_metadata.append((file_id, chunk_idx, chunk))
                chunk_hashes.append(compute_chunk_hash(chunk.content))

            # Add to Merkle tree
            merkle.add_file(
                scanned_file.relative_path,
                scanned_file.content_hash,
                chunk_hashes,
                scanned_file.modified_at.timestamp()
            )

            files_indexed += 1

            if show_progress and (i + 1) % 100 == 0:
                print(f"  Scanned {i + 1}/{total_files} files...")

        conn.commit()

        if show_progress:
            print(f"Generating embeddings for {len(all_texts)} chunks...")

        # Generate embeddings in batches
        if all_texts:
            embeddings = await self.embedder.embed_batch(
                all_texts,
                batch_size=batch_size,
                show_progress=show_progress
            )

            # Add to HNSW and SQLite
            for idx, (file_id, chunk_idx, chunk) in enumerate(all_metadata):
                # Insert chunk record
                conn.execute("""
                    INSERT INTO chunks (file_id, chunk_index, chunk_type, name,
                                       line_start, line_end, content_preview,
                                       token_count, embedding_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    file_id,
                    chunk_idx,
                    chunk.chunk_type,
                    chunk.name,
                    chunk.line_start,
                    chunk.line_end,
                    chunk.preview,
                    chunk.token_estimate,
                    embedding_id
                ))

                # Add to HNSW
                self._index.add_items(
                    embeddings[idx:idx+1],
                    np.array([embedding_id])
                )
                self._id_to_chunk[embedding_id] = (file_id, chunk_idx)

                embedding_id += 1
                chunks_indexed += 1

            conn.commit()

        # Save index and Merkle tree
        self._save_index()
        merkle.save(self.merkle_path)

        # Update metadata
        duration = (datetime.now() - start_time).total_seconds()
        conn.execute(
            "INSERT OR REPLACE INTO index_meta (key, value) VALUES (?, ?)",
            ("last_build", datetime.now().isoformat())
        )
        conn.execute(
            "INSERT OR REPLACE INTO index_meta (key, value) VALUES (?, ?)",
            ("files_count", str(files_indexed))
        )
        conn.execute(
            "INSERT OR REPLACE INTO index_meta (key, value) VALUES (?, ?)",
            ("chunks_count", str(chunks_indexed))
        )
        conn.commit()

        stats = {
            "files_indexed": files_indexed,
            "chunks_indexed": chunks_indexed,
            "duration_seconds": duration,
            "index_path": str(self.index_path)
        }

        if show_progress:
            print(f"\nIndexing complete!")
            print(f"  Files: {files_indexed}")
            print(f"  Chunks: {chunks_indexed}")
            print(f"  Duration: {duration:.1f}s")

        return stats

    async def incremental_update(
        self,
        directories: Optional[List[str]] = None,
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        Incrementally update the index, only processing changed files.
        Uses Merkle tree for efficient change detection.

        Args:
            directories: Directories to scan (uses config if not specified)
            show_progress: Print progress updates

        Returns:
            Statistics about the update process
        """
        start_time = datetime.now()

        if directories:
            self.scanner = FileScanner(directories=directories)

        # Load existing Merkle tree state
        old_merkle = MerkleTree.load(self.merkle_path)
        if old_merkle is None:
            if show_progress:
                print("No existing index state found, doing full rebuild...")
            return await self.build_index(directories, show_progress)

        # Build new Merkle tree from current files
        new_merkle = MerkleTree()
        all_files = list(self.scanner.scan_all())

        for scanned_file in all_files:
            # Chunk to get chunk hashes
            try:
                chunks = self.chunker.chunk_file(scanned_file.path)
                chunk_hashes = [compute_chunk_hash(c.content) for c in chunks]
            except Exception:
                chunk_hashes = []

            new_merkle.add_file(
                scanned_file.relative_path,
                scanned_file.content_hash,
                chunk_hashes,
                scanned_file.modified_at.timestamp()
            )

        # Quick check - if root hashes match, no changes
        if not new_merkle.diff_quick(old_merkle):
            duration = (datetime.now() - start_time).total_seconds()
            if show_progress:
                print(f"No changes detected ({duration:.1f}s)")
            return {
                "files_added": 0,
                "files_removed": 0,
                "files_modified": 0,
                "chunks_added": 0,
                "duration_seconds": duration
            }

        # Find what changed
        added, removed, modified = new_merkle.diff(old_merkle)

        if show_progress:
            print(f"Incremental update: {len(added)} added, {len(removed)} removed, {len(modified)} modified")

        # Load existing index
        conn = self._get_conn()
        index = self._get_index()

        # Get next embedding ID
        result = conn.execute("SELECT MAX(embedding_id) FROM chunks").fetchone()
        next_embedding_id = (result[0] or 0) + 1

        files_processed = 0
        chunks_added = 0

        # Process removed files
        for rel_path in removed:
            # Find file in DB and remove
            row = conn.execute(
                "SELECT id FROM files WHERE relative_path = ?",
                (rel_path,)
            ).fetchone()
            if row:
                file_id = row[0]
                # Get embedding IDs to remove from HNSW
                # Note: hnswlib doesn't support deletion easily, so we mark them
                # For now, we'll remove from SQLite but leave in HNSW (orphaned)
                conn.execute("DELETE FROM chunks WHERE file_id = ?", (file_id,))
                conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
                files_processed += 1

        # Process added and modified files
        files_to_embed = list(added | modified)
        all_texts = []
        all_metadata = []

        # Create mapping from relative path to scanned file
        scanned_map = {sf.relative_path: sf for sf in all_files}

        for rel_path in files_to_embed:
            scanned_file = scanned_map.get(rel_path)
            if not scanned_file:
                continue

            # If modified, remove old entry first
            if rel_path in modified:
                row = conn.execute(
                    "SELECT id FROM files WHERE relative_path = ?",
                    (rel_path,)
                ).fetchone()
                if row:
                    conn.execute("DELETE FROM chunks WHERE file_id = ?", (row[0],))
                    conn.execute("DELETE FROM files WHERE id = ?", (row[0],))

            # Insert new file record
            cursor = conn.execute("""
                INSERT INTO files (path, relative_path, file_type, size_bytes,
                                   modified_at, content_hash, git_repo, is_git_tracked)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(scanned_file.path),
                scanned_file.relative_path,
                scanned_file.file_type,
                scanned_file.size_bytes,
                scanned_file.modified_at.isoformat(),
                scanned_file.content_hash,
                scanned_file.git_repo,
                1 if scanned_file.is_git_tracked else 0
            ))
            file_id = cursor.lastrowid

            # Chunk the file
            try:
                chunks = self.chunker.chunk_file(scanned_file.path)
            except Exception as e:
                logger.warning(f"Failed to chunk {scanned_file.path}: {e}")
                chunks = []

            conn.execute(
                "UPDATE files SET total_chunks = ? WHERE id = ?",
                (len(chunks), file_id)
            )

            # Collect for batch embedding
            for chunk_idx, chunk in enumerate(chunks):
                embed_text = f"File: {scanned_file.relative_path}\n{chunk.content}"
                all_texts.append(embed_text)
                all_metadata.append((file_id, chunk_idx, chunk))

            files_processed += 1

        conn.commit()

        # Generate embeddings for new/modified chunks
        if all_texts:
            if show_progress:
                print(f"Generating embeddings for {len(all_texts)} chunks...")

            embeddings = await self.embedder.embed_batch(
                all_texts,
                show_progress=show_progress
            )

            # Add to HNSW and SQLite
            for idx, (file_id, chunk_idx, chunk) in enumerate(all_metadata):
                embedding_id = next_embedding_id + idx

                conn.execute("""
                    INSERT INTO chunks (file_id, chunk_index, chunk_type, name,
                                       line_start, line_end, content_preview,
                                       token_count, embedding_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    file_id,
                    chunk_idx,
                    chunk.chunk_type,
                    chunk.name,
                    chunk.line_start,
                    chunk.line_end,
                    chunk.preview,
                    chunk.token_estimate,
                    embedding_id
                ))

                # Add to HNSW (incremental)
                index.add_items(
                    embeddings[idx:idx+1],
                    np.array([embedding_id])
                )
                self._id_to_chunk[embedding_id] = (file_id, chunk_idx)

                chunks_added += 1

            conn.commit()

        # Save index and Merkle state
        self._save_index()
        new_merkle.save(self.merkle_path)

        # Update metadata
        duration = (datetime.now() - start_time).total_seconds()
        conn.execute(
            "INSERT OR REPLACE INTO index_meta (key, value) VALUES (?, ?)",
            ("last_update", datetime.now().isoformat())
        )
        conn.commit()

        stats = {
            "files_added": len(added),
            "files_removed": len(removed),
            "files_modified": len(modified),
            "chunks_added": chunks_added,
            "duration_seconds": duration
        }

        if show_progress:
            print(f"\nIncremental update complete!")
            print(f"  Added: {len(added)}, Removed: {len(removed)}, Modified: {len(modified)}")
            print(f"  New chunks: {chunks_added}")
            print(f"  Duration: {duration:.1f}s")

        return stats

    async def search(
        self,
        query: str,
        top_k: int = 10,
        file_types: Optional[List[str]] = None,
        directory: Optional[str] = None,
        git_only: bool = False,
        min_relevance: float = 0.3
    ) -> List[SearchResult]:
        """
        Search the index for relevant files/chunks.

        Args:
            query: Search query
            top_k: Number of results to return
            file_types: Filter by file types (e.g., ["python", "markdown"])
            directory: Filter by directory path prefix
            git_only: Only return git-tracked files
            min_relevance: Minimum relevance score (0-1)

        Returns:
            List of SearchResult objects
        """
        index = self._get_index()
        conn = self._get_conn()

        if index.get_current_count() == 0:
            logger.warning("Index is empty, no results to return")
            return []

        # Generate query embedding
        query_embedding = await self.embedder.embed_query(query)

        # Search HNSW (get more candidates for filtering)
        k_search = min(top_k * 5, index.get_current_count())
        labels, distances = index.knn_query(
            query_embedding.reshape(1, -1),
            k=k_search
        )

        # Convert distances to similarities (hnswlib returns 1-cosine for cosine space)
        similarities = 1 - distances[0]

        # Build results with filtering
        results = []

        for embedding_id, similarity in zip(labels[0], similarities):
            if similarity < min_relevance:
                continue

            if embedding_id not in self._id_to_chunk:
                continue

            file_id, chunk_idx = self._id_to_chunk[embedding_id]

            # Fetch file and chunk info
            row = conn.execute("""
                SELECT f.*, c.chunk_type, c.name as chunk_name,
                       c.line_start, c.line_end, c.content_preview
                FROM files f
                JOIN chunks c ON c.file_id = f.id
                WHERE f.id = ? AND c.chunk_index = ?
            """, (file_id, chunk_idx)).fetchone()

            if not row:
                continue

            # Apply filters
            if file_types and row["file_type"] not in file_types:
                continue

            if directory and not row["path"].startswith(directory):
                continue

            if git_only and not row["is_git_tracked"]:
                continue

            results.append(SearchResult(
                path=row["path"],
                relative_path=row["relative_path"],
                file_type=row["file_type"],
                chunk_type=row["chunk_type"],
                chunk_name=row["chunk_name"],
                line_start=row["line_start"],
                line_end=row["line_end"],
                preview=row["content_preview"],
                relevance=float(similarity),
                modified_at=datetime.fromisoformat(row["modified_at"]),
                git_tracked=bool(row["is_git_tracked"])
            ))

            if len(results) >= top_k:
                break

        return results

    def get_status(self) -> Dict[str, Any]:
        """Get index status and statistics."""
        conn = self._get_conn()

        files_count = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        chunks_count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]

        # Get last build time
        row = conn.execute(
            "SELECT value FROM index_meta WHERE key = 'last_build'"
        ).fetchone()
        last_build = row[0] if row else None

        # Get file type distribution
        type_dist = {}
        for row in conn.execute(
            "SELECT file_type, COUNT(*) as cnt FROM files GROUP BY file_type"
        ):
            type_dist[row["file_type"]] = row["cnt"]

        return {
            "files_indexed": files_count,
            "chunks_indexed": chunks_count,
            "last_build": last_build,
            "index_path": str(self.index_path),
            "index_size_mb": self.index_path.stat().st_size / 1024 / 1024 if self.index_path.exists() else 0,
            "file_types": type_dist
        }

    async def close(self):
        """Clean up resources."""
        await self.embedder.close()
        if self._conn:
            self._conn.close()
            self._conn = None


# Module-level singleton
_index: Optional[FileIndex] = None


def get_index() -> FileIndex:
    """Get or create global FileIndex instance."""
    global _index
    if _index is None:
        _index = FileIndex()
    return _index


if __name__ == "__main__":
    # Test indexing
    async def test():
        index = FileIndex()

        print("Building index...")
        stats = await index.build_index(
            directories=["F:/AI/mcp-tool-shop/file_compass"],
            show_progress=True
        )

        print("\nTesting search...")
        results = await index.search("embedding generation", top_k=5)

        for r in results:
            print(f"\n  {r.relative_path}")
            print(f"    {r.chunk_type}: {r.chunk_name or 'unnamed'}")
            print(f"    Lines {r.line_start}-{r.line_end}, relevance: {r.relevance:.3f}")
            print(f"    Preview: {r.preview[:100]}...")

        await index.close()

    asyncio.run(test())
