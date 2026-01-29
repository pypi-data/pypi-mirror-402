"""Main CLI module for Dataplex Semantic Model operations."""

import click
import json
import subprocess
import os
from typing import Optional
from pathlib import Path


@click.group()
@click.version_option(version="0.2.1")
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


@main.command()
@click.argument("file_path", type=click.Path(exists=True))
def validate_yaml(file_path: str) -> None:
    """
    Validate a YAML file using js-yaml (npm package).

    Example:
        dataplex-sm validate-yaml config.yaml
        dataplex-sm validate-yaml path/to/file.yaml
    """
    try:
        # Get the directory where this script is located
        script_dir = Path(__file__).parent
        validator_script = script_dir / "validator.js"

        # Run the Node.js validator
        result = subprocess.run(
            ["node", str(validator_script), file_path],
            capture_output=True,
            text=True,
        )

        # Parse the JSON output from the validator
        output_str = result.stdout if result.stdout else result.stderr
        
        try:
            output = json.loads(output_str)
        except json.JSONDecodeError:
            click.echo(click.style("✗ Validation error (invalid response)", fg="red"))
            click.echo(f"Response: {output_str}")
            raise click.ClickException("YAML validation failed")

        if output.get("success"):
            click.echo(click.style("✓ YAML is valid!", fg="green", bold=True))
            click.echo(f"File: {file_path}")
        else:
            error_msg = output.get("error", "Unknown error")
            click.echo(click.style("✗ YAML validation failed!", fg="red", bold=True))
            click.echo(f"Error: {error_msg}")
            if output.get("line") is not None:
                click.echo(f"Line: {output.get('line')}, Column: {output.get('column')}")
            raise click.ClickException("YAML validation failed")

    except FileNotFoundError:
        click.echo(
            click.style(
                "✗ Node.js is not installed or validator.js not found", fg="red"
            )
        )
        click.echo("\nTo use YAML validation, install Node.js:")
        click.echo("  Linux/Mac:   curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -")
        click.echo("               sudo apt-get install -y nodejs")
        click.echo("  Mac (Brew):  brew install node")
        click.echo("  Windows:     Download from https://nodejs.org/")
        click.echo("\nThen run: npm install")
        raise click.ClickException("Node.js not found")
    except click.ClickException:
        raise
    except Exception as e:
        click.echo(click.style(f"✗ Error: {str(e)}", fg="red"))
        raise click.ClickException(str(e))


if __name__ == "__main__":
    main()
