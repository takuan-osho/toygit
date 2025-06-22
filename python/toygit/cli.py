from pathlib import Path
from typing import Annotated

import typer

from toygit.commands.init import init_repository

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


def main():
    """Entry point for the toygit CLI."""
    app()


if __name__ == "__main__":
    main()
