import pytest

from toygit.cli import _find_repository_root
from toygit.commands.init import init_repository


def test_find_repository_root_in_repo_root(tmp_path):
    """Test _find_repository_root when already in repository root."""
    # Initialize repository
    init_repository(tmp_path)

    # Should find the repository root
    result = _find_repository_root(tmp_path)
    assert result == tmp_path


def test_find_repository_root_in_subdirectory(tmp_path):
    """Test _find_repository_root from a subdirectory."""
    # Initialize repository
    init_repository(tmp_path)

    # Create subdirectory
    subdir = tmp_path / "subdir" / "nested"
    subdir.mkdir(parents=True)

    # Should find the repository root from subdirectory
    result = _find_repository_root(subdir)
    assert result == tmp_path


def test_find_repository_root_deeply_nested(tmp_path):
    """Test _find_repository_root from deeply nested subdirectory."""
    # Initialize repository
    init_repository(tmp_path)

    # Create deeply nested directory
    deep_dir = tmp_path / "a" / "b" / "c" / "d" / "e"
    deep_dir.mkdir(parents=True)

    # Should find the repository root from deep directory
    result = _find_repository_root(deep_dir)
    assert result == tmp_path


def test_find_repository_root_no_git_directory(tmp_path):
    """Test _find_repository_root raises error when no .git directory found."""
    # Create directory without .git
    test_dir = tmp_path / "no_git"
    test_dir.mkdir()

    # Should raise RuntimeError
    with pytest.raises(RuntimeError, match="fatal: not a git repository"):
        _find_repository_root(test_dir)


def test_find_repository_root_nested_git_repos(tmp_path):
    """Test _find_repository_root finds closest .git directory."""
    # Initialize outer repository
    init_repository(tmp_path)

    # Create inner directory and initialize another repository
    inner_dir = tmp_path / "inner"
    inner_dir.mkdir()
    init_repository(inner_dir)

    # Create subdirectory in inner repo
    inner_subdir = inner_dir / "subdir"
    inner_subdir.mkdir()

    # Should find the closest (inner) repository root
    result = _find_repository_root(inner_subdir)
    assert result == inner_dir


def test_find_repository_root_with_symlinks(tmp_path):
    """Test _find_repository_root resolves symlinks correctly."""
    # Initialize repository
    init_repository(tmp_path)

    # Create symlink to a subdirectory
    subdir = tmp_path / "subdir"
    subdir.mkdir()

    symlink_path = tmp_path / "symlink_to_subdir"
    symlink_path.symlink_to(subdir)

    # Should resolve symlink and find repository root
    result = _find_repository_root(symlink_path)
    assert result == tmp_path
