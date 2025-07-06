from pathlib import Path
from typing import Annotated

import typer

from toygit.commands.add import add_files_sync
from toygit.commands.cat_file import cat_file_sync
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


@app.command(name="cat-file")
def cat_file(
    object_id: Annotated[str, typer.Argument(help="Object ID to show")],
    type: Annotated[
        bool, typer.Option("-t", "--type", help="Show object type")
    ] = False,
    size: Annotated[
        bool, typer.Option("-s", "--size", help="Show object size")
    ] = False,
    pretty: Annotated[
        bool, typer.Option("-p", "--pretty", help="Pretty-print object content")
    ] = False,
):
    """Show object content, type, or size."""
    current_path = Path.cwd()
    repo_path = _find_repository_root(current_path)
    cat_file_sync(
        object_id, repo_path, show_type=type, show_size=size, pretty_print=pretty
    )


def main():
    """Entry point for the toygit CLI."""
    app()


if __name__ == "__main__":
    main()
