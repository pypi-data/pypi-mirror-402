"""
Tests for file_compass.quick_index module.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

from file_compass.quick_index import QuickIndex, QuickResult
from file_compass.scanner import ScannedFile


class TestQuickIndex:
    """Tests for QuickIndex class."""

    def setup_method(self):
        """Create a temporary directory and index for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_quick.db"
        self.index = QuickIndex(db_path=self.db_path)

        # Create some test files
        self.test_files_dir = Path(self.temp_dir) / "code"
        self.test_files_dir.mkdir()

        # Python file with functions
        (self.test_files_dir / "utils.py").write_text("""
def calculate_total(items):
    return sum(items)

def format_output(data):
    return str(data)

class DataProcessor:
    def process(self):
        pass
""")

        # JavaScript file
        (self.test_files_dir / "helpers.js").write_text("""
function formatDate(date) {
    return date.toISOString();
}

export const parseJSON = (str) => {
    return JSON.parse(str);
}

class Helper {
    constructor() {}
}
""")

        # Config file
        (self.test_files_dir / "config.json").write_text('{"debug": true}')

        # Create mock scanned files
        self.mock_scanned_files = [
            ScannedFile(
                path=self.test_files_dir / "utils.py",
                relative_path="utils.py",
                file_type="python",
                size_bytes=200,
                modified_at=datetime.now(),
                content_hash="abc123",
                git_repo=None,
                is_git_tracked=False
            ),
            ScannedFile(
                path=self.test_files_dir / "helpers.js",
                relative_path="helpers.js",
                file_type="javascript",
                size_bytes=300,
                modified_at=datetime.now(),
                content_hash="def456",
                git_repo=None,
                is_git_tracked=False
            ),
            ScannedFile(
                path=self.test_files_dir / "config.json",
                relative_path="config.json",
                file_type="json",
                size_bytes=20,
                modified_at=datetime.now(),
                content_hash="ghi789",
                git_repo=None,
                is_git_tracked=False
            ),
        ]

    def teardown_method(self):
        """Clean up test files."""
        import shutil
        self.index.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _mock_scan_all(self):
        """Mock scan_all to return our test files."""
        return iter(self.mock_scanned_files)

    @pytest.mark.asyncio
    async def test_build_quick_index(self):
        """Test building quick index."""
        # Mock the scanner to return our test files
        with patch.object(self.index.scanner, 'scan_all', self._mock_scan_all):
            stats = await self.index.build_quick_index(
                directories=[str(self.test_files_dir)],
                extract_symbols=True
            )

        assert stats["files_indexed"] == 3
        assert stats["symbols_extracted"] > 0
        assert stats["duration_seconds"] >= 0

    @pytest.mark.asyncio
    async def test_search_by_filename(self):
        """Test searching by filename."""
        with patch.object(self.index.scanner, 'scan_all', self._mock_scan_all):
            await self.index.build_quick_index(
                directories=[str(self.test_files_dir)]
            )

        results = self.index.search("utils")

        assert len(results) > 0
        assert any("utils" in r.relative_path.lower() for r in results)

    @pytest.mark.asyncio
    async def test_search_by_symbol(self):
        """Test searching by function/class name."""
        with patch.object(self.index.scanner, 'scan_all', self._mock_scan_all):
            await self.index.build_quick_index(
                directories=[str(self.test_files_dir)]
            )

        results = self.index.search("calculate")

        assert len(results) > 0
        symbol_matches = [r for r in results if r.match_type == "symbol"]
        assert len(symbol_matches) > 0
        assert any("calculate" in r.match_text.lower() for r in symbol_matches)

    @pytest.mark.asyncio
    async def test_search_class(self):
        """Test searching for class names."""
        with patch.object(self.index.scanner, 'scan_all', self._mock_scan_all):
            await self.index.build_quick_index(
                directories=[str(self.test_files_dir)]
            )

        results = self.index.search("DataProcessor")

        assert len(results) > 0
        assert any("DataProcessor" in r.match_text for r in results)

    @pytest.mark.asyncio
    async def test_search_with_file_type_filter(self):
        """Test filtering by file type."""
        with patch.object(self.index.scanner, 'scan_all', self._mock_scan_all):
            await self.index.build_quick_index(
                directories=[str(self.test_files_dir)]
            )

        # Search only Python files
        results = self.index.search("format", file_types=["python"])

        # Should find format_output but not formatDate
        for r in results:
            assert r.file_type == "python"

    @pytest.mark.asyncio
    async def test_search_line_numbers(self):
        """Test that symbol search returns line numbers."""
        with patch.object(self.index.scanner, 'scan_all', self._mock_scan_all):
            await self.index.build_quick_index(
                directories=[str(self.test_files_dir)]
            )

        results = self.index.search("calculate_total")

        symbol_results = [r for r in results if r.match_type == "symbol"]
        assert len(symbol_results) > 0
        # Should have line number
        assert any(r.line_number is not None for r in symbol_results)

    @pytest.mark.asyncio
    async def test_get_status(self):
        """Test getting index status."""
        with patch.object(self.index.scanner, 'scan_all', self._mock_scan_all):
            await self.index.build_quick_index(
                directories=[str(self.test_files_dir)]
            )

        status = self.index.get_status()

        assert "files_indexed" in status
        assert "symbols_indexed" in status
        assert "file_types" in status
        assert status["files_indexed"] > 0

    def test_extract_symbols_python(self):
        """Test Python symbol extraction."""
        symbols = self.index._extract_symbols_fast(self.test_files_dir / "utils.py")

        names = [s[0] for s in symbols]
        types = [s[1] for s in symbols]

        assert "calculate_total" in names
        assert "format_output" in names
        assert "DataProcessor" in names
        assert "function" in types
        assert "class" in types

    def test_extract_symbols_javascript(self):
        """Test JavaScript symbol extraction."""
        symbols = self.index._extract_symbols_fast(self.test_files_dir / "helpers.js")

        names = [s[0] for s in symbols]

        assert "formatDate" in names
        assert "parseJSON" in names
        assert "Helper" in names

    @pytest.mark.asyncio
    async def test_search_deduplicates(self):
        """Test that search results are deduplicated."""
        with patch.object(self.index.scanner, 'scan_all', self._mock_scan_all):
            await self.index.build_quick_index(
                directories=[str(self.test_files_dir)]
            )

        results = self.index.search("format")

        # Check for duplicates
        seen = set()
        for r in results:
            key = (r.path, r.line_number)
            assert key not in seen, f"Duplicate result: {key}"
            seen.add(key)

    @pytest.mark.asyncio
    async def test_search_scoring(self):
        """Test that exact matches score higher."""
        with patch.object(self.index.scanner, 'scan_all', self._mock_scan_all):
            await self.index.build_quick_index(
                directories=[str(self.test_files_dir)]
            )

        results = self.index.search("utils")

        # Results should be sorted by score (highest first)
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_quick_result_dataclass(self):
        """Test QuickResult dataclass."""
        result = QuickResult(
            path="/test/file.py",
            relative_path="file.py",
            file_type="python",
            match_type="symbol",
            match_text="function my_func",
            line_number=42,
            modified_at=datetime.now(),
            score=0.85
        )

        assert result.path == "/test/file.py"
        assert result.match_type == "symbol"
        assert result.line_number == 42
        assert result.score == 0.85


class TestQuickIndexEdgeCases:
    """Edge case tests for QuickIndex."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_quick.db"
        self.index = QuickIndex(db_path=self.db_path)

    def teardown_method(self):
        import shutil
        self.index.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_search_empty_index(self):
        """Test searching empty index."""
        results = self.index.search("anything")
        assert results == []

    def test_search_no_matches(self):
        """Test search with no matches."""
        # Add a file manually to the index
        conn = self.index._get_conn()
        conn.execute("""
            INSERT INTO files (path, relative_path, file_type, modified_at, indexed_at)
            VALUES (?, ?, ?, ?, ?)
        """, ("/test/foo.py", "foo.py", "python", datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()

        results = self.index.search("zzzznonexistent")
        assert len(results) == 0

    def test_extract_symbols_nonexistent_file(self):
        """Test symbol extraction on nonexistent file."""
        symbols = self.index._extract_symbols_fast(Path("/nonexistent/file.py"))
        assert symbols == []

    def test_extract_symbols_binary_file(self):
        """Test symbol extraction on binary file."""
        binary_file = Path(self.temp_dir) / "binary.py"
        binary_file.write_bytes(b'\x00\x01\x02\x03')

        symbols = self.index._extract_symbols_fast(binary_file)
        # Should not crash, may return empty or partial
        assert isinstance(symbols, list)

    def test_search_with_recent_days_invalid(self):
        """Test search handles invalid recent_days gracefully."""
        conn = self.index._get_conn()
        conn.execute("""
            INSERT INTO files (path, relative_path, file_type, modified_at, indexed_at)
            VALUES (?, ?, ?, ?, ?)
        """, ("/test/foo.py", "foo.py", "python", datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()

        # Negative recent_days should be treated as None (no filter)
        results = self.index.search("foo", recent_days=-5)
        assert isinstance(results, list)

        # Zero recent_days should also be treated as None
        results = self.index.search("foo", recent_days=0)
        assert isinstance(results, list)

    def test_search_with_recent_days_valid(self):
        """Test search with valid recent_days filter."""
        conn = self.index._get_conn()
        conn.execute("""
            INSERT INTO files (path, relative_path, file_type, modified_at, indexed_at)
            VALUES (?, ?, ?, ?, ?)
        """, ("/test/recent.py", "recent.py", "python", datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()

        # Search with 7 day filter - recent file should be found
        results = self.index.search("recent", recent_days=7)
        assert len(results) > 0

    def test_extract_symbols_rust(self):
        """Test Rust symbol extraction."""
        rust_file = Path(self.temp_dir) / "test.rs"
        rust_file.write_text("""
pub fn process_data(input: &str) -> String {
    input.to_string()
}

pub struct Config {
    name: String,
}

async fn async_handler() {
    // async function
}
""")
        symbols = self.index._extract_symbols_fast(rust_file)
        names = [s[0] for s in symbols]

        assert "process_data" in names
        assert "Config" in names
        assert "async_handler" in names

    def test_extract_symbols_go(self):
        """Test Go symbol extraction."""
        go_file = Path(self.temp_dir) / "test.go"
        go_file.write_text("""
func processData(input string) string {
    return input
}

type Config struct {
    Name string
}

func (c *Config) GetName() string {
    return c.Name
}
""")
        symbols = self.index._extract_symbols_fast(go_file)
        names = [s[0] for s in symbols]

        assert "processData" in names
        assert "Config" in names
        assert "GetName" in names

    def test_search_with_file_types_multiple(self):
        """Test search with multiple file type filters."""
        conn = self.index._get_conn()
        conn.execute("""
            INSERT INTO files (path, relative_path, file_type, modified_at, indexed_at)
            VALUES (?, ?, ?, ?, ?)
        """, ("/test/app.py", "app.py", "python", datetime.now().isoformat(), datetime.now().isoformat()))
        conn.execute("""
            INSERT INTO files (path, relative_path, file_type, modified_at, indexed_at)
            VALUES (?, ?, ?, ?, ?)
        """, ("/test/app.js", "app.js", "javascript", datetime.now().isoformat(), datetime.now().isoformat()))
        conn.execute("""
            INSERT INTO files (path, relative_path, file_type, modified_at, indexed_at)
            VALUES (?, ?, ?, ?, ?)
        """, ("/test/app.rs", "app.rs", "rust", datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()

        # Search only Python and JavaScript
        results = self.index.search("app", file_types=["python", "javascript"])

        file_types_found = {r.file_type for r in results}
        assert "rust" not in file_types_found
        assert len(results) >= 2

    def test_close_and_reopen(self):
        """Test closing and reopening the index."""
        conn = self.index._get_conn()
        conn.execute("""
            INSERT INTO files (path, relative_path, file_type, modified_at, indexed_at)
            VALUES (?, ?, ?, ?, ?)
        """, ("/test/test.py", "test.py", "python", datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()

        # Close the index
        self.index.close()
        assert self.index._conn is None

        # Reopen and search
        results = self.index.search("test")
        assert len(results) > 0
