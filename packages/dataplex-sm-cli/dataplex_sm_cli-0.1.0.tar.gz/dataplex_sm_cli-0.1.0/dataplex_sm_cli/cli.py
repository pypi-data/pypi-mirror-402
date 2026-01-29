"""Main CLI module for Dataplex Semantic Model operations."""

import click
from typing import Optional


@click.group()
@click.version_option(version="0.1.0")
def main() -> None:
    """
    Dataplex Semantic Model CLI

    A powerful command-line interface for managing Dataplex Semantic Models.
    """
    pass


@main.command()
@click.argument("name", default="World")
def hello(name: str) -> None:
    """
    Say hello to verify the CLI is working.

    Example:
        dataplex-sm hello Alice
    """
    click.echo(f"Hello, {name}!")


@main.group()
def model() -> None:
    """Commands for managing semantic models."""
    pass


@model.command()
@click.option("--name", required=True, help="Name of the semantic model")
@click.option("--description", default="", help="Description of the model")
@click.option("--project", default=None, help="GCP Project ID")
def create(name: str, description: str, project: Optional[str]) -> None:
    """
    Create a new semantic model.

    Example:
        dataplex-sm model create --name my-model --description "My model" --project my-project
    """
    click.echo(f"Creating semantic model: {name}")
    if description:
        click.echo(f"Description: {description}")
    if project:
        click.echo(f"Project: {project}")
    click.echo("✓ Model created successfully!")


@model.command()
@click.option("--name", required=True, help="Name of the semantic model")
@click.option("--project", default=None, help="GCP Project ID")
def delete(name: str, project: Optional[str]) -> None:
    """
    Delete a semantic model.

    Example:
        dataplex-sm model delete --name my-model --project my-project
    """
    if click.confirm(f"Are you sure you want to delete model '{name}'?"):
        click.echo(f"Deleting semantic model: {name}")
        if project:
            click.echo(f"Project: {project}")
        click.echo("✓ Model deleted successfully!")
    else:
        click.echo("Deletion cancelled.")


@model.command()
@click.option("--project", default=None, help="GCP Project ID")
def list(project: Optional[str]) -> None:
    """
    List all semantic models.

    Example:
        dataplex-sm model list --project my-project
    """
    click.echo("Listing semantic models...")
    if project:
        click.echo(f"Project: {project}")
    click.echo("No models found (placeholder)")


@main.group()
def config() -> None:
    """Commands for managing configuration."""
    pass


@config.command()
@click.option("--key", required=True, help="Configuration key")
@click.option("--value", required=True, help="Configuration value")
def set(key: str, value: str) -> None:
    """
    Set a configuration value.

    Example:
        dataplex-sm config set --key project-id --value my-project
    """
    click.echo(f"Setting {key} = {value}")
    click.echo("✓ Configuration saved!")


@config.command()
@click.option("--key", default=None, help="Configuration key (optional)")
def get(key: Optional[str]) -> None:
    """
    Get configuration values.

    Example:
        dataplex-sm config get --key project-id
        dataplex-sm config get  # Get all values
    """
    if key:
        click.echo(f"Getting config for key: {key}")
        click.echo(f"{key} = (value placeholder)")
    else:
        click.echo("Current configuration:")
        click.echo("project-id = (value placeholder)")


if __name__ == "__main__":
    main()
