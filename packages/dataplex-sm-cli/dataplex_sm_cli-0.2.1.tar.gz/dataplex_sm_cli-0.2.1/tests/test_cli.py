"""Tests for the CLI module."""

import pytest
from click.testing import CliRunner
from dataplex_sm_cli.cli import main


@pytest.fixture
def runner():
    """Provide a Click CLI runner."""
    return CliRunner()


def test_hello_command(runner):
    """Test the hello command."""
    result = runner.invoke(main, ["hello"])
    assert result.exit_code == 0
    assert "Hello, World!" in result.output


def test_hello_with_name(runner):
    """Test the hello command with a name argument."""
    result = runner.invoke(main, ["hello", "Alice"])
    assert result.exit_code == 0
    assert "Hello, Alice!" in result.output


def test_version_flag(runner):
    """Test the --version flag."""
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_model_create(runner):
    """Test the model create command."""
    result = runner.invoke(main, [
        "model", "create",
        "--name", "test-model",
        "--description", "Test model"
    ])
    assert result.exit_code == 0
    assert "Creating semantic model: test-model" in result.output
    assert "✓ Model created successfully!" in result.output


def test_model_delete_confirmed(runner):
    """Test the model delete command with confirmation."""
    result = runner.invoke(main, [
        "model", "delete",
        "--name", "test-model"
    ], input="y\n")
    assert result.exit_code == 0
    assert "Deleting semantic model: test-model" in result.output


def test_config_set(runner):
    """Test the config set command."""
    result = runner.invoke(main, [
        "config", "set",
        "--key", "project-id",
        "--value", "my-project"
    ])
    assert result.exit_code == 0
    assert "Setting project-id = my-project" in result.output
