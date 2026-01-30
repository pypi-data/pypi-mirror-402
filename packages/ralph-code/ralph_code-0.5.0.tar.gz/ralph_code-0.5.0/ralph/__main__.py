"""Entry point for `python -m ralph`."""

import sys
from pathlib import Path

import click

from .app import main


@click.command()
@click.option(
    "--debug",
    is_flag=True,
    help="Enable verbose logging of all Claude interactions to .ralph/logs/",
)
@click.argument(
    "directory",
    required=False,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
def cli(debug: bool, directory: Path | None) -> None:
    """
    Ralph Coding - Automated task implementation with Claude Code.

    DIRECTORY is the optional target project directory.
    Defaults to the current working directory.
    """
    project_dir = directory or Path.cwd()
    main(project_dir=project_dir, debug=debug)


if __name__ == "__main__":
    cli()
