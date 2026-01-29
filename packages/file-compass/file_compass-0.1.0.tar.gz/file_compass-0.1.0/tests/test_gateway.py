"""
Tests for file_compass.gateway module.
Uses mocks to avoid actual MCP server and Ollama dependencies.
"""

import pytest
import tempfile
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from file_compass.gateway import (
    get_index_instance,
    file_search,
    file_preview,
    file_index_status,
    file_index_scan,
    build_index_cli,
    run_tests,
    main,
    _index,
    _is_path_safe
)
from file_compass.config import FileCompassConfig
import file_compass.gateway as gateway_module


class TestGetIndexInstance:
    """Tests for get_index_instance function."""

    @pytest.mark.asyncio
    async def test_get_index_instance_creates_new(self):
        """Test that get_index_instance creates a new index."""
        # Reset global state
        gateway_module._index = None

        with patch('file_compass.gateway.FileIndex') as MockIndex:
            mock_instance = MagicMock()
            mock_instance.index_path = MagicMock()
            mock_instance.index_path.exists.return_value = False
            MockIndex.return_value = mock_instance

            result = await get_index_instance()

            assert result is mock_instance
            MockIndex.assert_called_once()

        # Cleanup
        gateway_module._index = None

    @pytest.mark.asyncio
    async def test_get_index_instance_reuses_existing(self):
        """Test that get_index_instance reuses existing index."""
        # Set up existing index
        mock_existing = MagicMock()
        gateway_module._index = mock_existing

        result = await get_index_instance()

        assert result is mock_existing

        # Cleanup
        gateway_module._index = None

    @pytest.mark.asyncio
    async def test_get_index_instance_loads_existing_index(self):
        """Test that existing index files are loaded."""
        gateway_module._index = None

        with patch('file_compass.gateway.FileIndex') as MockIndex:
            mock_instance = MagicMock()
            mock_instance.index_path = MagicMock()
            mock_instance.index_path.exists.return_value = True
            MockIndex.return_value = mock_instance

            result = await get_index_instance()

            # Should call methods to load existing index
            mock_instance._get_index.assert_called_once()
            mock_instance._get_conn.assert_called_once()

        gateway_module._index = None


class TestFileSearch:
    """Tests for file_search tool."""

    @pytest.mark.asyncio
    async def test_file_search_empty_index(self):
        """Test search with empty index."""
        gateway_module._index = None

        with patch('file_compass.gateway.get_index_instance', new_callable=AsyncMock) as mock_get:
            mock_index = MagicMock()
            mock_index.get_status.return_value = {"files_indexed": 0}
            mock_get.return_value = mock_index

            result = await file_search("test query")

            assert "error" in result
            assert "No files indexed" in result["error"]

        gateway_module._index = None

    @pytest.mark.asyncio
    async def test_file_search_with_results(self):
        """Test search with results."""
        gateway_module._index = None

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

        with patch('file_compass.gateway.get_index_instance', new_callable=AsyncMock) as mock_get:
            mock_index = MagicMock()
            mock_index.get_status.return_value = {"files_indexed": 100}
            mock_index.search = AsyncMock(return_value=mock_results)
            mock_get.return_value = mock_index

            result = await file_search("test query")

            assert result["count"] == 1
            assert result["results"][0]["relative_path"] == "file.py"
            assert result["results"][0]["relevance"] == 0.85

        gateway_module._index = None

    @pytest.mark.asyncio
    async def test_file_search_with_filters(self):
        """Test search with type filter."""
        gateway_module._index = None

        with patch('file_compass.gateway.get_index_instance', new_callable=AsyncMock) as mock_get:
            mock_index = MagicMock()
            mock_index.get_status.return_value = {"files_indexed": 100}
            mock_index.search = AsyncMock(return_value=[])
            mock_get.return_value = mock_index

            await file_search(
                "test",
                file_types="python,markdown",
                directory="/test",
                git_only=True
            )

            # Verify search was called with correct arguments
            call_kwargs = mock_index.search.call_args[1]
            assert call_kwargs["file_types"] == ["python", "markdown"]
            assert call_kwargs["directory"] == "/test"
            assert call_kwargs["git_only"] is True

        gateway_module._index = None

    @pytest.mark.asyncio
    async def test_file_search_clamps_top_k(self):
        """Test that top_k is clamped to valid range."""
        gateway_module._index = None

        with patch('file_compass.gateway.get_index_instance', new_callable=AsyncMock) as mock_get:
            mock_index = MagicMock()
            mock_index.get_status.return_value = {"files_indexed": 100}
            mock_index.search = AsyncMock(return_value=[])
            mock_get.return_value = mock_index

            # Test with too large value
            await file_search("test", top_k=100)
            assert mock_index.search.call_args[1]["top_k"] == 50

            # Test with negative value
            await file_search("test", top_k=-5)
            assert mock_index.search.call_args[1]["top_k"] == 1

        gateway_module._index = None


class TestPathSafety:
    """Tests for path traversal protection."""

    def test_is_path_safe_within_directory(self):
        """Test path within allowed directory is safe."""
        config = FileCompassConfig(directories=["F:/AI", "C:/Projects"])
        assert _is_path_safe(Path("F:/AI/file.py"), config) is True
        assert _is_path_safe(Path("F:/AI/subdir/file.py"), config) is True
        assert _is_path_safe(Path("C:/Projects/app/main.py"), config) is True

    def test_is_path_safe_outside_directory(self):
        """Test path outside allowed directories is blocked."""
        config = FileCompassConfig(directories=["F:/AI"])
        assert _is_path_safe(Path("C:/Windows/System32/config"), config) is False
        assert _is_path_safe(Path("/etc/passwd"), config) is False
        assert _is_path_safe(Path("F:/Other/file.py"), config) is False

    def test_is_path_safe_traversal_attempt(self):
        """Test path traversal attempts are blocked."""
        config = FileCompassConfig(directories=["F:/AI/project"])
        # Attempt to escape via ..
        assert _is_path_safe(Path("F:/AI/project/../../../Windows"), config) is False

    def test_is_path_safe_handles_errors(self):
        """Test that path resolution errors return False."""
        config = FileCompassConfig(directories=["F:/AI"])
        # Empty path resolves to current directory on Windows
        # Test with a path that doesn't match allowed directories
        assert _is_path_safe(Path("Z:/nonexistent/path"), config) is False


class TestFilePreview:
    """Tests for file_preview tool."""

    @pytest.mark.asyncio
    async def test_file_preview_basic(self):
        """Test basic file preview."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, dir='.') as f:
            f.write("line 1\nline 2\nline 3\nline 4\nline 5")
            temp_path = f.name

        try:
            # Need to mock config to allow temp directory
            with patch('file_compass.gateway.get_config') as mock_config:
                mock_config.return_value = FileCompassConfig(directories=['.'])
                result = await file_preview(temp_path)

                assert "content" in result
                assert "line 1" in result["content"]
                assert result["total_lines"] == 5
        finally:
            Path(temp_path).unlink()

    @pytest.mark.asyncio
    async def test_file_preview_with_line_range(self):
        """Test file preview with line range."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, dir='.') as f:
            f.write("\n".join([f"line {i}" for i in range(1, 11)]))
            temp_path = f.name

        try:
            with patch('file_compass.gateway.get_config') as mock_config:
                mock_config.return_value = FileCompassConfig(directories=['.'])
                result = await file_preview(temp_path, line_start=3, line_end=5)

                assert "content" in result
                assert "line 3" in result["content"]
                assert "line 5" in result["content"]
                # line 1 should not be in the preview
                assert "   1 |" not in result["content"]
        finally:
            Path(temp_path).unlink()

    @pytest.mark.asyncio
    async def test_file_preview_nonexistent(self):
        """Test preview of nonexistent file."""
        with patch('file_compass.gateway.get_config') as mock_config:
            mock_config.return_value = FileCompassConfig(directories=["F:/AI"])
            result = await file_preview("F:/AI/nonexistent/file.py")

            assert "error" in result
            assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_file_preview_path_traversal_blocked(self):
        """Test that path traversal attempts are blocked."""
        with patch('file_compass.gateway.get_config') as mock_config:
            mock_config.return_value = FileCompassConfig(directories=["F:/AI/project"])

            # Try to access outside allowed directories
            result = await file_preview("C:/Windows/System32/config/SAM")

            assert "error" in result
            assert "Access denied" in result["error"]
            # Note: hint removed for security (doesn't expose allowed directories)

    @pytest.mark.asyncio
    async def test_file_preview_limits_lines(self):
        """Test that preview limits output to 100 lines."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, dir='.') as f:
            f.write("\n".join([f"line {i}" for i in range(1, 200)]))
            temp_path = f.name

        try:
            with patch('file_compass.gateway.get_config') as mock_config:
                mock_config.return_value = FileCompassConfig(directories=['.'])
                result = await file_preview(temp_path)

                assert "more lines" in result["content"]
        finally:
            Path(temp_path).unlink()

    @pytest.mark.asyncio
    async def test_file_preview_exception(self):
        """Test file preview handles exceptions gracefully."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, dir='.') as f:
            f.write("test content")
            temp_path = f.name

        try:
            # Mock Path.read_text to raise an exception
            with patch('file_compass.gateway.get_config') as mock_config:
                mock_config.return_value = FileCompassConfig(directories=['.'])
                with patch.object(Path, 'read_text', side_effect=PermissionError("Access denied")):
                    with patch.object(Path, 'exists', return_value=True):
                        result = await file_preview(temp_path)

                        # Should return sanitized error dict (no internal details)
                        assert "error" in result
                        assert result["error"] == "Failed to read file"
        finally:
            Path(temp_path).unlink()


class TestFileIndexStatus:
    """Tests for file_index_status tool."""

    @pytest.mark.asyncio
    async def test_file_index_status(self):
        """Test index status retrieval."""
        gateway_module._index = None

        with patch('file_compass.gateway.get_index_instance', new_callable=AsyncMock) as mock_get:
            mock_index = MagicMock()
            mock_index.get_status.return_value = {
                "files_indexed": 100,
                "chunks_indexed": 500,
                "index_size_mb": 25.123456,
                "last_build": "2024-01-15T10:30:00",
                "file_types": {"python": 50, "markdown": 30}
            }
            mock_get.return_value = mock_index

            result = await file_index_status()

            assert result["files_indexed"] == 100
            assert result["chunks_indexed"] == 500
            assert result["index_size_mb"] == 25.12  # Rounded
            assert result["last_build"] == "2024-01-15T10:30:00"
            assert "python" in result["file_types"]

        gateway_module._index = None


class TestFileIndexScan:
    """Tests for file_index_scan tool."""

    @pytest.mark.asyncio
    async def test_file_index_scan_success(self):
        """Test successful index scan."""
        gateway_module._index = None

        with patch('file_compass.gateway.get_index_instance', new_callable=AsyncMock) as mock_get:
            with patch('file_compass.gateway.get_config') as mock_config:
                mock_index = MagicMock()
                mock_index.build_index = AsyncMock(return_value={
                    "files_indexed": 100,
                    "chunks_indexed": 500,
                    "duration_seconds": 30.5
                })
                mock_get.return_value = mock_index

                mock_config.return_value.directories = ["."]

                result = await file_index_scan()

                assert result["success"] is True
                assert result["files_indexed"] == 100
                assert result["duration_seconds"] == 30.5

        gateway_module._index = None

    @pytest.mark.asyncio
    async def test_file_index_scan_with_directories(self):
        """Test index scan with custom directories - invalid dirs return error."""
        gateway_module._index = None

        with patch('file_compass.gateway.get_index_instance', new_callable=AsyncMock) as mock_get:
            with patch('file_compass.gateway.get_config') as mock_config:
                mock_index = MagicMock()
                mock_index.build_index = AsyncMock(return_value={
                    "files_indexed": 50,
                    "chunks_indexed": 250,
                    "duration_seconds": 15.0
                })
                mock_get.return_value = mock_index

                # Non-existent directories are now validated and filtered out
                result = await file_index_scan(directories="/test/dir1,/test/dir2")

                # Since directories don't exist, should return error
                assert result["success"] is False
                assert "No valid directories" in result["error"]

        gateway_module._index = None

    @pytest.mark.asyncio
    async def test_file_index_scan_failure(self):
        """Test index scan failure handling with sanitized error."""
        gateway_module._index = None

        with patch('file_compass.gateway.get_index_instance', new_callable=AsyncMock) as mock_get:
            with patch('file_compass.gateway.get_config') as mock_config:
                mock_index = MagicMock()
                mock_index.build_index = AsyncMock(side_effect=Exception("Ollama not running"))
                mock_get.return_value = mock_index

                mock_config.return_value.directories = ["."]

                result = await file_index_scan()

                assert result["success"] is False
                # Error is now sanitized - doesn't expose internal details
                assert result["error"] == "Indexing failed"
                assert "hint" in result

        gateway_module._index = None


class TestBuildIndexCli:
    """Tests for build_index_cli function."""

    @pytest.mark.asyncio
    async def test_build_index_cli(self, capsys):
        """Test CLI index building."""
        with patch('file_compass.gateway.FileIndex') as MockIndex:
            mock_index = MagicMock()
            mock_index.build_index = AsyncMock(return_value={
                "files_indexed": 100,
                "chunks_indexed": 500,
                "duration_seconds": 30.0
            })
            mock_index.close = AsyncMock()
            MockIndex.return_value = mock_index

            await build_index_cli(["/test/dir"])

            captured = capsys.readouterr()
            assert "Building File Compass index" in captured.out
            assert "100" in captured.out
            assert "500" in captured.out


class TestRunTests:
    """Tests for run_tests function."""

    @pytest.mark.asyncio
    async def test_run_tests(self, capsys):
        """Test test runner."""
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

        with patch('file_compass.gateway.FileIndex') as MockIndex:
            mock_index = MagicMock()
            mock_index.get_status.return_value = {
                "files_indexed": 100,
                "chunks_indexed": 500
            }
            mock_index.search = AsyncMock(return_value=mock_results)
            mock_index.close = AsyncMock()
            MockIndex.return_value = mock_index

            await run_tests()

            captured = capsys.readouterr()
            assert "FILE COMPASS - TEST SUITE" in captured.out
            assert "embedding generation" in captured.out
            assert "file.py" in captured.out


class TestMain:
    """Tests for main entry point."""

    def test_main_index_flag(self, monkeypatch):
        """Test main with --index flag."""
        monkeypatch.setattr(sys, 'argv', ['gateway.py', '--index', '-d', '/test'])

        with patch('file_compass.gateway.asyncio.run') as mock_run:
            main()

            mock_run.assert_called_once()

    def test_main_test_flag(self, monkeypatch):
        """Test main with --test flag."""
        monkeypatch.setattr(sys, 'argv', ['gateway.py', '--test'])

        with patch('file_compass.gateway.asyncio.run') as mock_run:
            main()

            mock_run.assert_called_once()

    def test_main_server_mode(self, monkeypatch, capsys):
        """Test main in server mode."""
        monkeypatch.setattr(sys, 'argv', ['gateway.py'])

        with patch('file_compass.gateway.mcp') as mock_mcp:
            main()

            mock_mcp.run.assert_called_once()


class TestLongPreviewTruncation:
    """Test that long previews are properly truncated."""

    @pytest.mark.asyncio
    async def test_search_truncates_long_previews(self):
        """Test that search results have truncated previews."""
        gateway_module._index = None

        from file_compass.indexer import SearchResult
        long_preview = "x" * 500  # Longer than 200 chars
        mock_results = [
            SearchResult(
                path="/test/file.py",
                relative_path="file.py",
                file_type="python",
                chunk_type="function",
                chunk_name="test_func",
                line_start=10,
                line_end=20,
                preview=long_preview,
                relevance=0.85,
                modified_at=datetime.now(),
                git_tracked=True
            )
        ]

        with patch('file_compass.gateway.get_index_instance', new_callable=AsyncMock) as mock_get:
            mock_index = MagicMock()
            mock_index.get_status.return_value = {"files_indexed": 100}
            mock_index.search = AsyncMock(return_value=mock_results)
            mock_get.return_value = mock_index

            result = await file_search("test")

            # Preview should be truncated to 200 chars + "..."
            preview = result["results"][0]["preview"]
            assert len(preview) <= 203  # 200 + "..."
            assert preview.endswith("...")

        gateway_module._index = None


class TestInputValidation:
    """Tests for input validation in MCP tools."""

    @pytest.mark.asyncio
    async def test_file_search_empty_query(self):
        """Test file_search rejects empty query."""
        result = await file_search("")
        assert "error" in result
        assert "non-empty string" in result["error"]

    @pytest.mark.asyncio
    async def test_file_search_query_too_long(self):
        """Test file_search rejects overly long query."""
        long_query = "x" * 1001
        result = await file_search(long_query)
        assert "error" in result
        assert "too long" in result["error"]

    @pytest.mark.asyncio
    async def test_file_preview_empty_path(self):
        """Test file_preview rejects empty path."""
        result = await file_preview("")
        assert "error" in result
        assert "non-empty string" in result["error"]

    @pytest.mark.asyncio
    async def test_file_preview_path_too_long(self):
        """Test file_preview rejects overly long path."""
        long_path = "x" * 501
        result = await file_preview(long_path)
        assert "error" in result
        assert "too long" in result["error"]

    @pytest.mark.asyncio
    async def test_file_preview_invalid_line_start(self):
        """Test file_preview rejects invalid line_start."""
        result = await file_preview("/test/file.py", line_start=0)
        assert "error" in result
        assert "positive integer" in result["error"]

    @pytest.mark.asyncio
    async def test_file_preview_invalid_line_end(self):
        """Test file_preview rejects invalid line_end."""
        result = await file_preview("/test/file.py", line_start=1, line_end=-5)
        assert "error" in result
        assert "positive integer" in result["error"]


class TestFileQuickSearch:
    """Tests for file_quick_search tool."""

    @pytest.mark.asyncio
    async def test_file_quick_search_empty_query(self):
        """Test quick search rejects empty query."""
        from file_compass.gateway import file_quick_search
        result = await file_quick_search("")
        assert "error" in result
        assert "non-empty string" in result["error"]

    @pytest.mark.asyncio
    async def test_file_quick_search_query_too_long(self):
        """Test quick search rejects overly long query."""
        from file_compass.gateway import file_quick_search
        long_query = "x" * 501
        result = await file_quick_search(long_query)
        assert "error" in result
        assert "too long" in result["error"]

    @pytest.mark.asyncio
    async def test_file_quick_search_clamps_top_k(self):
        """Test quick search clamps top_k to valid range."""
        from file_compass.gateway import file_quick_search
        from file_compass.quick_index import get_quick_index

        with patch.object(get_quick_index(), 'get_status', return_value={"files_indexed": 10, "symbols_indexed": 5}):
            with patch.object(get_quick_index(), 'search', return_value=[]) as mock_search:
                await file_quick_search("test", top_k=1000)
                # Should be clamped to max 100
                assert mock_search.call_args[1]["top_k"] == 100

    @pytest.mark.asyncio
    async def test_file_quick_search_clamps_recent_days(self):
        """Test quick search clamps recent_days to valid range."""
        from file_compass.gateway import file_quick_search
        from file_compass.quick_index import get_quick_index

        with patch.object(get_quick_index(), 'get_status', return_value={"files_indexed": 10, "symbols_indexed": 5}):
            with patch.object(get_quick_index(), 'search', return_value=[]) as mock_search:
                await file_quick_search("test", recent_days=500)
                # Should be clamped to max 365
                assert mock_search.call_args[1]["recent_days"] == 365

    @pytest.mark.asyncio
    async def test_file_quick_search_builds_index_if_empty(self):
        """Test quick search builds index on-demand if empty."""
        from file_compass.gateway import file_quick_search
        from file_compass.quick_index import get_quick_index

        quick_index = get_quick_index()
        call_count = [0]

        def mock_status():
            call_count[0] += 1
            # First call returns empty, second returns populated
            return {"files_indexed": 0 if call_count[0] == 1 else 10, "symbols_indexed": 5}

        with patch.object(quick_index, 'get_status', side_effect=mock_status):
            with patch.object(quick_index, 'build_quick_index', new_callable=AsyncMock) as mock_build:
                with patch.object(quick_index, 'search', return_value=[]):
                    await file_quick_search("test")
                    mock_build.assert_called_once()


class TestFileQuickIndexBuild:
    """Tests for file_quick_index_build tool."""

    @pytest.mark.asyncio
    async def test_file_quick_index_build_success(self):
        """Test quick index build returns success."""
        from file_compass.gateway import file_quick_index_build
        from file_compass.quick_index import get_quick_index

        with patch.object(get_quick_index(), 'build_quick_index', new_callable=AsyncMock) as mock_build:
            mock_build.return_value = {
                "files_indexed": 100,
                "symbols_extracted": 500,
                "duration_seconds": 2.5
            }

            result = await file_quick_index_build()

            assert result["success"] is True
            assert result["files_indexed"] == 100
            assert result["symbols_extracted"] == 500
            assert "hint" in result

    @pytest.mark.asyncio
    async def test_file_quick_index_build_failure(self):
        """Test quick index build handles failures."""
        from file_compass.gateway import file_quick_index_build
        from file_compass.quick_index import get_quick_index

        with patch.object(get_quick_index(), 'build_quick_index', new_callable=AsyncMock) as mock_build:
            mock_build.side_effect = Exception("Disk full")

            result = await file_quick_index_build()

            assert result["success"] is False
            assert "error" in result


class TestFileActions:
    """Tests for file_actions tool."""

    @pytest.mark.asyncio
    async def test_file_actions_empty_path(self):
        """Test file_actions rejects empty path."""
        from file_compass.gateway import file_actions
        result = await file_actions("", "context")
        assert "error" in result
        assert "non-empty string" in result["error"]

    @pytest.mark.asyncio
    async def test_file_actions_path_too_long(self):
        """Test file_actions rejects overly long path."""
        from file_compass.gateway import file_actions
        long_path = "x" * 501
        result = await file_actions(long_path, "context")
        assert "error" in result
        assert "too long" in result["error"]

    @pytest.mark.asyncio
    async def test_file_actions_empty_action(self):
        """Test file_actions rejects empty action."""
        from file_compass.gateway import file_actions
        result = await file_actions("/test/file.py", "")
        assert "error" in result
        assert "non-empty string" in result["error"]

    @pytest.mark.asyncio
    async def test_file_actions_invalid_action(self):
        """Test file_actions rejects invalid action."""
        from file_compass.gateway import file_actions
        result = await file_actions("/test/file.py", "invalid_action")
        assert "error" in result
        assert "Invalid action" in result["error"]
        assert "available_actions" in result

    @pytest.mark.asyncio
    async def test_file_actions_invalid_line_start(self):
        """Test file_actions rejects invalid line_start."""
        from file_compass.gateway import file_actions
        result = await file_actions("/test/file.py", "context", line_start=0)
        assert "error" in result
        assert "positive integer" in result["error"]

    @pytest.mark.asyncio
    async def test_file_actions_path_traversal_blocked(self):
        """Test file_actions blocks path traversal."""
        from file_compass.gateway import file_actions

        with patch('file_compass.gateway.get_config') as mock_config:
            mock_config.return_value = FileCompassConfig(directories=["F:/AI"])
            result = await file_actions("C:/Windows/System32/config", "context")

            assert "error" in result
            assert "Access denied" in result["error"]

    @pytest.mark.asyncio
    async def test_file_actions_file_not_found(self):
        """Test file_actions handles missing file."""
        from file_compass.gateway import file_actions

        with patch('file_compass.gateway.get_config') as mock_config:
            mock_config.return_value = FileCompassConfig(directories=["F:/AI"])
            result = await file_actions("F:/AI/nonexistent/file.py", "context")

            assert "error" in result
            assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_file_actions_context(self):
        """Test file_actions context action."""
        from file_compass.gateway import file_actions

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, dir='.') as f:
            f.write("\n".join([f"line {i}" for i in range(1, 51)]))
            temp_path = f.name

        try:
            with patch('file_compass.gateway.get_config') as mock_config:
                mock_config.return_value = FileCompassConfig(directories=['.'])
                result = await file_actions(temp_path, "context", line_start=20, line_end=25)

                assert "content" in result
                assert "focus_range" in result
                assert "20-25" in result["focus_range"]
        finally:
            Path(temp_path).unlink()

    @pytest.mark.asyncio
    async def test_file_actions_symbols(self):
        """Test file_actions symbols action."""
        from file_compass.gateway import file_actions

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, dir='.') as f:
            f.write("""
def my_function():
    pass

class MyClass:
    def method(self):
        pass
""")
            temp_path = f.name

        try:
            with patch('file_compass.gateway.get_config') as mock_config:
                mock_config.return_value = FileCompassConfig(directories=['.'])
                result = await file_actions(temp_path, "symbols")

                assert "functions" in result
                assert "classes" in result
                assert len(result["functions"]) >= 1
                assert len(result["classes"]) >= 1
        finally:
            Path(temp_path).unlink()

    @pytest.mark.asyncio
    async def test_file_actions_history_no_git(self):
        """Test file_actions history action without git repo."""
        from file_compass.gateway import file_actions

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, dir='.') as f:
            f.write("test content")
            temp_path = f.name

        try:
            with patch('file_compass.gateway.get_config') as mock_config:
                mock_config.return_value = FileCompassConfig(directories=['.'])
                # Mock subprocess to simulate no git repo
                with patch('subprocess.run') as mock_run:
                    mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="not a git repo")
                    result = await file_actions(temp_path, "history")

                    assert "error" in result or "recent_commits" in result
        finally:
            Path(temp_path).unlink()

    @pytest.mark.asyncio
    async def test_file_actions_usages(self):
        """Test file_actions usages action."""
        from file_compass.gateway import file_actions

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, dir='.') as f:
            f.write("test module")
            temp_path = f.name

        try:
            with patch('file_compass.gateway.get_config') as mock_config:
                mock_config.return_value = FileCompassConfig(directories=['.'])
                with patch('file_compass.gateway.get_index_instance', new_callable=AsyncMock) as mock_get:
                    mock_index = MagicMock()
                    mock_index.search = AsyncMock(return_value=[])
                    mock_get.return_value = mock_index

                    result = await file_actions(temp_path, "usages")

                    assert "usages" in result
                    assert "count" in result
        finally:
            Path(temp_path).unlink()

    @pytest.mark.asyncio
    async def test_file_actions_related(self):
        """Test file_actions related action."""
        from file_compass.gateway import file_actions

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, dir='.') as f:
            f.write("import os\nimport sys\nfrom pathlib import Path")
            temp_path = f.name

        try:
            with patch('file_compass.gateway.get_config') as mock_config:
                mock_config.return_value = FileCompassConfig(directories=['.'])
                with patch('file_compass.gateway.get_index_instance', new_callable=AsyncMock) as mock_get:
                    mock_index = MagicMock()
                    mock_index.search = AsyncMock(return_value=[])
                    mock_get.return_value = mock_index

                    result = await file_actions(temp_path, "related")

                    assert "imports" in result
                    assert "os" in result["imports"]
                    assert "sys" in result["imports"]
        finally:
            Path(temp_path).unlink()


class TestFileSearchWithExplanation:
    """Tests for file_search with explanation feature."""

    @pytest.mark.asyncio
    async def test_file_search_with_explain_true(self):
        """Test file_search includes explanations when explain=True."""
        gateway_module._index = None

        from file_compass.indexer import SearchResult
        mock_results = [
            SearchResult(
                path="/test/embedder.py",
                relative_path="embedder.py",
                file_type="python",
                chunk_type="function",
                chunk_name="generate_embedding",
                line_start=10,
                line_end=20,
                preview="def generate_embedding(text):\n    return model.embed(text)",
                relevance=0.85,
                modified_at=datetime.now(),
                git_tracked=True
            )
        ]

        with patch('file_compass.gateway.get_index_instance', new_callable=AsyncMock) as mock_get:
            mock_index = MagicMock()
            mock_index.get_status.return_value = {"files_indexed": 100}
            mock_index.search = AsyncMock(return_value=mock_results)
            mock_get.return_value = mock_index

            result = await file_search("embedding generation", explain=True)

            assert "results" in result
            assert len(result["results"]) > 0
            first_result = result["results"][0]
            assert "why" in first_result
            assert "match_reasons" in first_result

        gateway_module._index = None

    @pytest.mark.asyncio
    async def test_file_search_with_explain_false(self):
        """Test file_search excludes explanations when explain=False."""
        gateway_module._index = None

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
                preview="def test_func(): pass",
                relevance=0.75,
                modified_at=datetime.now(),
                git_tracked=True
            )
        ]

        with patch('file_compass.gateway.get_index_instance', new_callable=AsyncMock) as mock_get:
            mock_index = MagicMock()
            mock_index.get_status.return_value = {"files_indexed": 100}
            mock_index.search = AsyncMock(return_value=mock_results)
            mock_get.return_value = mock_index

            result = await file_search("test", explain=False)

            assert "results" in result
            assert len(result["results"]) > 0
            first_result = result["results"][0]
            assert "why" not in first_result
            assert "match_reasons" not in first_result

        gateway_module._index = None
