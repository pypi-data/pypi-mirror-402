"""Main CLI entry point for iFlow."""

import click

from iflow import __version__
from iflow.commands.auth import login, logout, status
from iflow.commands.config import config
from iflow.commands.files import files
from iflow.commands.orders import orders
from iflow.commands.pipelines import pipelines
from iflow.commands.runs import runs


@click.group()
@click.version_option(version=__version__, prog_name="iflow")
def main():
    """
    iFlow CLI - Command-line interface for iFlow platform.

    \b
    Examples:
      iflow login                        # Authenticate with OAuth
      iflow status                       # Check login status
      iflow files ls -p ID               # List files in project
      iflow pipelines list               # List available pipelines
      iflow runs submit -p ID --pipeline SLUG -P key=value
    """
    pass


# Auth commands
main.add_command(login)
main.add_command(logout)
main.add_command(status)

# File commands
main.add_command(files)

# Config commands
main.add_command(config)

# Pipeline commands
main.add_command(pipelines)

# Run commands
main.add_command(runs)

# Order commands
main.add_command(orders)


if __name__ == "__main__":
    main()
