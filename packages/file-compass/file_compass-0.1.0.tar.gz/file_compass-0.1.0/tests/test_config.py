"""
Tests for file_compass.config module.
"""

import pytest
import os
from pathlib import Path

from file_compass.config import FileCompassConfig, get_config


class TestConfig:
    """Tests for FileCompassConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = FileCompassConfig()

        assert config.ollama_url == "http://localhost:11434"
        assert config.embedding_model == "nomic-embed-text"
        assert config.embedding_dim == 768
        assert config.max_chunk_tokens > 0
        assert config.chunk_overlap_tokens >= 0
        assert config.min_chunk_tokens >= 0
        assert isinstance(config.include_extensions, list)
        assert len(config.include_extensions) > 0

    def test_config_directories(self):
        """Test default directories."""
        config = FileCompassConfig()

        # Default should be current directory
        assert config.directories == ["."]

    def test_config_from_env(self, monkeypatch):
        """Test configuration from environment variables."""
        monkeypatch.setenv("OLLAMA_URL", "http://custom:11434")

        # Reset global config
        import file_compass.config as cfg
        cfg._config = None

        config = FileCompassConfig.from_env()

        # Should pick up env vars
        assert config.ollama_url == "http://custom:11434"

    def test_get_config_singleton(self):
        """Test that get_config returns consistent config."""
        # Reset global config
        import file_compass.config as cfg
        cfg._config = None

        config1 = get_config()
        config2 = get_config()

        # Should return same instance
        assert config1 is config2

    def test_include_extensions_have_python(self):
        """Test that Python files are included by default."""
        config = FileCompassConfig()
        assert ".py" in config.include_extensions

    def test_include_extensions_have_common_types(self):
        """Test that common file types are included."""
        config = FileCompassConfig()
        extensions = config.include_extensions

        # Should include common code files
        assert ".py" in extensions
        assert ".md" in extensions
        assert ".json" in extensions

    def test_exclude_patterns(self):
        """Test exclude patterns are set."""
        config = FileCompassConfig()

        # Should exclude common unneeded directories
        patterns = config.exclude_patterns
        assert any("venv" in p for p in patterns)
        assert any("node_modules" in p for p in patterns)
        assert any("__pycache__" in p for p in patterns)

    def test_hnsw_settings(self):
        """Test HNSW index settings."""
        config = FileCompassConfig()

        assert config.hnsw_m > 0
        assert config.hnsw_ef_construction > 0
        assert config.hnsw_ef_search > 0
        assert config.hnsw_max_elements > 0
        assert config.hnsw_space == "cosine"

    def test_config_from_env_directories(self, monkeypatch):
        """Test FILE_COMPASS_DIRECTORIES env var."""
        monkeypatch.setenv("FILE_COMPASS_DIRECTORIES", "/dir1;/dir2")

        import file_compass.config as cfg
        cfg._config = None

        config = FileCompassConfig.from_env()
        assert config.directories == ["/dir1", "/dir2"]

    def test_config_from_env_db_path(self, monkeypatch):
        """Test FILE_COMPASS_DB_PATH env var."""
        monkeypatch.setenv("FILE_COMPASS_DB_PATH", "/custom/db/path")

        import file_compass.config as cfg
        cfg._config = None

        config = FileCompassConfig.from_env()
        assert config.db_path == Path("/custom/db/path")

    def test_config_from_env_exclude_patterns(self, monkeypatch):
        """Test FILE_COMPASS_EXCLUDE_PATTERNS env var."""
        monkeypatch.setenv("FILE_COMPASS_EXCLUDE_PATTERNS", "custom_dir/**;*.bak")

        import file_compass.config as cfg
        cfg._config = None

        config = FileCompassConfig.from_env()
        assert "custom_dir/**" in config.exclude_patterns
        assert "*.bak" in config.exclude_patterns

    def test_config_from_env_watch_enabled(self, monkeypatch):
        """Test FILE_COMPASS_WATCH_ENABLED env var."""
        monkeypatch.setenv("FILE_COMPASS_WATCH_ENABLED", "true")

        import file_compass.config as cfg
        cfg._config = None

        config = FileCompassConfig.from_env()
        assert config.watch_enabled is True

    def test_config_from_env_watch_enabled_false(self, monkeypatch):
        """Test FILE_COMPASS_WATCH_ENABLED env var with false."""
        monkeypatch.setenv("FILE_COMPASS_WATCH_ENABLED", "false")

        import file_compass.config as cfg
        cfg._config = None

        config = FileCompassConfig.from_env()
        assert config.watch_enabled is False
