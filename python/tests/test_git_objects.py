"""Unit tests for Git object models and parsing functions."""

import pytest
from datetime import datetime

from toygit.core.git_objects import (
    BlobObject,
    TreeObject,
    TreeEntry,
    CommitObject,
    TagObject,
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

    def test_blob_object_binary_content(self):
        """Test BlobObject with binary content."""
        content = b"\x00\x01\x02\xff"
        blob = BlobObject(
            object_id="af5626b4a114abcb82d63db7c8082c3c4756e51b",
            size=len(content),
            content=content,
        )

        assert blob.get_content_bytes() == content
        assert blob.pretty_print() == content.hex()

    def test_blob_object_empty_content(self):
        """Test BlobObject with empty content."""
        content = b""
        blob = BlobObject(
            object_id="e69de29bb2d1d6434b8b29ae775ad8c2e48c5391",
            size=0,
            content=content,
        )

        assert blob.get_content_bytes() == content
        assert blob.pretty_print() == ""

    def test_tree_entry_object_type_detection(self):
        """Test TreeEntry object type detection from mode."""
        # Regular file
        file_entry = TreeEntry(
            mode="100644",
            name="file.txt",
            object_id="af5626b4a114abcb82d63db7c8082c3c4756e51b",
        )
        assert file_entry.object_type == GitObjectType.BLOB

        # Executable file
        exec_entry = TreeEntry(
            mode="100755",
            name="script.sh",
            object_id="af5626b4a114abcb82d63db7c8082c3c4756e51b",
        )
        assert exec_entry.object_type == GitObjectType.BLOB

        # Directory
        dir_entry = TreeEntry(
            mode="040000",
            name="subdir",
            object_id="d8329fc1cc938780ffdd9f94e0d364e0ea74f579",
        )
        assert dir_entry.object_type == GitObjectType.TREE

        # Submodule
        submodule_entry = TreeEntry(
            mode="160000",
            name="submodule",
            object_id="123456789abcdef123456789abcdef1234567890",
        )
        assert submodule_entry.object_type == GitObjectType.COMMIT

        # Symlink
        symlink_entry = TreeEntry(
            mode="120000",
            name="symlink",
            object_id="af5626b4a114abcb82d63db7c8082c3c4756e51b",
        )
        assert symlink_entry.object_type == GitObjectType.BLOB

    def test_tree_entry_validation(self):
        """Test TreeEntry validation."""
        # Valid modes
        valid_modes = ["100644", "100755", "040000", "160000", "120000"]
        for mode in valid_modes:
            entry = TreeEntry(
                mode=mode,
                name="test",
                object_id="af5626b4a114abcb82d63db7c8082c3c4756e51b",
            )
            assert entry.mode == mode

        # Invalid mode
        with pytest.raises(ValueError):
            TreeEntry(
                mode="100666",
                name="test",
                object_id="af5626b4a114abcb82d63db7c8082c3c4756e51b",
            )

        # Invalid object_id
        with pytest.raises(ValueError):
            TreeEntry(
                mode="100644",
                name="test",
                object_id="invalid_hash",
            )

        # Empty name
        with pytest.raises(ValueError):
            TreeEntry(
                mode="100644",
                name="",
                object_id="af5626b4a114abcb82d63db7c8082c3c4756e51b",
            )

    def test_tree_object_serialization(self):
        """Test TreeObject content serialization."""
        entries = [
            TreeEntry(
                mode="100644",
                name="hello.txt",
                object_id="af5626b4a114abcb82d63db7c8082c3c4756e51b",
            ),
            TreeEntry(
                mode="040000",
                name="subdir",
                object_id="d8329fc1cc938780ffdd9f94e0d364e0ea74f579",
            ),
        ]

        tree = TreeObject(
            object_id="d8329fc1cc938780ffdd9f94e0d364e0ea74f579",
            size=74,
            entries=entries,
        )

        assert tree.type == GitObjectType.TREE
        content = tree.get_content_bytes()
        assert b"100644 hello.txt\x00" in content
        assert b"040000 subdir\x00" in content
        assert bytes.fromhex("af5626b4a114abcb82d63db7c8082c3c4756e51b") in content

    def test_tree_object_pretty_print(self):
        """Test TreeObject pretty print output."""
        entries = [
            TreeEntry(
                mode="100644",
                name="hello.txt",
                object_id="af5626b4a114abcb82d63db7c8082c3c4756e51b",
            ),
            TreeEntry(
                mode="040000",
                name="subdir",
                object_id="d8329fc1cc938780ffdd9f94e0d364e0ea74f579",
            ),
        ]

        tree = TreeObject(
            object_id="d8329fc1cc938780ffdd9f94e0d364e0ea74f579",
            size=74,
            entries=entries,
        )

        pretty = tree.pretty_print()
        assert (
            "100644 blob af5626b4a114abcb82d63db7c8082c3c4756e51b\thello.txt" in pretty
        )
        assert "040000 tree d8329fc1cc938780ffdd9f94e0d364e0ea74f579\tsubdir" in pretty

    def test_tree_object_empty(self):
        """Test TreeObject with no entries."""
        tree = TreeObject(
            object_id="4b825dc642cb6eb9a060e54bf8d69288fbee4904",
            size=0,
            entries=[],
        )

        assert tree.get_content_bytes() == b""
        assert tree.pretty_print() == ""

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

    def test_person_info_invalid_name(self):
        """Test PersonInfo with invalid name."""
        # Name with newline
        with pytest.raises(ValueError):
            PersonInfo(
                name="John\nDoe",
                email="john@example.com",
                timestamp=datetime.now(),
                timezone_offset="+0900",
            )

        # Name with angle brackets
        with pytest.raises(ValueError):
            PersonInfo(
                name="John <Doe>",
                email="john@example.com",
                timestamp=datetime.now(),
                timezone_offset="+0900",
            )

        # Empty name
        with pytest.raises(ValueError):
            PersonInfo(
                name="",
                email="john@example.com",
                timestamp=datetime.now(),
                timezone_offset="+0900",
            )

    def test_person_info_string_representation(self):
        """Test PersonInfo string representation."""
        person = PersonInfo(
            name="John Doe",
            email="john@example.com",
            timestamp=datetime.fromtimestamp(1234567890),
            timezone_offset="+0900",
        )

        expected = "John Doe <john@example.com> 1234567890 +0900"
        assert str(person) == expected

    def test_commit_object_structure(self):
        """Test CommitObject creation and serialization."""
        author = PersonInfo(
            name="John Doe",
            email="john@example.com",
            timestamp=datetime.fromtimestamp(1234567890),
            timezone_offset="+0000",
        )
        committer = PersonInfo(
            name="Jane Smith",
            email="jane@example.com",
            timestamp=datetime.fromtimestamp(1234567891),
            timezone_offset="+0900",
        )

        commit = CommitObject(
            object_id="123456789abcdef123456789abcdef1234567890",
            size=200,
            tree="af5626b4a114abcb82d63db7c8082c3c4756e51b",
            parents=[
                "parent1234567890abcdef123456789abcdef123",
                "parent2345678901bcdef234567890abcdef234",
            ],
            author=author,
            committer=committer,
            message="Initial commit\n\nThis is the first commit in the repository.",
        )

        assert commit.type == GitObjectType.COMMIT
        content = commit.get_content_bytes().decode("utf-8")
        assert "tree af5626b4a114abcb82d63db7c8082c3c4756e51b" in content
        assert "parent parent1234567890abcdef123456789abcdef123" in content
        assert "parent parent2345678901bcdef234567890abcdef234" in content
        assert "author John Doe <john@example.com> 1234567890 +0000" in content
        assert "committer Jane Smith <jane@example.com> 1234567891 +0900" in content
        assert (
            "Initial commit\n\nThis is the first commit in the repository." in content
        )

    def test_commit_object_no_parents(self):
        """Test CommitObject with no parents (root commit)."""
        author = PersonInfo(
            name="John Doe",
            email="john@example.com",
            timestamp=datetime.fromtimestamp(1234567890),
            timezone_offset="+0000",
        )

        commit = CommitObject(
            object_id="123456789abcdef123456789abcdef1234567890",
            size=150,
            tree="af5626b4a114abcb82d63db7c8082c3c4756e51b",
            parents=[],
            author=author,
            committer=author,
            message="Initial commit",
        )

        content = commit.get_content_bytes().decode("utf-8")
        assert "parent" not in content
        assert "tree af5626b4a114abcb82d63db7c8082c3c4756e51b" in content

    def test_commit_object_validation(self):
        """Test CommitObject validation."""
        author = PersonInfo(
            name="John Doe",
            email="john@example.com",
            timestamp=datetime.now(),
            timezone_offset="+0000",
        )

        # Invalid tree hash
        with pytest.raises(ValueError):
            CommitObject(
                object_id="123456789abcdef123456789abcdef1234567890",
                size=150,
                tree="invalid_hash",
                parents=[],
                author=author,
                committer=author,
                message="Test commit",
            )

    def test_tag_object_structure(self):
        """Test TagObject creation and serialization."""
        tagger = PersonInfo(
            name="John Doe",
            email="john@example.com",
            timestamp=datetime.fromtimestamp(1234567890),
            timezone_offset="+0000",
        )

        tag = TagObject(
            object_id="123456789abcdef123456789abcdef1234567890",
            size=150,
            object_ref="af5626b4a114abcb82d63db7c8082c3c4756e51b",
            object_type=GitObjectType.COMMIT,
            tag_name="v1.0.0",
            tagger=tagger,
            message="Release version 1.0.0",
        )

        assert tag.type == GitObjectType.TAG
        content = tag.get_content_bytes().decode("utf-8")
        assert "object af5626b4a114abcb82d63db7c8082c3c4756e51b" in content
        assert "type commit" in content
        assert "tag v1.0.0" in content
        assert "tagger John Doe <john@example.com> 1234567890 +0000" in content
        assert "Release version 1.0.0" in content

    def test_tag_object_validation(self):
        """Test TagObject validation."""
        tagger = PersonInfo(
            name="John Doe",
            email="john@example.com",
            timestamp=datetime.now(),
            timezone_offset="+0000",
        )

        # Invalid object reference
        with pytest.raises(ValueError):
            TagObject(
                object_id="123456789abcdef123456789abcdef1234567890",
                size=150,
                object_ref="invalid_hash",
                object_type=GitObjectType.COMMIT,
                tag_name="v1.0.0",
                tagger=tagger,
                message="Test tag",
            )

        # Empty tag name
        with pytest.raises(ValueError):
            TagObject(
                object_id="123456789abcdef123456789abcdef1234567890",
                size=150,
                object_ref="af5626b4a114abcb82d63db7c8082c3c4756e51b",
                object_type=GitObjectType.COMMIT,
                tag_name="",
                tagger=tagger,
                message="Test tag",
            )


class TestParsingFunctions:
    """Test parsing functions for Git objects."""

    def test_parse_tree_content(self):
        """Test tree content parsing."""
        # Create tree content: mode name\0 hash(20 bytes)
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
        assert entries[1].object_id == "d8329fc1cc938780ffdd9f94e0d364e0ea74f579"

    def test_parse_tree_content_empty(self):
        """Test parsing empty tree content."""
        entries = parse_tree_content(b"")
        assert len(entries) == 0

    def test_parse_tree_content_single_entry(self):
        """Test parsing tree content with single entry."""
        content = b"100755 script.sh\x00" + bytes.fromhex(
            "af5626b4a114abcb82d63db7c8082c3c4756e51b"
        )

        entries = parse_tree_content(content)

        assert len(entries) == 1
        assert entries[0].mode == "100755"
        assert entries[0].name == "script.sh"
        assert entries[0].object_id == "af5626b4a114abcb82d63db7c8082c3c4756e51b"

    def test_parse_tree_content_malformed(self):
        """Test parsing malformed tree content."""
        # Missing hash bytes
        content = b"100644 hello.txt\x00"
        entries = parse_tree_content(content)
        assert len(entries) == 0

        # Missing null separator
        content = b"100644 hello.txt" + bytes.fromhex(
            "af5626b4a114abcb82d63db7c8082c3c4756e51b"
        )
        entries = parse_tree_content(content)
        assert len(entries) == 0

    def test_parse_person_info(self):
        """Test person info string parsing."""
        person_str = "John Doe <john@example.com> 1234567890 +0900"
        person = parse_person_info(person_str)

        assert person.name == "John Doe"
        assert str(person.email) == "john@example.com"
        assert person.timestamp == datetime.fromtimestamp(1234567890)
        assert person.timezone_offset == "+0900"

    def test_parse_person_info_complex_name(self):
        """Test person info parsing with complex name."""
        person_str = "John Q. Doe Jr. <john.q.doe@example.com> 1234567890 -0500"
        person = parse_person_info(person_str)

        assert person.name == "John Q. Doe Jr."
        assert str(person.email) == "john.q.doe@example.com"
        assert person.timezone_offset == "-0500"

    def test_parse_person_info_invalid_format(self):
        """Test person info parsing with invalid format."""
        # Missing email brackets
        with pytest.raises(ValueError):
            parse_person_info("John Doe john@example.com 1234567890 +0900")

        # Missing timestamp
        with pytest.raises(ValueError):
            parse_person_info("John Doe <john@example.com> +0900")

        # Missing timezone
        with pytest.raises(ValueError):
            parse_person_info("John Doe <john@example.com> 1234567890")

        # Completely invalid format
        with pytest.raises(ValueError):
            parse_person_info("Invalid format")

    def test_parse_person_info_edge_cases(self):
        """Test person info parsing edge cases."""
        # Name with spaces
        person_str = "John   Doe <john@example.com> 1234567890 +0000"
        person = parse_person_info(person_str)
        assert person.name == "John   Doe"

        # Email with special characters
        person_str = "John Doe <john+test@example.co.uk> 1234567890 +0000"
        person = parse_person_info(person_str)
        assert str(person.email) == "john+test@example.co.uk"


class TestGitObjectEdgeCases:
    """Test edge cases and error conditions."""

    def test_blob_object_size_validation(self):
        """Test BlobObject size validation."""
        content = b"Hello, World!"

        # Test with correct size
        blob = BlobObject(
            object_id="af5626b4a114abcb82d63db7c8082c3c4756e51b",
            size=len(content),
            content=content,
        )
        assert blob.size == len(content)

    def test_tree_object_size_validation(self):
        """Test TreeObject size validation."""
        entries = [
            TreeEntry(
                mode="100644",
                name="test.txt",
                object_id="af5626b4a114abcb82d63db7c8082c3c4756e51b",
            )
        ]

        # Calculate expected size
        expected_size = len("100644 test.txt\0".encode()) + 20

        tree = TreeObject(
            object_id="d8329fc1cc938780ffdd9f94e0d364e0ea74f579",
            size=expected_size,
            entries=entries,
        )
        assert tree.size == expected_size

    def test_person_info_timezone_edge_cases(self):
        """Test PersonInfo timezone validation edge cases."""
        # Test maximum valid timezone
        person = PersonInfo(
            name="Test User",
            email="test@example.com",
            timestamp=datetime.now(),
            timezone_offset="+1400",
        )
        assert person.timezone_offset == "+1400"

        # Test minimum valid timezone
        person = PersonInfo(
            name="Test User",
            email="test@example.com",
            timestamp=datetime.now(),
            timezone_offset="-1400",
        )
        assert person.timezone_offset == "-1400"

        # Test invalid timezone format (Pydantic will raise ValidationError)
        with pytest.raises(pydantic.ValidationError):  # Expecting ValidationError
            PersonInfo(
                name="Test User",
                email="test@example.com",
                timestamp=datetime.now(),
                timezone_offset="invalid",
            )

        # Test invalid timezone minutes
        with pytest.raises(
            ValueError, match="Timezone offset minutes must be less than 60"
        ):
            PersonInfo(
                name="Test User",
                email="test@example.com",
                timestamp=datetime.now(),
                timezone_offset="+0260",
            )

    def test_tree_entry_mode_validation_edge_cases(self):
        """Test TreeEntry mode validation edge cases."""
        # Test all valid modes
        valid_modes = ["100644", "100755", "040000", "160000", "120000"]

        for mode in valid_modes:
            entry = TreeEntry(
                mode=mode,
                name="test",
                object_id="af5626b4a114abcb82d63db7c8082c3c4756e51b",
            )
            assert entry.mode == mode

        # Test invalid modes
        invalid_modes = ["100666", "777777", "123456", "000000"]

        for mode in invalid_modes:
            with pytest.raises(ValueError):
                TreeEntry(
                    mode=mode,
                    name="test",
                    object_id="af5626b4a114abcb82d63db7c8082c3c4756e51b",
                )

    def test_commit_object_multiple_parents(self):
        """Test CommitObject with multiple parents."""
        author = PersonInfo(
            name="John Doe",
            email="john@example.com",
            timestamp=datetime.fromtimestamp(1234567890),
            timezone_offset="+0000",
        )

        commit = CommitObject(
            object_id="123456789abcdef123456789abcdef1234567890",
            size=250,
            tree="af5626b4a114abcb82d63db7c8082c3c4756e51b",
            parents=[
                "parent1234567890abcdef123456789abcdef123",
                "parent2345678901bcdef234567890abcdef234",
                "parent3456789012cdef345678901bcdef345678",
            ],
            author=author,
            committer=author,
            message="Merge multiple branches",
        )

        content = commit.get_content_bytes().decode("utf-8")
        # Count "parent " (with space) to avoid matching "parent" in parent hashes
        assert content.count("parent ") == 3
        assert "parent parent1234567890abcdef123456789abcdef123" in content
        assert "parent parent2345678901bcdef234567890abcdef234" in content
        assert "parent parent3456789012cdef345678901bcdef345678" in content

    def test_tag_object_different_types(self):
        """Test TagObject with different referenced object types."""
        tagger = PersonInfo(
            name="John Doe",
            email="john@example.com",
            timestamp=datetime.fromtimestamp(1234567890),
            timezone_offset="+0000",
        )

        # Test tag pointing to blob
        tag = TagObject(
            object_id="123456789abcdef123456789abcdef1234567890",
            size=150,
            object_ref="af5626b4a114abcb82d63db7c8082c3c4756e51b",
            object_type=GitObjectType.BLOB,
            tag_name="file-v1.0",
            tagger=tagger,
            message="Tag for specific file version",
        )

        content = tag.get_content_bytes().decode("utf-8")
        assert "type blob" in content

        # Test tag pointing to tree
        tag = TagObject(
            object_id="123456789abcdef123456789abcdef1234567890",
            size=150,
            object_ref="af5626b4a114abcb82d63db7c8082c3c4756e51b",
            object_type=GitObjectType.TREE,
            tag_name="tree-v1.0",
            tagger=tagger,
            message="Tag for specific tree version",
        )

        content = tag.get_content_bytes().decode("utf-8")
        assert "type tree" in content

    def test_parse_tree_content_with_special_names(self):
        """Test parsing tree content with special file names."""
        # File with dots and underscores
        content = b"100644 file.name_with-special.chars\x00" + bytes.fromhex(
            "af5626b4a114abcb82d63db7c8082c3c4756e51b"
        )

        entries = parse_tree_content(content)
        assert len(entries) == 1
        assert entries[0].name == "file.name_with-special.chars"

        # File with numbers
        content = b"100644 file123.txt\x00" + bytes.fromhex(
            "af5626b4a114abcb82d63db7c8082c3c4756e51b"
        )

        entries = parse_tree_content(content)
        assert len(entries) == 1
        assert entries[0].name == "file123.txt"
