import os
import tempfile
import zlib
from pathlib import Path

from typer.testing import CliRunner

from toygit.cli import app
from toygit.commands.cat_file import cat_file_sync


class TestCatFile:
    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    def create_test_repo_with_objects(self, repo_path: Path):
        """Create a test repository with sample objects."""
        git_dir = repo_path / ".git"
        git_dir.mkdir()
        objects_dir = git_dir / "objects"
        objects_dir.mkdir()

        # Create a blob object
        blob_content = b"Hello, World!"
        blob_data = b"blob " + str(len(blob_content)).encode() + b"\0" + blob_content
        blob_hash = "af5626b4a114abcb82d63db7c8082c3c4756e51b"

        obj_dir = objects_dir / blob_hash[:2]
        obj_dir.mkdir()
        obj_file = obj_dir / blob_hash[2:]
        with open(obj_file, "wb") as f:
            f.write(zlib.compress(blob_data))

        # Create a tree object
        tree_content = b"100644 hello.txt\0" + bytes.fromhex(blob_hash)
        tree_data = b"tree " + str(len(tree_content)).encode() + b"\0" + tree_content
        tree_hash = "d8329fc1cc938780ffdd9f94e0d364e0ea74f579"

        obj_dir = objects_dir / tree_hash[:2]
        obj_dir.mkdir(exist_ok=True)
        obj_file = obj_dir / tree_hash[2:]
        with open(obj_file, "wb") as f:
            f.write(zlib.compress(tree_data))

        return blob_hash, tree_hash

    def test_cat_file_blob_content(self):
        """Test cat-file shows blob content by default."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            blob_hash, _ = self.create_test_repo_with_objects(repo_path)

            # Change directory to repo for testing
            original_cwd = os.getcwd()
            os.chdir(str(repo_path))
            try:
                result = self.runner.invoke(app, ["cat-file", blob_hash])
                assert result.exit_code == 0
                assert result.stdout == "Hello, World!"
            finally:
                os.chdir(original_cwd)

    def test_cat_file_show_type(self):
        """Test cat-file -t shows object type."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            blob_hash, tree_hash = self.create_test_repo_with_objects(repo_path)

            original_cwd = os.getcwd()
            os.chdir(str(repo_path))
            try:
                # Test blob type
                result = self.runner.invoke(app, ["cat-file", "-t", blob_hash])
                assert result.exit_code == 0
                assert result.stdout.strip() == "blob"

                # Test tree type
                result = self.runner.invoke(app, ["cat-file", "-t", tree_hash])
                assert result.exit_code == 0
                assert result.stdout.strip() == "tree"
            finally:
                os.chdir(original_cwd)

    def test_cat_file_show_size(self):
        """Test cat-file -s shows object size."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            blob_hash, tree_hash = self.create_test_repo_with_objects(repo_path)

            original_cwd = os.getcwd()
            os.chdir(str(repo_path))
            try:
                # Test blob size
                result = self.runner.invoke(app, ["cat-file", "-s", blob_hash])
                assert result.exit_code == 0
                assert result.stdout.strip() == "13"  # len("Hello, World!")

                # Test tree size
                result = self.runner.invoke(app, ["cat-file", "-s", tree_hash])
                assert result.exit_code == 0
                assert result.stdout.strip() == "37"  # tree object size
            finally:
                os.chdir(original_cwd)

    def test_cat_file_pretty_print_blob(self):
        """Test cat-file -p pretty prints blob content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            blob_hash, _ = self.create_test_repo_with_objects(repo_path)

            original_cwd = os.getcwd()
            os.chdir(str(repo_path))
            try:
                result = self.runner.invoke(app, ["cat-file", "-p", blob_hash])
                assert result.exit_code == 0
                assert result.stdout == "Hello, World!"
            finally:
                os.chdir(original_cwd)

    def test_cat_file_pretty_print_tree(self):
        """Test cat-file -p pretty prints tree content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            blob_hash, tree_hash = self.create_test_repo_with_objects(repo_path)

            original_cwd = os.getcwd()
            os.chdir(str(repo_path))
            try:
                result = self.runner.invoke(app, ["cat-file", "-p", tree_hash])
                assert result.exit_code == 0
                assert "100644 blob" in result.stdout
                assert "hello.txt" in result.stdout
                assert blob_hash in result.stdout
            finally:
                os.chdir(original_cwd)

    def test_cat_file_abbreviated_hash(self):
        """Test cat-file works with abbreviated hash."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            blob_hash, _ = self.create_test_repo_with_objects(repo_path)

            original_cwd = os.getcwd()
            os.chdir(str(repo_path))
            try:
                # Test with first 7 characters
                short_hash = blob_hash[:7]
                result = self.runner.invoke(app, ["cat-file", "-t", short_hash])
                assert result.exit_code == 0
                assert result.stdout.strip() == "blob"
            finally:
                os.chdir(original_cwd)

    def test_cat_file_invalid_object(self):
        """Test cat-file with invalid object ID."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            self.create_test_repo_with_objects(repo_path)

            original_cwd = os.getcwd()
            os.chdir(str(repo_path))
            try:
                result = self.runner.invoke(app, ["cat-file", "invalid_hash"])
                assert result.exit_code != 0
                # Error is caught by Typer and doesn't appear in stdout
                assert result.exit_code != 0
            finally:
                os.chdir(original_cwd)

    def test_cat_file_not_git_repo(self):
        """Test cat-file in directory that's not a git repo."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(str(temp_dir))
            try:
                result = self.runner.invoke(app, ["cat-file", "somehash"])
                assert result.exit_code != 0
                # Error is caught by Typer and doesn't appear in stdout
                assert result.exit_code != 0
            finally:
                os.chdir(original_cwd)

    def test_cat_file_sync_function(self):
        """Test the synchronous cat_file function directly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            blob_hash, _ = self.create_test_repo_with_objects(repo_path)

            # Test that function runs without error
            cat_file_sync(blob_hash, repo_path, show_type=True)
            cat_file_sync(blob_hash, repo_path, show_size=True)
            cat_file_sync(blob_hash, repo_path, pretty_print=True)

    def test_cat_file_ambiguous_hash(self):
        """Test cat-file with ambiguous abbreviated hash."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            git_dir = repo_path / ".git"
            git_dir.mkdir()
            objects_dir = git_dir / "objects"
            objects_dir.mkdir()

            # Create two objects with same prefix
            obj_dir = objects_dir / "ab"
            obj_dir.mkdir()

            # Create first object
            blob_data1 = b"blob 5\0test1"
            obj_file1 = obj_dir / "cdef1234567890123456789012345678"
            with open(obj_file1, "wb") as f:
                f.write(zlib.compress(blob_data1))

            # Create second object with same prefix
            blob_data2 = b"blob 5\0test2"
            obj_file2 = obj_dir / "cdef9876543210987654321098765432"
            with open(obj_file2, "wb") as f:
                f.write(zlib.compress(blob_data2))

            # Test ambiguous hash
            original_cwd = os.getcwd()
            os.chdir(str(repo_path))
            try:
                result = self.runner.invoke(app, ["cat-file", "abcdef"])
                assert result.exit_code != 0
                # Error is caught by Typer and doesn't appear in stdout
                assert result.exit_code != 0
            finally:
                os.chdir(original_cwd)
