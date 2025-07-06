# ToyGit Python Implementation

This directory contains the Python implementation of ToyGit, a simple Git clone built for educational purposes.

## Requirements

- Python 3.13 or higher
- uv (recommended) or pip for package management

## Installation

### Using uv (Recommended)

```bash
# Install dependencies
uv sync

# Install in development mode
uv pip install -e .
```

### Using pip

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

## Usage

### Command Line Interface

After installation, you can use the `toygit` command:

```bash
# Initialize a new repository
toygit init [path] [--force]

# Add files to staging area
toygit add <files...>

# Show Git object information
toygit cat-file [-t|-s|-p] <object-id>
```

### Python API

You can also use ToyGit programmatically by importing the command modules from `toygit.commands`.

## Development

### Setup Development Environment

```bash
# Clone and navigate to the project
cd toygit/python

# Install with development dependencies
uv sync --group dev

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=toygit

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_init.py

# Run tests in parallel
pytest -n auto
```

### Code Quality

This project uses several tools to maintain code quality:

```bash
# Format code
ruff format

# Lint code
ruff check

# Fix linting issues automatically
ruff check --fix

# Run pre-commit on all files
pre-commit run --all-files
```

## Project Structure

```
python/
├── toygit/                 # Main package
│   ├── cli.py             # Command-line interface
│   ├── commands/          # Git command implementations
│   └── core/              # Core Git functionality
├── tests/                 # Test suite
├── pyproject.toml         # Project configuration
└── uv.lock               # Dependency lock file
```

## Architecture

### Command Pattern
Each Git command is implemented as a separate module in `toygit.commands/`, following a consistent pattern:
- Input validation and error handling
- Core logic implementation
- Integration with Git object models

### Git Object Models
Type-safe Pydantic models for Git objects (blob, tree, commit, tag) with comprehensive validation and parsing.

### CLI Integration
Uses Typer for command-line interface with automatic help generation and type validation.

### Testing Strategy

- **Unit Tests**: Each command and component is thoroughly tested
- **Modular Test Organization**: Separate test files for each major component
- **Edge Cases**: Comprehensive coverage of error conditions and validation
- **Integration Tests**: Full command-line interface testing
- **Property-Based Testing**: Using pytest-randomly for additional test coverage

## Configuration

The project uses modern Python tooling:

- **Ruff**: Fast Python linter and formatter
- **Pytest**: Testing framework with plugins for coverage and parallel execution
- **Pre-commit**: Git hook management for code quality
- **Typer**: CLI framework with automatic help generation
- **Pydantic**: Type-safe data models with validation

## Troubleshooting

### Common Issues

1. **Permission Denied**: Ensure you have write permissions to the target directory
2. **Python Version**: Requires Python 3.13+
3. **Missing Dependencies**: Run `uv sync` to install all dependencies

### Development Issues

1. **Pre-commit Failures**: Run `pre-commit run --all-files` to fix issues
2. **Test Failures**: Check that you're in the correct environment with `python --version`
3. **Import Errors**: Ensure the package is installed with `uv pip install -e .`

## Contributing

When contributing to the Python implementation:

1. **Follow PEP 8**: Code style is enforced by Ruff
2. **Write Tests**: All new features must have tests
3. **Update Documentation**: Keep docstrings and README current
4. **Type Hints**: Use type annotations for better code clarity
5. **Error Handling**: Include comprehensive error checking

## Current Features

The Python implementation currently supports:

✅ **Repository Initialization** (`init`)
- Creates `.git` directory structure
- Supports force re-initialization

✅ **File Staging** (`add`)
- Adds files and directories to staging area
- Updates index file

✅ **Object Inspection** (`cat-file`)
- Shows object type, size, and content
- Supports abbreviated hash resolution

✅ **Git Object Models**
- Type-safe Pydantic models for all Git objects
- Support for blob, tree, commit, and tag objects

## Future Enhancements

Planned additions:

- Commit creation and history
- Branch operations
- File status tracking (`status`)
- Diff functionality
- Merge operations
- Remote repository support

Each new feature follows established patterns:
- Dedicated module in `commands/`
- Comprehensive error handling
- Full test coverage
- Type annotations with Pydantic models
- CLI integration through Typer
