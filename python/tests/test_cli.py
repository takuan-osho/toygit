import re
from pathlib import Path

import pytest
from click.testing import Result
from typer.testing import CliRunner

from toygit.cli import _find_repository_root, app
from toygit.commands.init import init_repository_sync


def strip_ansi_codes(text: str) -> str:
    """Remove ANSI escape sequences from text.

    This is a workaround for ANSI color codes appearing in CLI test output
    in GitHub Actions environment. Environment variables like NO_COLOR and
    PY_COLORS do not seem to work reliably in GHA with Typer's CliRunner.

    Related issues:
    - https://github.com/tiangolo/typer/issues/231
    - https://github.com/pallets/click/issues/2227
    """
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


# Initialize the CLI runner for testing
runner = CliRunner()


class TestCliCommands:
    """Test CLI commands using Typer's testing framework."""

    def test_cli_init_command_basic(self):
        """Test basic 'toygit init' command."""
        with runner.isolated_filesystem():
            result: Result = runner.invoke(app, ["init"])

            assert result.exit_code == 0
            assert Path(".git").exists()
            assert Path(".git").is_dir()
            # Check required subdirectories were created
            assert (Path(".git") / "objects").exists()
            assert (Path(".git") / "refs" / "heads").exists()
            assert (Path(".git") / "HEAD").exists()

    def test_cli_init_command_with_path(self):
        """Test 'toygit init' with specific path."""
        with runner.isolated_filesystem():
            # Create the directory first
            Path("test_repo").mkdir()
            result: Result = runner.invoke(app, ["init", "test_repo"])

            assert result.exit_code == 0
            assert Path("test_repo/.git").exists()
            assert Path("test_repo/.git").is_dir()
            # Check required subdirectories were created
            assert (Path("test_repo/.git") / "objects").exists()
            assert (Path("test_repo/.git") / "refs" / "heads").exists()
            assert (Path("test_repo/.git") / "HEAD").exists()

    def test_cli_init_command_with_force(self):
        """Test 'toygit init --force' command."""
        with runner.isolated_filesystem():
            # Initialize first time
            result1: Result = runner.invoke(app, ["init"])
            assert result1.exit_code == 0

            # Initialize again with --force
            result2: Result = runner.invoke(app, ["init", "--force"])
            assert result2.exit_code == 0
            # Repository should still exist and be functional
            assert Path(".git").exists()
            assert Path(".git").is_dir()
            assert (Path(".git") / "HEAD").exists()

    def test_cli_init_command_existing_repo_without_force(self):
        """Test 'toygit init' fails on existing repo without --force."""
        with runner.isolated_filesystem():
            # Initialize first time
            result1: Result = runner.invoke(app, ["init"])
            assert result1.exit_code == 0

            # Initialize again without --force (should fail)
            result2: Result = runner.invoke(app, ["init"])
            assert result2.exit_code != 0
            # Check that the error is the expected FileExistsError
            assert result2.exception is not None
            assert isinstance(result2.exception, FileExistsError)
            assert "already exists" in str(result2.exception)

    def test_cli_add_command_single_file(self):
        """Test 'toygit add' with single file."""
        with runner.isolated_filesystem():
            # Initialize repository
            init_result = runner.invoke(app, ["init"])
            assert init_result.exit_code == 0

            # Create test file
            test_file = Path("test.txt")
            test_file.write_text("Hello, world!")

            # Add file
            result = runner.invoke(app, ["add", "test.txt"])
            assert result.exit_code == 0

            # Check index was created
            index_file = Path(".git/index")
            assert index_file.exists()
            assert "test.txt" in index_file.read_text()

    def test_cli_add_command_multiple_files(self):
        """Test 'toygit add' with multiple files."""
        with runner.isolated_filesystem():
            # Initialize repository
            init_result = runner.invoke(app, ["init"])
            assert init_result.exit_code == 0

            # Create test files
            Path("file1.txt").write_text("Content 1")
            Path("file2.txt").write_text("Content 2")

            # Add files
            result = runner.invoke(app, ["add", "file1.txt", "file2.txt"])
            assert result.exit_code == 0

            # Check index contains both files
            index_content = Path(".git/index").read_text()
            assert "file1.txt" in index_content
            assert "file2.txt" in index_content

    def test_cli_add_command_nonexistent_file(self):
        """Test 'toygit add' with non-existent file."""
        with runner.isolated_filesystem():
            # Initialize repository
            init_result = runner.invoke(app, ["init"])
            assert init_result.exit_code == 0

            # Add non-existent file
            result = runner.invoke(app, ["add", "nonexistent.txt"])
            assert result.exit_code == 0  # Command succeeds but shows warning
            assert "did not match any files" in result.output

    def test_cli_add_command_outside_repository(self):
        """Test 'toygit add' fails when not in a repository."""
        with runner.isolated_filesystem():
            # Create test file without initializing repository
            Path("test.txt").write_text("content")

            # Add file (should fail)
            result = runner.invoke(app, ["add", "test.txt"])
            assert result.exit_code != 0
            # Check that the error is the expected RuntimeError
            assert isinstance(result.exception, RuntimeError)
            assert "not a git repository" in str(result.exception)

    def test_cli_add_command_directory(self):
        """Test 'toygit add' with directory."""
        with runner.isolated_filesystem():
            # Initialize repository
            init_result = runner.invoke(app, ["init"])
            assert init_result.exit_code == 0

            # Create directory with files
            subdir = Path("subdir")
            subdir.mkdir()
            (subdir / "file1.txt").write_text("Content 1")
            (subdir / "file2.txt").write_text("Content 2")

            # Add directory
            result = runner.invoke(app, ["add", "subdir"])
            assert result.exit_code == 0

            # Check index contains directory files
            index_content = Path(".git/index").read_text()
            assert "subdir/file1.txt" in index_content
            assert "subdir/file2.txt" in index_content

    def test_cli_help_command(self):
        """Test CLI help functionality."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        # Strip ANSI codes since environment variables don't work reliably in GHA
        clean_output = strip_ansi_codes(result.output)
        assert "Toygit - A simple Git implementation" in clean_output
        assert "Commands" in clean_output
        assert "init" in clean_output
        assert "add" in clean_output

    def test_cli_init_help(self):
        """Test 'toygit init --help' command."""
        result = runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0
        # Strip ANSI codes since environment variables don't work reliably in GHA
        clean_output = strip_ansi_codes(result.output)
        assert "Initialize a new Git repository" in clean_output
        assert "--force" in clean_output

    def test_cli_add_help(self):
        """Test 'toygit add --help' command."""
        result = runner.invoke(app, ["add", "--help"])
        assert result.exit_code == 0
        # Strip ANSI codes since environment variables don't work reliably in GHA
        clean_output = strip_ansi_codes(result.output)
        assert "Add files to the staging area" in clean_output

    def test_cli_no_args_shows_help(self):
        """Test that running toygit without arguments shows help."""
        result = runner.invoke(app, [])
        # Typer returns exit code 2 for no args when no_args_is_help=True
        assert result.exit_code == 2
        # Strip ANSI codes since environment variables don't work reliably in GHA
        clean_output = strip_ansi_codes(result.output)
        assert "Usage:" in clean_output
        assert "Commands" in clean_output


class TestFindRepositoryRoot:
    """Test _find_repository_root function."""

    def test_find_repository_root_in_repo_root(self, tmp_path):
        """Test _find_repository_root when already in repository root."""
        # Initialize repository
        init_repository_sync(tmp_path)

        # Should find the repository root
        result = _find_repository_root(tmp_path)
        assert result == tmp_path

    def test_find_repository_root_in_subdirectory(self, tmp_path):
        """Test _find_repository_root from a subdirectory."""
        # Initialize repository
        init_repository_sync(tmp_path)

        # Create subdirectory
        subdir = tmp_path / "subdir" / "nested"
        subdir.mkdir(parents=True)

        # Should find the repository root from subdirectory
        result = _find_repository_root(subdir)
        assert result == tmp_path

    def test_find_repository_root_deeply_nested(self, tmp_path):
        """Test _find_repository_root from deeply nested subdirectory."""
        # Initialize repository
        init_repository_sync(tmp_path)

        # Create deeply nested directory
        deep_dir = tmp_path / "a" / "b" / "c" / "d" / "e"
        deep_dir.mkdir(parents=True)

        # Should find the repository root from deep directory
        result = _find_repository_root(deep_dir)
        assert result == tmp_path

    def test_find_repository_root_no_git_directory(self, tmp_path):
        """Test _find_repository_root raises error when no .git directory found."""
        # Create directory without .git
        test_dir = tmp_path / "no_git"
        test_dir.mkdir()

        # Should raise RuntimeError
        with pytest.raises(RuntimeError, match="fatal: not a git repository"):
            _find_repository_root(test_dir)

    def test_find_repository_root_nested_git_repos(self, tmp_path):
        """Test _find_repository_root finds closest .git directory."""
        # Initialize outer repository
        init_repository_sync(tmp_path)

        # Create inner directory and initialize another repository
        inner_dir = tmp_path / "inner"
        inner_dir.mkdir()
        init_repository_sync(inner_dir)

        # Create subdirectory in inner repo
        inner_subdir = inner_dir / "subdir"
        inner_subdir.mkdir()

        # Should find the closest (inner) repository root
        result = _find_repository_root(inner_subdir)
        assert result == inner_dir

    def test_find_repository_root_with_symlinks(self, tmp_path):
        """Test _find_repository_root resolves symlinks correctly."""
        # Initialize repository
        init_repository_sync(tmp_path)

        # Create symlink to a subdirectory
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        symlink_path = tmp_path / "symlink_to_subdir"
        symlink_path.symlink_to(subdir)

        # Verify symlink was created successfully
        assert symlink_path.is_symlink()

        # Should resolve symlink and find repository root
        result = _find_repository_root(symlink_path)
        assert result == tmp_path


class TestCliIntegration:
    """Integration tests for CLI commands."""

    def test_init_then_add_workflow(self):
        """Test complete workflow: init -> add files."""
        with runner.isolated_filesystem():
            # Initialize repository
            init_result = runner.invoke(app, ["init"])
            assert init_result.exit_code == 0

            # Create multiple files
            Path("README.md").write_text("# Test Repository")
            Path("main.py").write_text("print('Hello, World!')")

            # Add files one by one
            add_result1: Result = runner.invoke(app, ["add", "README.md"])
            assert add_result1.exit_code == 0

            add_result2: Result = runner.invoke(app, ["add", "main.py"])
            assert add_result2.exit_code == 0

            # Verify both files are in index
            index_content = Path(".git/index").read_text()
            assert "README.md" in index_content
            assert "main.py" in index_content

    def test_init_nested_directory_then_add(self):
        """Test init in nested directory, then add files."""
        with runner.isolated_filesystem():
            # Create nested directory
            nested_path = Path("projects/myproject")
            nested_path.mkdir(parents=True)

            # Initialize repository in nested directory
            init_result = runner.invoke(app, ["init", "projects/myproject"])
            assert init_result.exit_code == 0

            # Create file in the repository
            (nested_path / "test.txt").write_text("test content")

            # Use os.chdir() with proper isolation for this test
            # Note: This is necessary because the CLI needs to be run from within
            # the git repository directory to find the .git folder
            import os

            original_cwd = os.getcwd()
            try:
                os.chdir(nested_path)
                add_result: Result = runner.invoke(app, ["add", "test.txt"])
                assert add_result.exit_code == 0

                # Verify file is in index
                index_content = Path(".git/index").read_text()
                assert "test.txt" in index_content
            finally:
                os.chdir(original_cwd)

    def test_add_from_subdirectory(self):
        """Test adding files from subdirectory of repository."""
        with runner.isolated_filesystem():
            # Initialize repository
            init_result: Result = runner.invoke(app, ["init"])
            assert init_result.exit_code == 0

            # Create subdirectory with files
            subdir = Path("src")
            subdir.mkdir()
            (subdir / "main.py").write_text("print('Hello from src!')")

            # Add files from root directory with relative path
            add_result: Result = runner.invoke(app, ["add", "src/main.py"])
            assert add_result.exit_code == 0

            # Verify file is in index with correct path
            index_file = Path(".git/index")
            assert index_file.exists(), "Index file should exist after adding files"
            index_content = index_file.read_text()
            assert "src/main.py" in index_content


class TestCatFileCLI:
    """Test cat-file command through CLI interface."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    def create_test_repo_with_files(self):
        """Create a test repository with files and objects."""
        # Initialize repository
        init_result = self.runner.invoke(app, ["init"])
        assert init_result.exit_code == 0

        # Create and add files
        test_file = Path("hello.txt")
        test_file.write_text("Hello, World!")

        add_result = self.runner.invoke(app, ["add", "hello.txt"])
        assert add_result.exit_code == 0

        # Get blob hash from index
        index_file = Path(".git/index")
        index_content = index_file.read_text()

        # Find lines that contain "hello.txt" and extract hash
        for line in index_content.split("\n"):
            if "hello.txt" in line:
                parts = line.split()
                if len(parts) >= 2:
                    # The hash should be a 40-character hex string
                    for part in parts:
                        if len(part) == 40 and all(
                            c in "0123456789abcdef" for c in part
                        ):
                            return part
        raise RuntimeError("No hash found in index")

    def test_cat_file_help(self):
        """Test cat-file command help."""
        result = self.runner.invoke(app, ["cat-file", "--help"])
        assert result.exit_code == 0
        help_text = strip_ansi_codes(result.stdout)
        assert "Show object content, type, or size" in help_text
        assert "--type" in help_text
        assert "--size" in help_text
        assert "--pretty" in help_text

    def test_cat_file_show_type(self):
        """Test cat-file -t shows object type."""
        with self.runner.isolated_filesystem():
            blob_hash = self.create_test_repo_with_files()

            result = self.runner.invoke(app, ["cat-file", "-t", blob_hash])
            assert result.exit_code == 0
            assert result.stdout.strip() == "blob"

    def test_cat_file_show_size(self):
        """Test cat-file -s shows object size."""
        with self.runner.isolated_filesystem():
            blob_hash = self.create_test_repo_with_files()

            result = self.runner.invoke(app, ["cat-file", "-s", blob_hash])
            assert result.exit_code == 0
            assert result.stdout.strip() == "13"  # len("Hello, World!")

    def test_cat_file_pretty_print(self):
        """Test cat-file -p pretty prints content."""
        with self.runner.isolated_filesystem():
            blob_hash = self.create_test_repo_with_files()

            result = self.runner.invoke(app, ["cat-file", "-p", blob_hash])
            assert result.exit_code == 0
            assert result.stdout == "Hello, World!"

    def test_cat_file_default_content(self):
        """Test cat-file shows content by default."""
        with self.runner.isolated_filesystem():
            blob_hash = self.create_test_repo_with_files()

            result = self.runner.invoke(app, ["cat-file", blob_hash])
            assert result.exit_code == 0
            assert result.stdout == "Hello, World!"

    def test_cat_file_abbreviated_hash(self):
        """Test cat-file works with abbreviated hash."""
        with self.runner.isolated_filesystem():
            blob_hash = self.create_test_repo_with_files()
            short_hash = blob_hash[:7]

            result = self.runner.invoke(app, ["cat-file", "-t", short_hash])
            assert result.exit_code == 0
            assert result.stdout.strip() == "blob"

    def test_cat_file_invalid_object(self):
        """Test cat-file with invalid object ID."""
        with self.runner.isolated_filesystem():
            self.create_test_repo_with_files()

            result = self.runner.invoke(app, ["cat-file", "invalid_hash"])
            assert result.exit_code != 0

    def test_cat_file_not_git_repo(self):
        """Test cat-file in directory that's not a git repo."""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(app, ["cat-file", "somehash"])
            assert result.exit_code != 0
