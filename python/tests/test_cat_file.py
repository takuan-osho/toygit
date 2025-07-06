"""Unit tests for cat-file command internal logic."""

import tempfile
import zlib
from pathlib import Path

import pytest

from toygit.commands.cat_file import (
    _parse_git_object,
    _resolve_abbreviated_hash,
    cat_file_sync,
)
from toygit.core.git_objects import (
    BlobObject,
    TreeObject,
    GitObjectType,
)


class TestCatFileInternalLogic:
    """Test cat-file internal functions."""

    def create_test_git_objects(self, objects_dir: Path):
        """Create test git objects in objects directory."""
        # Create blob object
        blob_content = b"Hello, World!"
        blob_data = b"blob " + str(len(blob_content)).encode() + b"\x00" + blob_content
        blob_hash = "af5626b4a114abcb82d63db7c8082c3c4756e51b"

        obj_dir = objects_dir / blob_hash[:2]
        obj_dir.mkdir(parents=True)
        obj_file = obj_dir / blob_hash[2:]
        with open(obj_file, "wb") as f:
            f.write(zlib.compress(blob_data))

        # Create tree object
        tree_content = b"100644 hello.txt\x00" + bytes.fromhex(blob_hash)
        tree_data = b"tree " + str(len(tree_content)).encode() + b"\x00" + tree_content
        tree_hash = "d8329fc1cc938780ffdd9f94e0d364e0ea74f579"

        obj_dir = objects_dir / tree_hash[:2]
        obj_dir.mkdir(exist_ok=True)
        obj_file = obj_dir / tree_hash[2:]
        with open(obj_file, "wb") as f:
            f.write(zlib.compress(tree_data))

        return blob_hash, tree_hash

    def test_parse_git_object_blob(self):
        """Test parsing blob object."""
        with tempfile.TemporaryDirectory() as temp_dir:
            objects_dir = Path(temp_dir) / "objects"
            blob_hash, _ = self.create_test_git_objects(objects_dir)

            # Use asyncio.run to test async function
            import asyncio

            git_object = asyncio.run(_parse_git_object(blob_hash, objects_dir))

            assert isinstance(git_object, BlobObject)
            assert git_object.type == GitObjectType.BLOB
            assert git_object.get_content_bytes() == b"Hello, World!"

    def test_parse_git_object_tree(self):
        """Test parsing tree object."""
        with tempfile.TemporaryDirectory() as temp_dir:
            objects_dir = Path(temp_dir) / "objects"
            _, tree_hash = self.create_test_git_objects(objects_dir)

            import asyncio

            git_object = asyncio.run(_parse_git_object(tree_hash, objects_dir))

            assert isinstance(git_object, TreeObject)
            assert git_object.type == GitObjectType.TREE
            assert len(git_object.entries) == 1
            assert git_object.entries[0].name == "hello.txt"

    def test_resolve_abbreviated_hash(self):
        """Test abbreviated hash resolution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            objects_dir = Path(temp_dir) / "objects"
            blob_hash, _ = self.create_test_git_objects(objects_dir)

            import asyncio

            resolved = asyncio.run(
                _resolve_abbreviated_hash(blob_hash[:7], objects_dir)
            )
            assert resolved == blob_hash

    def test_resolve_abbreviated_hash_not_found(self):
        """Test abbreviated hash resolution with non-existent hash."""
        with tempfile.TemporaryDirectory() as temp_dir:
            objects_dir = Path(temp_dir) / "objects"
            objects_dir.mkdir()

            import asyncio

            with pytest.raises(RuntimeError, match="Not a valid object name"):
                asyncio.run(_resolve_abbreviated_hash("nonexistent", objects_dir))

    def test_cat_file_sync_function(self):
        """Test synchronous cat_file wrapper function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            git_dir = repo_path / ".git"
            git_dir.mkdir()

            objects_dir = git_dir / "objects"
            blob_hash, _ = self.create_test_git_objects(objects_dir)

            # Test that function runs without error (output verification in CLI tests)
            cat_file_sync(blob_hash, repo_path, show_type=True)
            cat_file_sync(blob_hash, repo_path, show_size=True)
            cat_file_sync(blob_hash, repo_path, pretty_print=True)
