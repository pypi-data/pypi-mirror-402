# dataplex-sm-cli

A powerful and extensible CLI tool for managing Dataplex Semantic Models. This CLI can be installed in any Python project via pip.

## Features

- 🚀 Easy installation via pip
- 🎯 Semantic model management (create, delete, list)
- ⚙️ Configuration management
- 🔧 Extensible command structure
- 📝 Well-documented commands with examples

## Installation

### From Source (Development)

```bash
# Clone the repository
git clone https://github.com/Sachin-Rungta/dataplex-sm-cli.git
cd dataplex-sm-cli

# Install in development mode
pip install -e .
```

### From PyPI (Once Published)

```bash
pip install dataplex-sm-cli
```

### In Any Project

Once installed, you can use the CLI from any directory:

```bash
pip install dataplex-sm-cli
dataplex-sm --help
```

## Usage

### Get Help

```bash
dataplex-sm --help
dataplex-sm --version
```

### Model Commands

#### Create a semantic model
```bash
dataplex-sm model create --name my-model --description "My model" --project my-project
```

#### List all models
```bash
dataplex-sm model list --project my-project
```

#### Delete a model
```bash
dataplex-sm model delete --name my-model --project my-project
```

### Configuration Commands

#### Set a configuration value
```bash
dataplex-sm config set --key project-id --value my-project
```

#### Get configuration
```bash
dataplex-sm config get --key project-id
dataplex-sm config get  # Get all values
```

## Development

### Setup Development Environment

```bash
# Install with dev dependencies
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest tests/
pytest tests/ --cov=dataplex_sm_cli  # With coverage
```

### Code Quality

```bash
# Format code
black dataplex_sm_cli/ tests/

# Lint
flake8 dataplex_sm_cli/ tests/

# Type checking
mypy dataplex_sm_cli/
```

## Project Structure

```
dataplex-sm-cli/
├── dataplex_sm_cli/
│   ├── __init__.py          # Package initialization
│   └── cli.py               # Main CLI implementation
├── tests/
│   ├── __init__.py
│   └── test_cli.py          # CLI tests
├── pyproject.toml           # Modern Python project config
├── setup.py                 # Setup script for pip
├── README.md                # This file
└── .gitignore               # Git ignore rules
```

## Adding New Commands

To add new commands to the CLI, edit `dataplex_sm_cli/cli.py`:

```python
@main.command()
@click.option("--option", help="Option help text")
def my_command(option):
    """Command help text."""
    click.echo(f"Executing my-command with option: {option}")
```

Then add tests in `tests/test_cli.py`:

```python
def test_my_command(runner):
    result = runner.invoke(main, ["my-command", "--option", "value"])
    assert result.exit_code == 0
    assert "expected output" in result.output
```

## Publishing to PyPI

```bash
# Build the package
pip install build
python -m build

# Upload to PyPI (requires credentials)
pip install twine
twine upload dist/*
```

## Requirements

- Python 3.8+
- click >= 8.0.0

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a pull request.
