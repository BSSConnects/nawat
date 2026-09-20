"""Entry point for the nawat CLI."""

import click
import requests

from nawat_cli import __version__


@click.group()
@click.version_option(__version__, prog_name="nawat")
def cli() -> None:
    """Nawat command-line interface."""


@cli.command()
@click.argument("url")
def ping(url: str) -> None:
    """Send a GET request to URL and print the status code."""
    response = requests.get(url, timeout=10)
    click.echo(f"{url} -> {response.status_code}")


@cli.group()
def create() -> None:
    """Create Nawat resources."""


@create.command()
@click.option("--name", required=True, help="Name of the model to create.")
def model(name: str) -> None:
    """Create a model with the given name. sdfsdf"""
    click.echo(f"Creating model: {name}")


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
