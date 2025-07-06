"""Tests for git init command."""

import os
import tempfile
from pathlib import Path

import pytest

from toygit.commands.init import init_repository


class TestInitCommand:
    """Test cases for git init command."""

    @pytest.mark.asyncio
    async def test_init_creates_git_directory(self):
        """Test that init creates .git directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Run init command
            await init_repository(repo_path)

            # Check that .git directory was created
            git_dir = repo_path / ".git"
            assert git_dir.exists()
            assert git_dir.is_dir()

    @pytest.mark.asyncio
    async def test_init_creates_required_subdirectories(self):
        """Test that init creates required Git subdirectories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Run init command
            await init_repository(repo_path)

            git_dir = repo_path / ".git"

            # Check required subdirectories
            required_dirs = ["objects", "refs", "refs/heads", "refs/tags"]
            for dir_name in required_dirs:
                dir_path = git_dir / dir_name
                assert dir_path.exists(), f"Directory {dir_name} should exist"
                assert dir_path.is_dir(), f"{dir_name} should be a directory"

    @pytest.mark.asyncio
    async def test_init_creates_head_file(self):
        """Test that init creates HEAD file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Run init command
            await init_repository(repo_path)

            # Check HEAD file
            head_file = repo_path / ".git" / "HEAD"
            assert head_file.exists()
            assert head_file.is_file()

            # Check HEAD content
            content = head_file.read_text().strip()
            assert content == "ref: refs/heads/main"

    @pytest.mark.asyncio
    async def test_init_in_existing_git_repo_fails_without_force(self):
        """Test that init fails in existing Git repository without --force."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Initialize once
            await init_repository(repo_path)

            # Initialize again without force (should fail)
            with pytest.raises(FileExistsError, match="Git repository already exists"):
                await init_repository(repo_path, force=False)

            # Check that .git directory still exists
            git_dir = repo_path / ".git"
            assert git_dir.exists()

    @pytest.mark.asyncio
    async def test_init_in_existing_git_repo_succeeds_with_force(self):
        """Test that init succeeds in existing Git repository with force=True."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Initialize once
            await init_repository(repo_path)

            # Initialize again with force (should succeed)
            await init_repository(repo_path, force=True)

            # Check that .git directory still exists
            git_dir = repo_path / ".git"
            assert git_dir.exists()

    @pytest.mark.asyncio
    async def test_init_force_flag_with_new_repository(self):
        """Test that force flag works correctly with new repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Initialize with force=True (should succeed even for new repo)
            await init_repository(repo_path, force=True)

            # Check that .git directory was created
            git_dir = repo_path / ".git"
            assert git_dir.exists()
            assert git_dir.is_dir()

    @pytest.mark.asyncio
    async def test_init_in_nonexistent_directory(self):
        """Test that init fails gracefully with nonexistent directory."""
        nonexistent_path = Path("/nonexistent/directory")

        with pytest.raises(FileNotFoundError):
            await init_repository(nonexistent_path)

    @pytest.mark.asyncio
    async def test_init_with_no_permissions(self):
        """Test that init fails gracefully with no write permissions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Remove write permissions
            os.chmod(repo_path, 0o444)

            try:
                with pytest.raises(PermissionError):
                    await init_repository(repo_path)
            finally:
                # Restore permissions for cleanup
                os.chmod(repo_path, 0o755)
