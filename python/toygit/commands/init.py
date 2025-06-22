"""Git init command implementation."""

from pathlib import Path


def init_repository(path: Path, force: bool = False) -> None:
    """Initialize a new Git repository.

    Args:
        path: Path where to initialize the repository
        force: If True, reinitialize existing Git repository

    Raises:
        FileNotFoundError: If the target directory doesn't exist
        PermissionError: If don't have write permissions
        FileExistsError: If .git directory already exists and force=False
    """
    if not path.exists():
        raise FileNotFoundError(f"Directory {path} does not exist")

    if not path.is_dir():
        raise ValueError(f"{path} is not a directory")

    # Check if .git directory already exists
    git_dir = path / ".git"
    if git_dir.exists() and not force:
        raise FileExistsError(
            f"Git repository already exists in {path}. Use --force to reinitialize."
        )

    # Create .git directory
    # exist_ok=True is safe here because we've already validated existence above
    git_dir.mkdir(exist_ok=True)

    # Create required subdirectories
    # exist_ok=True is safe for all subdirectories since parent is controlled
    (git_dir / "objects").mkdir(exist_ok=True)
    (git_dir / "refs").mkdir(exist_ok=True)
    (git_dir / "refs" / "heads").mkdir(exist_ok=True)
    (git_dir / "refs" / "tags").mkdir(exist_ok=True)

    # Create HEAD file pointing to main branch
    head_file = git_dir / "HEAD"
    head_file.write_text("ref: refs/heads/main\n")
