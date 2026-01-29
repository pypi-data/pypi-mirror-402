"""
Tests for file_compass.merkle module.
"""

import pytest
import tempfile
from pathlib import Path

from file_compass.merkle import (
    MerkleTree, FileNode, DirectoryNode,
    compute_chunk_hash, compute_file_hash
)


class TestFileNode:
    """Tests for FileNode class."""

    def test_file_node_basic(self):
        """Test basic FileNode creation."""
        node = FileNode(
            path="test/file.py",
            content_hash="abc123",
            chunk_hashes=["hash1", "hash2"],
            modified_at=1234567890.0
        )
        assert node.path == "test/file.py"
        assert node.content_hash == "abc123"
        assert len(node.chunk_hashes) == 2

    def test_file_node_combined_hash_no_chunks(self):
        """Test combined hash when no chunks."""
        node = FileNode(path="test.py", content_hash="abc123")
        assert node.combined_hash == "abc123"

    def test_file_node_combined_hash_with_chunks(self):
        """Test combined hash includes chunks."""
        node1 = FileNode(path="test.py", content_hash="abc", chunk_hashes=["a", "b"])
        node2 = FileNode(path="test.py", content_hash="abc", chunk_hashes=["a", "c"])
        # Different chunks should produce different combined hash
        assert node1.combined_hash != node2.combined_hash

    def test_file_node_combined_hash_deterministic(self):
        """Test combined hash is deterministic."""
        node1 = FileNode(path="test.py", content_hash="abc", chunk_hashes=["b", "a"])
        node2 = FileNode(path="test.py", content_hash="abc", chunk_hashes=["a", "b"])
        # Order shouldn't matter (sorted internally)
        assert node1.combined_hash == node2.combined_hash


class TestDirectoryNode:
    """Tests for DirectoryNode class."""

    def test_directory_node_empty(self):
        """Test empty directory hash."""
        node = DirectoryNode(path="test")
        assert node.hash == "empty"

    def test_directory_node_with_files(self):
        """Test directory hash with files."""
        node = DirectoryNode(path="test")
        node.files["a.py"] = FileNode(path="test/a.py", content_hash="hash1")
        node.files["b.py"] = FileNode(path="test/b.py", content_hash="hash2")

        hash1 = node.hash
        assert hash1 != "empty"

    def test_directory_node_hash_changes_with_files(self):
        """Test directory hash changes when files change."""
        node = DirectoryNode(path="test")
        node.files["a.py"] = FileNode(path="test/a.py", content_hash="hash1")
        hash1 = node.hash

        # Modify file
        node.invalidate_hash()
        node.files["a.py"] = FileNode(path="test/a.py", content_hash="hash2")
        hash2 = node.hash

        assert hash1 != hash2

    def test_directory_node_hash_caching(self):
        """Test hash caching."""
        node = DirectoryNode(path="test")
        node.files["a.py"] = FileNode(path="test/a.py", content_hash="hash1")

        hash1 = node.hash
        hash2 = node.hash

        # Should return cached value
        assert hash1 == hash2
        assert node._cached_hash is not None


class TestMerkleTree:
    """Tests for MerkleTree class."""

    def test_empty_tree(self):
        """Test empty tree."""
        tree = MerkleTree()
        assert tree.get_root_hash() == "empty"

    def test_add_file_basic(self):
        """Test adding a file."""
        tree = MerkleTree()
        tree.add_file("test.py", "hash123")

        file_node = tree.get_file("test.py")
        assert file_node is not None
        assert file_node.content_hash == "hash123"

    def test_add_file_nested(self):
        """Test adding nested file."""
        tree = MerkleTree()
        tree.add_file("src/utils/helper.py", "hash123")

        file_node = tree.get_file("src/utils/helper.py")
        assert file_node is not None

        # Directories should be created
        assert "src" in tree.root.subdirs
        assert "utils" in tree.root.subdirs["src"].subdirs

    def test_add_file_normalizes_path(self):
        """Test path normalization."""
        tree = MerkleTree()
        tree.add_file("src\\utils\\helper.py", "hash123")  # Windows path

        file_node = tree.get_file("src/utils/helper.py")
        assert file_node is not None

    def test_remove_file(self):
        """Test removing a file."""
        tree = MerkleTree()
        tree.add_file("test.py", "hash123")
        tree.add_file("other.py", "hash456")

        result = tree.remove_file("test.py")
        assert result is True
        assert tree.get_file("test.py") is None
        assert tree.get_file("other.py") is not None

    def test_remove_file_not_found(self):
        """Test removing non-existent file."""
        tree = MerkleTree()
        result = tree.remove_file("nonexistent.py")
        assert result is False

    def test_root_hash_changes_with_content(self):
        """Test root hash changes when content changes."""
        tree = MerkleTree()
        tree.add_file("test.py", "hash1")
        hash1 = tree.get_root_hash()

        tree.add_file("test.py", "hash2")  # Update same file
        hash2 = tree.get_root_hash()

        assert hash1 != hash2

    def test_diff_empty_trees(self):
        """Test diff of empty trees."""
        tree1 = MerkleTree()
        tree2 = MerkleTree()

        added, removed, modified = tree1.diff(tree2)
        assert len(added) == 0
        assert len(removed) == 0
        assert len(modified) == 0

    def test_diff_added_files(self):
        """Test diff detects added files."""
        tree1 = MerkleTree()
        tree1.add_file("new.py", "hash1")

        tree2 = MerkleTree()

        added, removed, modified = tree1.diff(tree2)
        assert "new.py" in added
        assert len(removed) == 0
        assert len(modified) == 0

    def test_diff_removed_files(self):
        """Test diff detects removed files."""
        tree1 = MerkleTree()

        tree2 = MerkleTree()
        tree2.add_file("deleted.py", "hash1")

        added, removed, modified = tree1.diff(tree2)
        assert len(added) == 0
        assert "deleted.py" in removed
        assert len(modified) == 0

    def test_diff_modified_files(self):
        """Test diff detects modified files."""
        tree1 = MerkleTree()
        tree1.add_file("file.py", "new_hash")

        tree2 = MerkleTree()
        tree2.add_file("file.py", "old_hash")

        added, removed, modified = tree1.diff(tree2)
        assert len(added) == 0
        assert len(removed) == 0
        assert "file.py" in modified

    def test_diff_chunk_changes(self):
        """Test diff detects chunk-level changes."""
        tree1 = MerkleTree()
        tree1.add_file("file.py", "same_hash", chunk_hashes=["c1", "c2"])

        tree2 = MerkleTree()
        tree2.add_file("file.py", "same_hash", chunk_hashes=["c1", "c3"])

        added, removed, modified = tree1.diff(tree2)
        assert "file.py" in modified

    def test_diff_quick(self):
        """Test quick diff comparison."""
        tree1 = MerkleTree()
        tree1.add_file("file.py", "hash1")

        tree2 = MerkleTree()
        tree2.add_file("file.py", "hash1")

        # Identical trees
        assert not tree1.diff_quick(tree2)

        # Different trees
        tree2.add_file("other.py", "hash2")
        assert tree1.diff_quick(tree2)

    def test_find_changed_dirs(self):
        """Test finding changed directories."""
        tree1 = MerkleTree()
        tree1.add_file("src/a.py", "hash1")
        tree1.add_file("src/utils/b.py", "hash2")
        tree1.add_file("tests/test.py", "hash3")

        tree2 = MerkleTree()
        tree2.add_file("src/a.py", "hash1")
        tree2.add_file("src/utils/b.py", "old_hash")  # Changed
        tree2.add_file("tests/test.py", "hash3")

        changed = tree1.find_changed_dirs(tree2)
        # Root, src, and src/utils should be changed
        assert "" in changed  # root
        assert "src" in changed
        assert "src/utils" in changed
        # tests should not be changed
        assert "tests" not in changed

    def test_serialization_roundtrip(self):
        """Test save and load."""
        tree1 = MerkleTree()
        tree1.add_file("src/a.py", "hash1", chunk_hashes=["c1", "c2"])
        tree1.add_file("src/utils/b.py", "hash2")
        tree1.add_file("tests/test.py", "hash3")

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = Path(f.name)

        try:
            tree1.save(temp_path)
            tree2 = MerkleTree.load(temp_path)

            assert tree2 is not None
            assert tree1.get_root_hash() == tree2.get_root_hash()

            # Verify files are preserved
            file_node = tree2.get_file("src/a.py")
            assert file_node is not None
            assert file_node.chunk_hashes == ["c1", "c2"]
        finally:
            temp_path.unlink()

    def test_load_nonexistent_file(self):
        """Test loading from non-existent file."""
        tree = MerkleTree.load(Path("/nonexistent/file.json"))
        assert tree is None

    def test_to_dict_from_dict(self):
        """Test dict serialization."""
        tree1 = MerkleTree()
        tree1.add_file("file.py", "hash1", modified_at=1234567890.0)

        data = tree1.to_dict()
        tree2 = MerkleTree.from_dict(data)

        assert tree1.get_root_hash() == tree2.get_root_hash()
        file_node = tree2.get_file("file.py")
        assert file_node.modified_at == 1234567890.0

    def test_get_stats(self):
        """Test statistics collection."""
        tree = MerkleTree()
        tree.add_file("src/a.py", "h1", chunk_hashes=["c1", "c2"])
        tree.add_file("src/b.py", "h2", chunk_hashes=["c3"])
        tree.add_file("tests/test.py", "h3")

        stats = tree.get_stats()
        assert stats["total_files"] == 3
        assert stats["total_directories"] == 2  # src, tests
        assert stats["total_chunks"] == 3  # c1, c2, c3
        assert stats["root_hash"] != "empty"


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_compute_chunk_hash(self):
        """Test chunk hash computation."""
        hash1 = compute_chunk_hash("hello world")
        hash2 = compute_chunk_hash("hello world")
        hash3 = compute_chunk_hash("different content")

        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 16

    def test_compute_file_hash(self):
        """Test file hash computation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("test content")
            temp_path = Path(f.name)

        try:
            hash1 = compute_file_hash(temp_path)
            assert hash1 is not None
            assert len(hash1) == 16
        finally:
            temp_path.unlink()

    def test_compute_file_hash_nonexistent(self):
        """Test file hash for non-existent file."""
        hash_result = compute_file_hash(Path("/nonexistent/file.txt"))
        assert hash_result is None


class TestComplexScenarios:
    """Tests for complex real-world scenarios."""

    def test_large_tree_performance(self):
        """Test performance with many files."""
        tree = MerkleTree()

        # Add 1000 files in various directories
        for i in range(1000):
            dir_idx = i % 10
            tree.add_file(f"dir{dir_idx}/file{i}.py", f"hash{i}")

        # Should be reasonably fast
        root_hash = tree.get_root_hash()
        assert root_hash != "empty"

        stats = tree.get_stats()
        assert stats["total_files"] == 1000
        assert stats["total_directories"] == 10

    def test_incremental_update_scenario(self):
        """Test typical incremental update workflow."""
        # Initial state
        old_tree = MerkleTree()
        old_tree.add_file("src/main.py", "hash1", chunk_hashes=["c1", "c2"])
        old_tree.add_file("src/utils.py", "hash2", chunk_hashes=["c3"])
        old_tree.add_file("tests/test_main.py", "hash3")

        # After some edits
        new_tree = MerkleTree()
        new_tree.add_file("src/main.py", "hash1_new", chunk_hashes=["c1", "c2_modified"])  # Modified
        new_tree.add_file("src/utils.py", "hash2", chunk_hashes=["c3"])  # Unchanged
        new_tree.add_file("src/helpers.py", "hash4")  # Added
        # tests/test_main.py removed

        added, removed, modified = new_tree.diff(old_tree)

        assert "src/helpers.py" in added
        assert "tests/test_main.py" in removed
        assert "src/main.py" in modified
        assert "src/utils.py" not in modified  # Unchanged

    def test_unchanged_subdirectory_not_traversed(self):
        """Test Merkle property: unchanged subtrees have same hash."""
        tree1 = MerkleTree()
        tree1.add_file("unchanged/a.py", "hash1")
        tree1.add_file("unchanged/b.py", "hash2")
        tree1.add_file("changed/c.py", "hash3")

        tree2 = MerkleTree()
        tree2.add_file("unchanged/a.py", "hash1")
        tree2.add_file("unchanged/b.py", "hash2")
        tree2.add_file("changed/c.py", "hash3_modified")

        # The unchanged directory should have same hash
        unchanged1 = tree1.root.subdirs["unchanged"]
        unchanged2 = tree2.root.subdirs["unchanged"]
        assert unchanged1.hash == unchanged2.hash

        # The changed directory should differ
        changed1 = tree1.root.subdirs["changed"]
        changed2 = tree2.root.subdirs["changed"]
        assert changed1.hash != changed2.hash
