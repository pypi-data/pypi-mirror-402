"""
File Compass - Merkle Tree Module
Efficient change detection using hash trees.
Based on Cursor IDE's approach for fast incremental indexing.
"""

import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class FileNode:
    """Represents a file in the Merkle tree."""
    path: str
    content_hash: str
    chunk_hashes: List[str] = field(default_factory=list)
    modified_at: float = 0.0  # Unix timestamp

    @property
    def combined_hash(self) -> str:
        """Get combined hash of file and all its chunks."""
        if not self.chunk_hashes:
            return self.content_hash
        combined = self.content_hash + "".join(sorted(self.chunk_hashes))
        return hashlib.sha256(combined.encode()).hexdigest()[:16]


@dataclass
class DirectoryNode:
    """Represents a directory in the Merkle tree."""
    path: str
    files: Dict[str, FileNode] = field(default_factory=dict)
    subdirs: Dict[str, "DirectoryNode"] = field(default_factory=dict)
    _cached_hash: Optional[str] = field(default=None, repr=False)

    @property
    def hash(self) -> str:
        """Compute Merkle hash for this directory."""
        if self._cached_hash is not None:
            return self._cached_hash

        # Combine all file and subdirectory hashes
        parts = []

        # Add file hashes (sorted for determinism)
        for name in sorted(self.files.keys()):
            parts.append(f"F:{name}:{self.files[name].combined_hash}")

        # Add subdirectory hashes (sorted)
        for name in sorted(self.subdirs.keys()):
            parts.append(f"D:{name}:{self.subdirs[name].hash}")

        if not parts:
            self._cached_hash = "empty"
        else:
            combined = "\n".join(parts)
            self._cached_hash = hashlib.sha256(combined.encode()).hexdigest()[:16]

        return self._cached_hash

    def invalidate_hash(self):
        """Invalidate cached hash (call when contents change)."""
        self._cached_hash = None


class MerkleTree:
    """
    Merkle tree for efficient file change detection.

    The tree structure mirrors the directory structure:
    - Each file has a hash based on content + chunk hashes
    - Each directory has a hash based on all children
    - Changes propagate up, enabling fast diff detection
    """

    def __init__(self):
        self.root = DirectoryNode(path="")
        self._file_index: Dict[str, FileNode] = {}  # path -> FileNode

    def add_file(self, path: str, content_hash: str, chunk_hashes: List[str] = None,
                 modified_at: float = 0.0):
        """
        Add or update a file in the tree.

        Args:
            path: Relative file path (forward slashes)
            content_hash: Hash of file content
            chunk_hashes: Hashes of individual chunks
            modified_at: File modification timestamp
        """
        # Normalize path
        path = path.replace("\\", "/").lstrip("/")
        parts = path.split("/")

        # Navigate/create directory structure
        current = self.root
        for part in parts[:-1]:  # All but filename
            if part not in current.subdirs:
                current.subdirs[part] = DirectoryNode(path=f"{current.path}/{part}".lstrip("/"))
            current.invalidate_hash()  # Mark for recomputation
            current = current.subdirs[part]

        # Create/update file node
        filename = parts[-1]
        file_node = FileNode(
            path=path,
            content_hash=content_hash,
            chunk_hashes=chunk_hashes or [],
            modified_at=modified_at
        )
        current.files[filename] = file_node
        current.invalidate_hash()

        # Update index
        self._file_index[path] = file_node

        # Invalidate hashes up to root
        self._invalidate_path(parts[:-1])

    def remove_file(self, path: str) -> bool:
        """
        Remove a file from the tree.

        Args:
            path: Relative file path

        Returns:
            True if file was removed, False if not found
        """
        path = path.replace("\\", "/").lstrip("/")
        parts = path.split("/")

        # Navigate to parent directory
        current = self.root
        for part in parts[:-1]:
            if part not in current.subdirs:
                return False
            current = current.subdirs[part]

        # Remove file
        filename = parts[-1]
        if filename in current.files:
            del current.files[filename]
            current.invalidate_hash()
            self._file_index.pop(path, None)
            self._invalidate_path(parts[:-1])
            return True

        return False

    def _invalidate_path(self, path_parts: List[str]):
        """Invalidate hashes along a path from root."""
        current = self.root
        current.invalidate_hash()
        for part in path_parts:
            if part in current.subdirs:
                current = current.subdirs[part]
                current.invalidate_hash()

    def get_file(self, path: str) -> Optional[FileNode]:
        """Get file node by path."""
        path = path.replace("\\", "/").lstrip("/")
        return self._file_index.get(path)

    def get_root_hash(self) -> str:
        """Get the root hash of the entire tree."""
        return self.root.hash

    def diff(self, other: "MerkleTree") -> Tuple[Set[str], Set[str], Set[str]]:
        """
        Compare with another Merkle tree and find differences.

        Args:
            other: Another MerkleTree to compare against

        Returns:
            Tuple of (added_files, removed_files, modified_files)
        """
        added = set()
        removed = set()
        modified = set()

        our_files = set(self._file_index.keys())
        their_files = set(other._file_index.keys())

        # Files only in self (added)
        added = our_files - their_files

        # Files only in other (removed)
        removed = their_files - our_files

        # Files in both - check for modifications
        for path in our_files & their_files:
            our_node = self._file_index[path]
            their_node = other._file_index[path]

            if our_node.combined_hash != their_node.combined_hash:
                modified.add(path)

        return added, removed, modified

    def diff_quick(self, other: "MerkleTree") -> bool:
        """
        Quick check if trees are identical (just compare root hashes).

        Returns:
            True if trees are different, False if identical
        """
        return self.get_root_hash() != other.get_root_hash()

    def find_changed_dirs(self, other: "MerkleTree") -> Set[str]:
        """
        Find directories that have changed between trees.
        Uses Merkle property to prune unchanged subtrees.

        Returns:
            Set of directory paths that have changes
        """
        changed = set()

        def compare_dirs(our_dir: DirectoryNode, their_dir: Optional[DirectoryNode], path: str):
            if their_dir is None:
                # Entire directory is new
                changed.add(path)
                return

            if our_dir.hash == their_dir.hash:
                # Hashes match - no changes in this subtree
                return

            # Something changed - add this dir
            changed.add(path)

            # Recursively check subdirectories
            all_subdirs = set(our_dir.subdirs.keys()) | set(their_dir.subdirs.keys())
            for subdir in all_subdirs:
                subpath = f"{path}/{subdir}".lstrip("/")
                compare_dirs(
                    our_dir.subdirs.get(subdir, DirectoryNode(path=subpath)),
                    their_dir.subdirs.get(subdir),
                    subpath
                )

        compare_dirs(self.root, other.root, "")
        return changed

    def to_dict(self) -> Dict:
        """Serialize tree to dictionary."""
        def serialize_dir(dir_node: DirectoryNode) -> Dict:
            return {
                "path": dir_node.path,
                "files": {
                    name: {
                        "path": f.path,
                        "content_hash": f.content_hash,
                        "chunk_hashes": f.chunk_hashes,
                        "modified_at": f.modified_at
                    }
                    for name, f in dir_node.files.items()
                },
                "subdirs": {
                    name: serialize_dir(subdir)
                    for name, subdir in dir_node.subdirs.items()
                }
            }
        return serialize_dir(self.root)

    @classmethod
    def from_dict(cls, data: Dict) -> "MerkleTree":
        """Deserialize tree from dictionary."""
        tree = cls()

        def deserialize_dir(dir_data: Dict, current: DirectoryNode):
            for name, file_data in dir_data.get("files", {}).items():
                file_node = FileNode(
                    path=file_data["path"],
                    content_hash=file_data["content_hash"],
                    chunk_hashes=file_data.get("chunk_hashes", []),
                    modified_at=file_data.get("modified_at", 0.0)
                )
                current.files[name] = file_node
                tree._file_index[file_data["path"]] = file_node

            for name, subdir_data in dir_data.get("subdirs", {}).items():
                subdir = DirectoryNode(path=subdir_data["path"])
                current.subdirs[name] = subdir
                deserialize_dir(subdir_data, subdir)

        deserialize_dir(data, tree.root)
        return tree

    def save(self, path: Path):
        """Save tree to JSON file."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: Path) -> Optional["MerkleTree"]:
        """Load tree from JSON file."""
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to load Merkle tree from {path}: {e}")
            return None

    def get_stats(self) -> Dict:
        """Get statistics about the tree."""
        def count_dir(dir_node: DirectoryNode) -> Tuple[int, int, int]:
            files = len(dir_node.files)
            dirs = len(dir_node.subdirs)
            chunks = sum(len(f.chunk_hashes) for f in dir_node.files.values())

            for subdir in dir_node.subdirs.values():
                sf, sd, sc = count_dir(subdir)
                files += sf
                dirs += sd
                chunks += sc

            return files, dirs, chunks

        files, dirs, chunks = count_dir(self.root)
        return {
            "total_files": files,
            "total_directories": dirs,
            "total_chunks": chunks,
            "root_hash": self.get_root_hash()
        }


def compute_chunk_hash(content: str) -> str:
    """Compute hash for a chunk of content."""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def compute_file_hash(path: Path) -> Optional[str]:
    """Compute hash for a file's content."""
    try:
        content = path.read_bytes()
        return hashlib.sha256(content).hexdigest()[:16]
    except Exception as e:
        logger.warning(f"Failed to hash {path}: {e}")
        return None
