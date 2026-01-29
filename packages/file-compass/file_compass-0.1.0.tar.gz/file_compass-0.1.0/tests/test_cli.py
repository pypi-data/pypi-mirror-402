"""
Tests for file_compass.cli module.
Uses mocks to avoid actual indexing and searching.
"""

import pytest
import sys
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from io import StringIO

from file_compass.cli import cmd_index, cmd_search, cmd_status, cmd_scan, main


class TestCmdIndex:
    """Tests for cmd_index command."""

    def test_cmd_index_basic(self, capsys):
        """Test basic index command."""
        args = MagicMock()
        args.directories = None

        with patch('file_compass.cli.FileIndex') as MockIndex:
            mock_instance = MagicMock()
            MockIndex.return_value = mock_instance

            # Mock async build_index
            async def mock_build(**kwargs):
                return {
                    "files_indexed": 10,
                    "chunks_indexed": 50,
                    "duration_seconds": 1.5
                }
            mock_instance.build_index = mock_build
            mock_instance.close = AsyncMock()

            cmd_index(args)

            captured = capsys.readouterr()
            assert "File Compass - Building Index" in captured.out

    def test_cmd_index_with_directories(self, capsys):
        """Test index command with custom directories."""
        args = MagicMock()
        args.directories = ["/test/dir1", "/test/dir2"]

        with patch('file_compass.cli.FileIndex') as MockIndex:
            mock_instance = MagicMock()
            MockIndex.return_value = mock_instance

            async def mock_build(**kwargs):
                # Verify directories were passed
                assert kwargs.get("directories") == ["/test/dir1", "/test/dir2"]
                return {"files_indexed": 5, "chunks_indexed": 25, "duration_seconds": 0.5}

            mock_instance.build_index = mock_build
            mock_instance.close = AsyncMock()

            cmd_index(args)


class TestCmdSearch:
    """Tests for cmd_search command."""

    def test_cmd_search_no_results(self, capsys):
        """Test search with no results."""
        args = MagicMock()
        args.query = "nonexistent query"
        args.top_k = 10
        args.types = None
        args.directory = None
        args.git_only = False
        args.min_relevance = 0.3

        with patch('file_compass.cli.get_index') as mock_get_index:
            mock_index = MagicMock()
            mock_get_index.return_value = mock_index

            async def mock_search(**kwargs):
                return []
            mock_index.search = mock_search
            mock_index.close = AsyncMock()

            cmd_search(args)

            captured = capsys.readouterr()
            assert "No results found" in captured.out

    def test_cmd_search_with_results(self, capsys):
        """Test search with results."""
        args = MagicMock()
        args.query = "test query"
        args.top_k = 5
        args.types = None
        args.directory = None
        args.git_only = False
        args.min_relevance = 0.3

        from file_compass.indexer import SearchResult

        mock_results = [
            SearchResult(
                path="/test/file.py",
                relative_path="file.py",
                file_type="python",
                chunk_type="function",
                chunk_name="test_func",
                line_start=10,
                line_end=20,
                preview="def test_func():",
                relevance=0.85,
                modified_at=datetime.now(),
                git_tracked=True
            )
        ]

        with patch('file_compass.cli.get_index') as mock_get_index:
            mock_index = MagicMock()
            mock_get_index.return_value = mock_index

            async def mock_search(**kwargs):
                return mock_results
            mock_index.search = mock_search
            mock_index.close = AsyncMock()

            cmd_search(args)

            captured = capsys.readouterr()
            assert "Found 1 results" in captured.out
            assert "file.py" in captured.out
            assert "test_func" in captured.out

    def test_cmd_search_with_type_filter(self, capsys):
        """Test search with type filter."""
        args = MagicMock()
        args.query = "test"
        args.top_k = 10
        args.types = "python,markdown"
        args.directory = None
        args.git_only = False
        args.min_relevance = 0.3

        with patch('file_compass.cli.get_index') as mock_get_index:
            mock_index = MagicMock()
            mock_get_index.return_value = mock_index

            async def mock_search(**kwargs):
                # Verify types were parsed correctly
                assert kwargs.get("file_types") == ["python", "markdown"]
                return []
            mock_index.search = mock_search
            mock_index.close = AsyncMock()

            cmd_search(args)


class TestCmdStatus:
    """Tests for cmd_status command."""

    def test_cmd_status_basic(self, capsys):
        """Test status command output."""
        with patch('file_compass.cli.get_index') as mock_get_index:
            mock_index = MagicMock()
            mock_get_index.return_value = mock_index

            mock_index.get_status.return_value = {
                "files_indexed": 100,
                "chunks_indexed": 500,
                "index_size_mb": 25.5,
                "last_build": "2024-01-15T10:30:00",
                "file_types": {
                    "python": 50,
                    "markdown": 30,
                    "json": 20
                }
            }

            cmd_status(MagicMock())

            captured = capsys.readouterr()
            assert "File Compass - Index Status" in captured.out
            assert "100" in captured.out
            assert "500" in captured.out
            assert "25.5" in captured.out
            assert "python" in captured.out

    def test_cmd_status_empty_index(self, capsys):
        """Test status with empty index."""
        with patch('file_compass.cli.get_index') as mock_get_index:
            mock_index = MagicMock()
            mock_get_index.return_value = mock_index

            mock_index.get_status.return_value = {
                "files_indexed": 0,
                "chunks_indexed": 0,
                "index_size_mb": 0,
                "last_build": None,
                "file_types": {}
            }

            cmd_status(MagicMock())

            captured = capsys.readouterr()
            assert "0" in captured.out
            assert "Never" in captured.out


class TestCmdScan:
    """Tests for cmd_scan command."""

    def test_cmd_scan_basic(self, capsys):
        """Test scan command."""
        args = MagicMock()
        args.directories = None
        args.verbose = False

        from file_compass.scanner import ScannedFile

        mock_files = [
            ScannedFile(
                path=Path("/test/file1.py"),
                relative_path="file1.py",
                file_type="python",
                size_bytes=100,
                modified_at=datetime.now(),
                content_hash="abc",
                is_git_tracked=True
            ),
            ScannedFile(
                path=Path("/test/file2.md"),
                relative_path="file2.md",
                file_type="markdown",
                size_bytes=50,
                modified_at=datetime.now(),
                content_hash="def",
                is_git_tracked=False
            )
        ]

        with patch('file_compass.cli.FileScanner') as MockScanner:
            mock_scanner = MagicMock()
            MockScanner.return_value = mock_scanner
            mock_scanner.scan_all.return_value = iter(mock_files)

            cmd_scan(args)

            captured = capsys.readouterr()
            assert "Found 2 files" in captured.out
            assert "python" in captured.out
            assert "markdown" in captured.out

    def test_cmd_scan_verbose(self, capsys):
        """Test scan command with verbose output."""
        args = MagicMock()
        args.directories = ["/test"]
        args.verbose = True

        from file_compass.scanner import ScannedFile

        mock_files = [
            ScannedFile(
                path=Path("/test/file1.py"),
                relative_path="file1.py",
                file_type="python",
                size_bytes=100,
                modified_at=datetime.now(),
                content_hash="abc",
                is_git_tracked=True
            )
        ]

        with patch('file_compass.cli.FileScanner') as MockScanner:
            mock_scanner = MagicMock()
            MockScanner.return_value = mock_scanner
            mock_scanner.scan_all.return_value = iter(mock_files)

            cmd_scan(args)

            captured = capsys.readouterr()
            assert "file1.py" in captured.out
            assert "git" in captured.out  # git tracking indicator

    def test_cmd_scan_verbose_many_files(self, capsys):
        """Test scan command with verbose output showing >50 files truncation."""
        args = MagicMock()
        args.directories = ["/test"]
        args.verbose = True

        from file_compass.scanner import ScannedFile

        # Create 60 files to trigger truncation message
        mock_files = [
            ScannedFile(
                path=Path(f"/test/file{i}.py"),
                relative_path=f"file{i}.py",
                file_type="python",
                size_bytes=100,
                modified_at=datetime.now(),
                content_hash=f"hash{i}",
                is_git_tracked=True
            )
            for i in range(60)
        ]

        with patch('file_compass.cli.FileScanner') as MockScanner:
            mock_scanner = MagicMock()
            MockScanner.return_value = mock_scanner
            mock_scanner.scan_all.return_value = iter(mock_files)

            cmd_scan(args)

            captured = capsys.readouterr()
            assert "Found 60 files" in captured.out
            # Should show truncation message for files >50
            assert "and 10 more" in captured.out


class TestMain:
    """Tests for main entry point."""

    def test_main_no_command(self, capsys, monkeypatch):
        """Test main with no command shows help."""
        monkeypatch.setattr(sys, 'argv', ['file-compass'])

        with pytest.raises(SystemExit) as exc_info:
            main()

        # Should exit with 0 or 1 depending on help behavior
        assert exc_info.value.code in [0, 1, None]

    def test_main_index_command(self, monkeypatch):
        """Test main dispatches to index command."""
        monkeypatch.setattr(sys, 'argv', ['file-compass', 'index', '-d', '/test'])

        with patch('file_compass.cli.cmd_index') as mock_cmd:
            mock_cmd.return_value = 0
            result = main()

            mock_cmd.assert_called_once()

    def test_main_search_command(self, monkeypatch):
        """Test main dispatches to search command."""
        monkeypatch.setattr(sys, 'argv', ['file-compass', 'search', 'test query'])

        with patch('file_compass.cli.cmd_search') as mock_cmd:
            mock_cmd.return_value = 0
            result = main()

            mock_cmd.assert_called_once()

    def test_main_status_command(self, monkeypatch):
        """Test main dispatches to status command."""
        monkeypatch.setattr(sys, 'argv', ['file-compass', 'status'])

        with patch('file_compass.cli.cmd_status') as mock_cmd:
            mock_cmd.return_value = 0
            result = main()

            mock_cmd.assert_called_once()

    def test_main_scan_command(self, monkeypatch):
        """Test main dispatches to scan command."""
        monkeypatch.setattr(sys, 'argv', ['file-compass', 'scan', '-d', '/test'])

        with patch('file_compass.cli.cmd_scan') as mock_cmd:
            mock_cmd.return_value = 0
            result = main()

            mock_cmd.assert_called_once()

    def test_main_scan_verbose(self, monkeypatch):
        """Test main with verbose flag."""
        monkeypatch.setattr(sys, 'argv', ['file-compass', 'scan', '-v'])

        with patch('file_compass.cli.cmd_scan') as mock_cmd:
            mock_cmd.return_value = 0
            main()

            # Verify verbose was set
            args = mock_cmd.call_args[0][0]
            assert args.verbose is True

    def test_main_search_with_options(self, monkeypatch):
        """Test main search with all options."""
        monkeypatch.setattr(sys, 'argv', [
            'file-compass', 'search', 'query',
            '-k', '20',
            '-t', 'python',
            '-d', '/test',
            '--git-only',
            '--min-relevance', '0.5'
        ])

        with patch('file_compass.cli.cmd_search') as mock_cmd:
            mock_cmd.return_value = 0
            main()

            args = mock_cmd.call_args[0][0]
            assert args.query == 'query'
            assert args.top_k == 20
            assert args.types == 'python'
            assert args.directory == '/test'
            assert args.git_only is True
            assert args.min_relevance == 0.5
