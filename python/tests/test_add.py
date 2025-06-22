import pytest

from toygit.commands.add import (
    add_files,
    _load_index,
    _save_index,
    _collect_files_to_add,
    _add_single_file,
)
from toygit.commands.init import init_repository


def test_add_single_file(tmp_path):
    """Test adding a single file to staging area."""
    # Initialize repository
    init_repository(tmp_path)

    # Create test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, world!")

    # Add file
    add_files(["test.txt"], tmp_path)

    # Check index file
    index_file = tmp_path / ".git" / "index"
    assert index_file.exists()

    index_content = index_file.read_text()
    assert "test.txt" in index_content

    # Check object was created
    objects_dir = tmp_path / ".git" / "objects"
    assert any(objects_dir.rglob("*"))


def test_add_multiple_files(tmp_path):
    """Test adding multiple files to staging area."""
    # Initialize repository
    init_repository(tmp_path)

    # Create test files
    file1 = tmp_path / "file1.txt"
    file1.write_text("Content 1")
    file2 = tmp_path / "file2.txt"
    file2.write_text("Content 2")

    # Add files
    add_files(["file1.txt", "file2.txt"], tmp_path)

    # Check index file
    index_file = tmp_path / ".git" / "index"
    index_content = index_file.read_text()
    assert "file1.txt" in index_content
    assert "file2.txt" in index_content


def test_add_directory(tmp_path):
    """Test adding a directory recursively."""
    # Initialize repository
    init_repository(tmp_path)

    # Create directory with files
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "file1.txt").write_text("Content 1")
    (subdir / "file2.txt").write_text("Content 2")

    # Add directory
    add_files(["subdir"], tmp_path)

    # Check index file
    index_file = tmp_path / ".git" / "index"
    index_content = index_file.read_text()
    assert "subdir/file1.txt" in index_content
    assert "subdir/file2.txt" in index_content


def test_add_nonexistent_file(tmp_path):
    """Test adding a file that doesn't exist."""
    # Initialize repository
    init_repository(tmp_path)

    # Add non-existent file (should not raise exception)
    add_files(["nonexistent.txt"], tmp_path)

    # Index should be empty or not exist
    index_file = tmp_path / ".git" / "index"
    if index_file.exists():
        assert index_file.read_text().strip() == ""


def test_add_not_in_repository(tmp_path):
    """Test adding files when not in a repository."""
    # Create test file without initializing repository
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, world!")

    # Should raise error
    with pytest.raises(RuntimeError, match="not a git repository"):
        add_files(["test.txt"], tmp_path)


def test_add_ignores_git_directory(tmp_path):
    """Test that .git directory is ignored."""
    # Initialize repository
    init_repository(tmp_path)

    # Create file in .git directory
    git_file = tmp_path / ".git" / "config"
    git_file.write_text("some config")

    # Add everything
    add_files(["."], tmp_path)

    # Check that .git files are not in index
    index_file = tmp_path / ".git" / "index"
    if index_file.exists():
        index_content = index_file.read_text()
        assert ".git" not in index_content


def test_add_same_file_twice(tmp_path):
    """Test adding the same file twice updates the index."""
    # Initialize repository
    init_repository(tmp_path)

    # Create test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Original content")

    # Add file first time
    add_files(["test.txt"], tmp_path)

    # Get first hash
    index_file = tmp_path / ".git" / "index"
    first_content = index_file.read_text()
    first_hash = first_content.split()[1]

    # Modify file and add again
    test_file.write_text("Modified content")
    add_files(["test.txt"], tmp_path)

    # Get second hash
    second_content = index_file.read_text()
    second_hash = second_content.split()[1]

    # Hashes should be different
    assert first_hash != second_hash
    # Should still have only one entry for the file
    assert second_content.count("test.txt") == 1


# Unit tests for individual functions


def test_load_index_empty_file(tmp_path):
    """Test loading index from non-existent file."""
    index_file = tmp_path / "index"
    index = _load_index(index_file)
    assert index == {}


def test_load_index_existing_file(tmp_path):
    """Test loading index from existing file."""
    index_file = tmp_path / "index"
    index_file.write_text("file1.txt abc123\nfile2.txt def456\n")

    index = _load_index(index_file)
    assert index == {"file1.txt": "abc123", "file2.txt": "def456"}


def test_load_index_with_empty_lines(tmp_path):
    """Test loading index with empty lines."""
    index_file = tmp_path / "index"
    index_file.write_text("file1.txt abc123\n\nfile2.txt def456\n\n")

    index = _load_index(index_file)
    assert index == {"file1.txt": "abc123", "file2.txt": "def456"}


def test_save_index_empty(tmp_path):
    """Test saving empty index."""
    index_file = tmp_path / "index"
    _save_index({}, index_file)

    assert index_file.read_text() == ""


def test_save_index_with_data(tmp_path):
    """Test saving index with data."""
    index_file = tmp_path / "index"
    index = {"file2.txt": "def456", "file1.txt": "abc123"}
    _save_index(index, index_file)

    content = index_file.read_text()
    # Should be sorted
    assert content == "file1.txt abc123\nfile2.txt def456\n"


def test_collect_files_single_file(tmp_path):
    """Test collecting single file."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")

    files = _collect_files_to_add(["test.txt"], tmp_path)
    assert files == ["test.txt"]


def test_collect_files_nonexistent_file(tmp_path, capsys):
    """Test collecting non-existent file."""
    files = _collect_files_to_add(["nonexistent.txt"], tmp_path)
    assert files == []

    captured = capsys.readouterr()
    assert "fatal: pathspec 'nonexistent.txt' did not match any files" in captured.out


def test_collect_files_directory(tmp_path):
    """Test collecting files from directory."""
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "file1.txt").write_text("content1")
    (subdir / "file2.txt").write_text("content2")

    files = _collect_files_to_add(["subdir"], tmp_path)
    assert set(files) == {"subdir/file1.txt", "subdir/file2.txt"}


def test_collect_files_ignores_git_directory(tmp_path):
    """Test that .git directory is ignored when collecting files."""
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text("config content")

    files = _collect_files_to_add([".git"], tmp_path)
    assert files == []


def test_add_single_file_unit(tmp_path):
    """Test _add_single_file function directly."""
    # Setup
    init_repository(tmp_path)
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, world!")

    objects_dir = tmp_path / ".git" / "objects"
    index = {}

    # Test
    _add_single_file("test.txt", tmp_path, objects_dir, index)

    # Verify
    assert "test.txt" in index
    assert len(index["test.txt"]) == 40  # SHA1 hash length

    # Verify object was created
    hash_value = index["test.txt"]
    obj_dir = objects_dir / hash_value[:2]
    obj_file = obj_dir / hash_value[2:]
    assert obj_file.exists()


def test_add_single_file_nonexistent(tmp_path, capsys):
    """Test _add_single_file with non-existent file."""
    objects_dir = tmp_path / "objects"
    objects_dir.mkdir()
    index = {}

    _add_single_file("nonexistent.txt", tmp_path, objects_dir, index)

    # Should not be added to index
    assert "nonexistent.txt" not in index

    # Should print error message
    captured = capsys.readouterr()
    assert "error: unable to read file 'nonexistent.txt'" in captured.out
