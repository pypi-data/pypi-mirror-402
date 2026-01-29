"""
File Compass - Quick Index Module
Provides instant search capability while full semantic index builds.

Phases:
1. Filename index (instant) - Search by file/function names
2. Recent files (fast) - Semantic search on recently modified files
3. Full index (slow) - Complete semantic search
"""

import sqlite3
import asyncio
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Generator
from datetime import datetime, timedelta
import logging
import re
import fnmatch

from . import DEFAULT_DB_PATH
from .config import get_config
from .scanner import FileScanner, ScannedFile

logger = logging.getLogger(__name__)

# Quick index database path
QUICK_INDEX_PATH = DEFAULT_DB_PATH / "quick_index.db"


@dataclass
class QuickResult:
    """Result from quick (non-semantic) search."""
    path: str
    relative_path: str
    file_type: str
    match_type: str  # "filename", "symbol", "recent", "content"
    match_text: str  # What matched
    line_number: Optional[int]
    modified_at: datetime
    score: float  # Relevance score (0-1)


class QuickIndex:
    """
    Fast file index for instant search while semantic index builds.

    Provides three levels of search:
    1. Filename/path matching (instant)
    2. Symbol extraction (fast - scans file headers)
    3. Content grep (slower - searches file contents)
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or QUICK_INDEX_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self.scanner = FileScanner()

    def _get_conn(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            self._init_schema()
        return self._conn

    def _init_schema(self):
        """Initialize quick index schema."""
        conn = self._conn
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                relative_path TEXT NOT NULL,
                file_type TEXT NOT NULL,
                size_bytes INTEGER,
                modified_at TEXT,
                indexed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS symbols (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                symbol_type TEXT NOT NULL,
                line_number INTEGER,
                FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_files_path ON files(path);
            CREATE INDEX IF NOT EXISTS idx_files_relative ON files(relative_path);
            CREATE INDEX IF NOT EXISTS idx_files_modified ON files(modified_at DESC);
            CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name);
            CREATE INDEX IF NOT EXISTS idx_symbols_file ON symbols(file_id);
        """)
        conn.commit()

    async def build_quick_index(
        self,
        directories: Optional[List[str]] = None,
        extract_symbols: bool = True,
        show_progress: bool = False
    ) -> Dict[str, Any]:
        """
        Build quick index (filename + symbols).

        This is FAST - typically completes in 2-10 seconds for large codebases.

        Args:
            directories: Directories to scan
            extract_symbols: Whether to extract function/class names
            show_progress: Show progress output

        Returns:
            Statistics about the indexing
        """
        config = get_config()
        dirs = directories or config.directories

        start_time = datetime.now()
        conn = self._get_conn()

        # Clear existing data
        conn.execute("DELETE FROM symbols")
        conn.execute("DELETE FROM files")
        conn.commit()

        files_indexed = 0
        symbols_extracted = 0

        if show_progress:
            print("Building quick index (filename + symbols)...")

        for scanned_file in self.scanner.scan_all():
            # Insert file record
            cursor = conn.execute("""
                INSERT INTO files (path, relative_path, file_type, size_bytes, modified_at, indexed_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                str(scanned_file.path),
                scanned_file.relative_path,
                scanned_file.file_type,
                scanned_file.size_bytes,
                scanned_file.modified_at.isoformat(),
                datetime.now().isoformat()
            ))
            file_id = cursor.lastrowid
            files_indexed += 1

            # Extract symbols if requested
            if extract_symbols:
                symbols = self._extract_symbols_fast(scanned_file.path)
                for sym_name, sym_type, line_num in symbols:
                    conn.execute("""
                        INSERT INTO symbols (file_id, name, symbol_type, line_number)
                        VALUES (?, ?, ?, ?)
                    """, (file_id, sym_name, sym_type, line_num))
                    symbols_extracted += 1

            if show_progress and files_indexed % 500 == 0:
                print(f"  Indexed {files_indexed} files...")

        conn.commit()

        duration = (datetime.now() - start_time).total_seconds()

        if show_progress:
            print(f"Quick index complete: {files_indexed} files, {symbols_extracted} symbols in {duration:.1f}s")

        return {
            "files_indexed": files_indexed,
            "symbols_extracted": symbols_extracted,
            "duration_seconds": duration
        }

    def _extract_symbols_fast(self, path: Path) -> List[tuple]:
        """
        Fast symbol extraction - only reads first 200 lines of file.

        Returns list of (name, type, line_number) tuples.
        """
        symbols = []

        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            lines = content.split("\n")[:200]  # Only first 200 lines

            suffix = path.suffix.lower()

            if suffix == ".py":
                for i, line in enumerate(lines, 1):
                    # Function
                    match = re.match(r'^\s*(?:async\s+)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)', line)
                    if match:
                        symbols.append((match.group(1), "function", i))
                    # Class
                    match = re.match(r'^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)', line)
                    if match:
                        symbols.append((match.group(1), "class", i))

            elif suffix in (".js", ".ts", ".jsx", ".tsx"):
                for i, line in enumerate(lines, 1):
                    # Function
                    match = re.match(r'^\s*(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z_][a-zA-Z0-9_]*)', line)
                    if match:
                        symbols.append((match.group(1), "function", i))
                    # Class
                    match = re.match(r'^\s*(?:export\s+)?class\s+([a-zA-Z_][a-zA-Z0-9_]*)', line)
                    if match:
                        symbols.append((match.group(1), "class", i))
                    # Const arrow function
                    match = re.match(r'^\s*(?:export\s+)?const\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?:async\s+)?\(', line)
                    if match:
                        symbols.append((match.group(1), "function", i))

            elif suffix in (".rs",):
                for i, line in enumerate(lines, 1):
                    match = re.match(r'^\s*(?:pub\s+)?(?:async\s+)?fn\s+([a-zA-Z_][a-zA-Z0-9_]*)', line)
                    if match:
                        symbols.append((match.group(1), "function", i))
                    match = re.match(r'^\s*(?:pub\s+)?struct\s+([a-zA-Z_][a-zA-Z0-9_]*)', line)
                    if match:
                        symbols.append((match.group(1), "struct", i))

            elif suffix == ".go":
                for i, line in enumerate(lines, 1):
                    match = re.match(r'^\s*func\s+(?:\([^)]+\)\s+)?([a-zA-Z_][a-zA-Z0-9_]*)', line)
                    if match:
                        symbols.append((match.group(1), "function", i))
                    match = re.match(r'^\s*type\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+struct', line)
                    if match:
                        symbols.append((match.group(1), "struct", i))

        except Exception as e:
            logger.debug(f"Symbol extraction failed for {path}: {e}")

        return symbols

    def search(
        self,
        query: str,
        top_k: int = 20,
        file_types: Optional[List[str]] = None,
        include_symbols: bool = True,
        recent_days: Optional[int] = None
    ) -> List[QuickResult]:
        """
        Search the quick index.

        Searches in order of relevance:
        1. Exact filename matches
        2. Symbol name matches
        3. Filename contains query
        4. Path contains query

        Args:
            query: Search query
            top_k: Max results
            file_types: Filter by file type
            include_symbols: Search symbol names
            recent_days: Only search files modified in last N days

        Returns:
            List of QuickResult objects
        """
        conn = self._get_conn()
        results = []
        query_lower = query.lower()
        query_words = query_lower.split()

        # Build date filter with parameterized query (security fix)
        date_filter_sql = ""
        date_filter_params = []
        if recent_days:
            # Validate recent_days is a positive integer
            if not isinstance(recent_days, int) or recent_days <= 0:
                recent_days = None
            else:
                cutoff = (datetime.now() - timedelta(days=recent_days)).isoformat()
                date_filter_sql = " AND modified_at >= ?"
                date_filter_params = [cutoff]

        # 1. Search filenames (exact match gets highest score)
        for word in query_words:
            # Build query with optional type filter
            if file_types:
                placeholders = ",".join("?" * len(file_types))
                query_sql = f"""
                    SELECT path, relative_path, file_type, modified_at
                    FROM files
                    WHERE relative_path LIKE ?
                    AND file_type IN ({placeholders})
                    {date_filter_sql}
                    LIMIT ?
                """
                params = [f"%{word}%"] + list(file_types) + date_filter_params + [top_k]
            else:
                query_sql = f"""
                    SELECT path, relative_path, file_type, modified_at
                    FROM files
                    WHERE relative_path LIKE ?
                    {date_filter_sql}
                    LIMIT ?
                """
                params = [f"%{word}%"] + date_filter_params + [top_k]

            rows = conn.execute(query_sql, params).fetchall()

            for row in rows:
                filename = Path(row["relative_path"]).stem.lower()
                # Higher score for exact filename match
                if word == filename:
                    score = 1.0
                elif word in filename:
                    score = 0.8
                else:
                    score = 0.5

                results.append(QuickResult(
                    path=row["path"],
                    relative_path=row["relative_path"],
                    file_type=row["file_type"],
                    match_type="filename",
                    match_text=row["relative_path"],
                    line_number=None,
                    modified_at=datetime.fromisoformat(row["modified_at"]),
                    score=score
                ))

        # 2. Search symbols
        if include_symbols:
            # Build symbol date filter (uses f.modified_at alias)
            sym_date_filter_sql = date_filter_sql.replace('modified_at', 'f.modified_at') if date_filter_sql else ""

            for word in query_words:
                # Build query with optional type filter
                if file_types:
                    placeholders = ",".join("?" * len(file_types))
                    sym_query = f"""
                        SELECT f.path, f.relative_path, f.file_type, f.modified_at,
                               s.name, s.symbol_type, s.line_number
                        FROM symbols s
                        JOIN files f ON s.file_id = f.id
                        WHERE s.name LIKE ?
                        AND f.file_type IN ({placeholders})
                        {sym_date_filter_sql}
                        LIMIT ?
                    """
                    sym_params = [f"%{word}%"] + list(file_types) + date_filter_params + [top_k]
                else:
                    sym_query = f"""
                        SELECT f.path, f.relative_path, f.file_type, f.modified_at,
                               s.name, s.symbol_type, s.line_number
                        FROM symbols s
                        JOIN files f ON s.file_id = f.id
                        WHERE s.name LIKE ?
                        {sym_date_filter_sql}
                        LIMIT ?
                    """
                    sym_params = [f"%{word}%"] + date_filter_params + [top_k]

                rows = conn.execute(sym_query, sym_params).fetchall()

                for row in rows:
                    sym_name = row["name"].lower()
                    # Higher score for exact symbol match
                    if word == sym_name:
                        score = 0.95
                    elif word in sym_name:
                        score = 0.75
                    else:
                        score = 0.5

                    results.append(QuickResult(
                        path=row["path"],
                        relative_path=row["relative_path"],
                        file_type=row["file_type"],
                        match_type="symbol",
                        match_text=f"{row['symbol_type']} {row['name']}",
                        line_number=row["line_number"],
                        modified_at=datetime.fromisoformat(row["modified_at"]),
                        score=score
                    ))

        # Deduplicate and sort by score
        seen = set()
        unique_results = []
        for r in sorted(results, key=lambda x: x.score, reverse=True):
            key = (r.path, r.line_number)
            if key not in seen:
                seen.add(key)
                unique_results.append(r)
                if len(unique_results) >= top_k:
                    break

        return unique_results

    def get_status(self) -> Dict[str, Any]:
        """Get quick index status."""
        conn = self._get_conn()

        files_count = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        symbols_count = conn.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]

        # Get file type distribution
        type_dist = {}
        for row in conn.execute(
            "SELECT file_type, COUNT(*) as cnt FROM files GROUP BY file_type"
        ):
            type_dist[row["file_type"]] = row["cnt"]

        return {
            "files_indexed": files_count,
            "symbols_indexed": symbols_count,
            "file_types": type_dist
        }

    def close(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None


# Singleton instance
_quick_index: Optional[QuickIndex] = None


def get_quick_index() -> QuickIndex:
    """Get singleton QuickIndex instance."""
    global _quick_index
    if _quick_index is None:
        _quick_index = QuickIndex()
    return _quick_index
