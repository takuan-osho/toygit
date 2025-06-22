from pathlib import Path
from typing import Annotated

import typer

from toygit.commands.init import init_repository
from toygit.commands.add import add_files

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
    init_repository(repo_path, force=force)


@app.command()
def add(
    files: Annotated[
        list[str], typer.Argument(help="Files to add to the staging area")
    ],
):
    """Add files to the staging area."""
    add_files(files)


def main():
    """Entry point for the toygit CLI."""
    app()


if __name__ == "__main__":
    main()
