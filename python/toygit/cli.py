from pathlib import Path
from typing import Annotated

import typer

from toygit.commands.add import add_files_sync
from toygit.commands.init import init_repository_sync


def _find_repository_root(start_path: Path) -> Path:
    """Find the repository root by looking for .git directory."""
    current_path = start_path.resolve()

    while current_path != current_path.parent:
        if (current_path / ".git").exists():
            return current_path
        current_path = current_path.parent

    # If we reach here, no .git directory was found
    raise RuntimeError(
        "fatal: not a git repository (or any of the parent directories): .git"
    )


app = typer.Typer(
    help="Toygit - A simple Git implementation in Python", no_args_is_help=True
)


@app.command()
def init(
    path: Annotated[
        str, typer.Argument(help="Directory to initialize as Git repository")
    ] = ".",
    force: Annotated[
        bool, typer.Option("--force", help="Reinitialize existing Git repository")
    ] = False,
):
    """Initialize a new Git repository."""
    repo_path = Path(path).resolve()
    init_repository_sync(repo_path, force=force)


@app.command()
def add(
    files: Annotated[
        list[str], typer.Argument(help="Files to add to the staging area")
    ],
):
    """Add files to the staging area."""
    # Find the repository root by looking for .git directory
    current_path = Path.cwd()
    repo_path = _find_repository_root(current_path)
    add_files_sync(files, repo_path)


def main():
    """Entry point for the toygit CLI."""
    app()


if __name__ == "__main__":
    main()
