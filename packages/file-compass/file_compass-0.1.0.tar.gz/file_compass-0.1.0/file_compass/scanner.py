"""
File Compass - Scanner Module
Discovers files for indexing with gitignore and pattern support.
"""

import os
import fnmatch
import hashlib
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Iterator, Set
from datetime import datetime
import logging

from .config import get_config

logger = logging.getLogger(__name__)


@dataclass
class ScannedFile:
    """Represents a discovered file for indexing."""
    path: Path
    relative_path: str
    file_type: str
    size_bytes: int
    modified_at: datetime
    content_hash: str
    git_repo: Optional[str] = None
    is_git_tracked: bool = False


class FileScanner:
    """
    Scans directories for indexable files.
    Respects gitignore patterns and configurable exclusions.
    """

    def __init__(
        self,
        directories: Optional[List[str]] = None,
        include_extensions: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ):
        config = get_config()
        self.directories = [Path(d) for d in (directories or config.directories)]
        self.include_extensions = set(include_extensions or config.include_extensions)
        self.exclude_patterns = exclude_patterns or config.exclude_patterns

        # Cache for git repo roots
        self._git_repos: dict[Path, Optional[Path]] = {}
        self._git_tracked_files: dict[Path, Set[str]] = {}

    def _matches_exclude_pattern(self, path: Path, base_dir: Path) -> bool:
        """Check if path matches any exclude pattern."""
        rel_path = str(path.relative_to(base_dir)).replace("\\", "/")

        for pattern in self.exclude_patterns:
            # Handle ** patterns
            if "**" in pattern:
                pattern_parts = pattern.replace("\\", "/").split("**")
                if len(pattern_parts) == 2:
                    prefix, suffix = pattern_parts
                    prefix = prefix.rstrip("/")
                    suffix = suffix.lstrip("/")

                    if prefix and not rel_path.startswith(prefix.lstrip("/")):
                        continue
                    if suffix and not fnmatch.fnmatch(rel_path, f"*{suffix}"):
                        continue
                    return True
            elif fnmatch.fnmatch(rel_path, pattern):
                return True

        return False

    def _find_git_repo(self, path: Path) -> Optional[Path]:
        """Find the git repository root for a path."""
        # Check cache first
        for parent in [path] + list(path.parents):
            if parent in self._git_repos:
                return self._git_repos[parent]

        # Search for .git directory
        current = path if path.is_dir() else path.parent
        while current != current.parent:
            if (current / ".git").exists():
                # Cache result for this and all child paths
                self._git_repos[path] = current
                return current
            current = current.parent

        self._git_repos[path] = None
        return None

    def _get_git_tracked_files(self, repo_root: Path) -> Set[str]:
        """Get set of git-tracked files in a repository."""
        if repo_root in self._git_tracked_files:
            return self._git_tracked_files[repo_root]

        tracked = set()
        try:
            result = subprocess.run(
                ["git", "ls-files"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if line:
                        tracked.add(line.replace("/", "\\"))
        except Exception as e:
            logger.warning(f"Failed to get git tracked files for {repo_root}: {e}")

        self._git_tracked_files[repo_root] = tracked
        return tracked

    def _compute_hash(self, path: Path) -> str:
        """Compute SHA256 hash of file content."""
        try:
            return hashlib.sha256(path.read_bytes()).hexdigest()[:16]
        except Exception:
            return ""

    def _get_file_type(self, path: Path) -> str:
        """Determine file type from extension."""
        ext = path.suffix.lower()
        type_map = {
            ".py": "python",
            ".md": "markdown",
            ".txt": "text",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".toml": "toml",
            ".ini": "ini",
            ".cfg": "config",
            ".ts": "typescript",
            ".js": "javascript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".html": "html",
            ".css": "css",
            ".sql": "sql",
            ".sh": "shell",
            ".ps1": "powershell",
            ".bat": "batch",
        }
        return type_map.get(ext, "text")

    def scan_directory(self, directory: Path) -> Iterator[ScannedFile]:
        """
        Scan a single directory for indexable files.

        Yields:
            ScannedFile objects for each discovered file
        """
        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return

        logger.info(f"Scanning {directory}...")

        for root, dirs, files in os.walk(directory):
            root_path = Path(root)

            # Filter directories in-place to skip excluded paths
            dirs[:] = [
                d for d in dirs
                if not self._matches_exclude_pattern(root_path / d, directory)
                and not d.startswith(".")
            ]

            for filename in files:
                file_path = root_path / filename

                # Check extension
                if file_path.suffix.lower() not in self.include_extensions:
                    continue

                # Check exclude patterns
                if self._matches_exclude_pattern(file_path, directory):
                    continue

                # Skip very large files (>10MB)
                try:
                    stat = file_path.stat()
                    if stat.st_size > 10 * 1024 * 1024:
                        continue
                except OSError:
                    continue

                # Get git info
                git_repo = self._find_git_repo(file_path)
                is_tracked = False
                git_repo_str = None

                if git_repo:
                    git_repo_str = str(git_repo)
                    tracked_files = self._get_git_tracked_files(git_repo)
                    rel_to_repo = str(file_path.relative_to(git_repo))
                    is_tracked = rel_to_repo in tracked_files

                yield ScannedFile(
                    path=file_path,
                    relative_path=str(file_path.relative_to(directory)),
                    file_type=self._get_file_type(file_path),
                    size_bytes=stat.st_size,
                    modified_at=datetime.fromtimestamp(stat.st_mtime),
                    content_hash=self._compute_hash(file_path),
                    git_repo=git_repo_str,
                    is_git_tracked=is_tracked
                )

    def scan_all(self) -> Iterator[ScannedFile]:
        """
        Scan all configured directories.

        Yields:
            ScannedFile objects for each discovered file
        """
        for directory in self.directories:
            yield from self.scan_directory(directory)

    def scan_count(self) -> int:
        """Count total files without full scan."""
        count = 0
        for _ in self.scan_all():
            count += 1
        return count


if __name__ == "__main__":
    # Quick test
    scanner = FileScanner(directories=["F:/AI/mcp-tool-shop"])

    print("Scanning files...")
    files = list(scanner.scan_all())
    print(f"Found {len(files)} files")

    # Show first 10
    for f in files[:10]:
        print(f"  {f.relative_path} ({f.file_type}, {f.size_bytes} bytes)")

    # Count by type
    from collections import Counter
    types = Counter(f.file_type for f in files)
    print("\nBy type:")
    for t, c in types.most_common():
        print(f"  {t}: {c}")
