"""Configuration for File Compass."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

@dataclass
class FileCompassConfig:
    """Configuration for File Compass indexing and search."""

    # Directories to index
    directories: List[str] = field(default_factory=lambda: ["."])

    # Ollama settings
    ollama_url: str = "http://localhost:11434"
    embedding_model: str = "nomic-embed-text"
    embedding_dim: int = 768

    # HNSW settings (tuned for ~100K chunks)
    hnsw_m: int = 32
    hnsw_ef_construction: int = 200
    hnsw_ef_search: int = 100
    hnsw_max_elements: int = 500_000
    hnsw_space: str = "cosine"

    # File scanning
    include_extensions: List[str] = field(default_factory=lambda: [
        ".py", ".md", ".txt", ".json", ".yaml", ".yml",
        ".toml", ".ini", ".cfg", ".ts", ".js", ".jsx", ".tsx",
        ".html", ".css", ".sql", ".sh", ".ps1", ".bat"
    ])

    exclude_patterns: List[str] = field(default_factory=lambda: [
        "**/venv/**", "**/venv_*/**", "**/.venv/**",
        "**/node_modules/**", "**/site-packages/**",
        "**/__pycache__/**", "**/.git/**", "**/.cache/**",
        "**/build/**", "**/dist/**", "**/*.pyc",
        "**/models/**/*.safetensors", "**/models/**/*.gguf",
        "**/models/**/*.bin", "**/models/**/*.pt"
    ])

    # Chunking
    max_chunk_tokens: int = 500
    chunk_overlap_tokens: int = 100
    min_chunk_tokens: int = 50

    # Database paths
    db_path: Optional[Path] = None

    # Search defaults
    default_top_k: int = 10
    min_relevance: float = 0.3

    # Watcher settings
    watch_enabled: bool = False
    watch_debounce_ms: int = 1000

    @classmethod
    def from_env(cls) -> "FileCompassConfig":
        """Load configuration from environment variables."""
        config = cls()

        if dirs := os.environ.get("FILE_COMPASS_DIRECTORIES"):
            config.directories = dirs.split(";")

        if url := os.environ.get("OLLAMA_URL"):
            config.ollama_url = url

        if db := os.environ.get("FILE_COMPASS_DB_PATH"):
            config.db_path = Path(db)

        if exclude := os.environ.get("FILE_COMPASS_EXCLUDE_PATTERNS"):
            config.exclude_patterns.extend(exclude.split(";"))

        if os.environ.get("FILE_COMPASS_WATCH_ENABLED", "").lower() == "true":
            config.watch_enabled = True

        return config


# Global config instance
_config: Optional[FileCompassConfig] = None

def get_config() -> FileCompassConfig:
    """Get or create global config instance."""
    global _config
    if _config is None:
        _config = FileCompassConfig.from_env()
    return _config
