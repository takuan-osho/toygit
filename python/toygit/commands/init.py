"""Git init command implementation."""

import asyncio
from pathlib import Path

import aiofiles


async def init_repository(path: Path, force: bool = False) -> None:
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

    try:
        # Create .git directory
        # exist_ok=True is safe here because we've already validated existence above
        # Create .git directory
        if git_dir.exists() and force:
            import shutil

            shutil.rmtree(git_dir)
        git_dir.mkdir(exist_ok=True)

        # Create required subdirectories in proper dependency order
        # First create independent directories
        await asyncio.gather(
            asyncio.to_thread((git_dir / "objects").mkdir, exist_ok=True),
            asyncio.to_thread((git_dir / "refs").mkdir, exist_ok=True),
        )

        # Then create subdirectories that depend on refs
        await asyncio.gather(
            asyncio.to_thread((git_dir / "refs" / "heads").mkdir, exist_ok=True),
            asyncio.to_thread((git_dir / "refs" / "tags").mkdir, exist_ok=True),
        )

        # Create HEAD file pointing to main branch
        head_file = git_dir / "HEAD"
        async with aiofiles.open(head_file, "w") as f:
            await f.write("ref: refs/heads/main\n")
    except PermissionError as e:
        raise PermissionError(
            f"Permission denied: Cannot create Git repository in {path}. {e}"
        ) from e


def init_repository_sync(path: Path, force: bool = False) -> None:
    """Synchronous wrapper for init_repository."""
    asyncio.run(init_repository(path, force))
