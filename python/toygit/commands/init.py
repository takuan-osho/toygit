"""Git init command implementation."""

from pathlib import Path


def init_repository(path: Path) -> None:
    """Initialize a new Git repository.

    Args:
        path: Path where to initialize the repository

    Raises:
        FileNotFoundError: If the target directory doesn't exist
        PermissionError: If don't have write permissions
    """
    if not path.exists():
        raise FileNotFoundError(f"Directory {path} does not exist")

    if not path.is_dir():
        raise ValueError(f"{path} is not a directory")

    # Create .git directory
    git_dir = path / ".git"
    git_dir.mkdir(exist_ok=True)

    # Create required subdirectories
    (git_dir / "objects").mkdir(exist_ok=True)
    (git_dir / "refs").mkdir(exist_ok=True)
    (git_dir / "refs" / "heads").mkdir(exist_ok=True)
    (git_dir / "refs" / "tags").mkdir(exist_ok=True)

    # Create HEAD file pointing to main branch
    head_file = git_dir / "HEAD"
    head_file.write_text("ref: refs/heads/main\n")
