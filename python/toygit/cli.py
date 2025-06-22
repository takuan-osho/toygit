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
):
    """Initialize a new Git repository."""
    repo_path = Path(path).resolve()

    try:
        init_repository(repo_path)
        typer.echo(f"Initialized empty Git repository in {repo_path / '.git'}")
    except FileNotFoundError:
        typer.echo(f"Error: Directory {repo_path} does not exist", err=True)
        raise typer.Exit(1)
    except PermissionError:
        typer.echo(f"Error: Permission denied for {repo_path}", err=True)
        raise typer.Exit(1)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Unexpected error: {e}", err=True)
        raise


def main():
    """Entry point for the toygit CLI."""
    app()


if __name__ == "__main__":
    main()
