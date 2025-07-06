"""Unit tests for cat-file internal logic and Git object models."""

import tempfile
import zlib
from datetime import datetime
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
    TreeEntry,
    CommitObject,
    PersonInfo,
    GitObjectType,
    parse_tree_content,
    parse_person_info,
)


class TestGitObjectModels:
    """Test Git object Pydantic models."""

    def test_blob_object_creation(self):
        """Test BlobObject creation and properties."""
        content = b"Hello, World!"
        blob = BlobObject(
            object_id="af5626b4a114abcb82d63db7c8082c3c4756e51b",
            size=len(content),
            content=content,
        )

        assert blob.type == GitObjectType.BLOB
        assert blob.get_content_bytes() == content
        assert blob.pretty_print() == "Hello, World!"

    def test_tree_entry_object_type_detection(self):
        """Test TreeEntry object type detection from mode."""
        # File entry
        file_entry = TreeEntry(
            mode="100644",
            name="file.txt",
            object_id="af5626b4a114abcb82d63db7c8082c3c4756e51b",
        )
        assert file_entry.object_type == GitObjectType.BLOB

        # Directory entry
        dir_entry = TreeEntry(
            mode="040000",
            name="subdir",
            object_id="d8329fc1cc938780ffdd9f94e0d364e0ea74f579",
        )
        assert dir_entry.object_type == GitObjectType.TREE

        # Submodule entry
        submodule_entry = TreeEntry(
            mode="160000",
            name="submodule",
            object_id="123456789abcdef123456789abcdef1234567890",
        )
        assert submodule_entry.object_type == GitObjectType.COMMIT

    def test_tree_object_serialization(self):
        """Test TreeObject content serialization."""
        entries = [
            TreeEntry(
                mode="100644",
                name="hello.txt",
                object_id="af5626b4a114abcb82d63db7c8082c3c4756e51b",
            )
        ]

        tree = TreeObject(
            object_id="d8329fc1cc938780ffdd9f94e0d364e0ea74f579",
            size=37,
            entries=entries,
        )

        assert tree.type == GitObjectType.TREE
        content = tree.get_content_bytes()
        assert b"100644 hello.txt\x00" in content
        assert bytes.fromhex("af5626b4a114abcb82d63db7c8082c3c4756e51b") in content

    def test_person_info_validation(self):
        """Test PersonInfo validation and formatting."""
        person = PersonInfo(
            name="John Doe",
            email="john.doe@example.com",
            timestamp=datetime.fromtimestamp(1234567890),
            timezone_offset="+0900",
        )

        assert person.name == "John Doe"
        assert str(person.email) == "john.doe@example.com"
        assert person.timezone_offset == "+0900"
        assert person.timezone_info == "+09:00"

    def test_person_info_invalid_email(self):
        """Test PersonInfo with invalid email."""
        with pytest.raises(ValueError):
            PersonInfo(
                name="John Doe",
                email="invalid-email",
                timestamp=datetime.now(),
                timezone_offset="+0900",
            )

    def test_person_info_invalid_timezone(self):
        """Test PersonInfo with invalid timezone."""
        with pytest.raises(ValueError):
            PersonInfo(
                name="John Doe",
                email="john@example.com",
                timestamp=datetime.now(),
                timezone_offset="+2500",  # Invalid: exceeds +14:00
            )

    def test_commit_object_structure(self):
        """Test CommitObject creation and serialization."""
        author = PersonInfo(
            name="John Doe",
            email="john@example.com",
            timestamp=datetime.fromtimestamp(1234567890),
            timezone_offset="+0000",
        )

        commit = CommitObject(
            object_id="123456789abcdef123456789abcdef1234567890",
            size=200,
            tree="af5626b4a114abcb82d63db7c8082c3c4756e51b",
            parents=["parent1234567890abcdef123456789abcdef123"],
            author=author,
            committer=author,
            message="Initial commit",
        )

        assert commit.type == GitObjectType.COMMIT
        content = commit.get_content_bytes().decode("utf-8")
        assert "tree af5626b4a114abcb82d63db7c8082c3c4756e51b" in content
        assert "parent parent1234567890abcdef123456789abcdef123" in content
        assert "Initial commit" in content


class TestParsingFunctions:
    """Test parsing functions for Git objects."""

    def test_parse_tree_content(self):
        """Test tree content parsing."""
        # Create tree content: mode name\\0 hash(20 bytes)
        content = b"100644 hello.txt\x00" + bytes.fromhex(
            "af5626b4a114abcb82d63db7c8082c3c4756e51b"
        )
        content += b"040000 subdir\x00" + bytes.fromhex(
            "d8329fc1cc938780ffdd9f94e0d364e0ea74f579"
        )

        entries = parse_tree_content(content)

        assert len(entries) == 2
        assert entries[0].mode == "100644"
        assert entries[0].name == "hello.txt"
        assert entries[0].object_id == "af5626b4a114abcb82d63db7c8082c3c4756e51b"
        assert entries[1].mode == "040000"
        assert entries[1].name == "subdir"

    def test_parse_person_info(self):
        """Test person info string parsing."""
        person_str = "John Doe <john@example.com> 1234567890 +0900"
        person = parse_person_info(person_str)

        assert person.name == "John Doe"
        assert str(person.email) == "john@example.com"
        assert person.timestamp == datetime.fromtimestamp(1234567890)
        assert person.timezone_offset == "+0900"

    def test_parse_person_info_invalid_format(self):
        """Test person info parsing with invalid format."""
        with pytest.raises(ValueError):
            parse_person_info("Invalid format")


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
