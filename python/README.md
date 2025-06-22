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
# Initialize a new repository in current directory
toygit init

# Initialize a new repository in specific directory
toygit init /path/to/directory

# Force reinitialize existing repository
toygit init --force
```

### Python API

You can also use ToyGit programmatically:

```python
from pathlib import Path
from toygit.commands.init import init_repository

# Initialize repository
repo_path = Path("/path/to/repo")
init_repository(repo_path)

# With force flag
init_repository(repo_path, force=True)
```

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
│   ├── __init__.py
│   ├── cli.py             # Command-line interface using Typer
│   ├── commands/          # Git command implementations
│   │   ├── __init__.py
│   │   └── init.py        # git init command
│   └── core/              # Core Git functionality
│       └── __init__.py
├── tests/                 # Test suite
│   └── test_init.py       # Tests for git init
├── pyproject.toml         # Project configuration
└── uv.lock               # Dependency lock file
```

## Implementation Details

### Git Init Command

The `git init` command creates a standard Git repository structure:

```
.git/
├── objects/              # Object database
├── refs/                # References
│   ├── heads/           # Branch references
│   └── tags/            # Tag references
└── HEAD                 # Current branch pointer
```

### Error Handling

The implementation includes comprehensive error handling for:

- Non-existent target directories
- Permission errors
- Existing repositories (without `--force`)
- Invalid paths

### Testing Strategy

- **Unit Tests**: Each command is thoroughly tested
- **Edge Cases**: Comprehensive coverage of error conditions
- **Integration Tests**: Full command-line interface testing
- **Property-Based Testing**: Using pytest-randomly for additional test coverage

## Configuration

### pyproject.toml

Key configuration sections:

- **Dependencies**: Minimal runtime dependencies (only Typer)
- **Development Dependencies**: Comprehensive dev tools
- **Scripts**: Command-line entry points
- **Build System**: Uses Hatchling for packaging

### Development Tools

- **Ruff**: Fast Python linter and formatter
- **Pytest**: Testing framework with plugins
- **Pre-commit**: Git hook management
- **pytest-cov**: Coverage reporting
- **pytest-xdist**: Parallel test execution

## Troubleshooting

### Common Issues

1. **Permission Denied**: Ensure you have write permissions to the target directory
2. **Python Version**: Requires Python 3.13+
3. **Missing Dependencies**: Run `uv sync` to install all dependencies

### Development Issues

1. **Pre-commit Failures**: Run `pre-commit run --all-files` to fix issues
2. **Test Failures**: Check that you're in the correct environment with `python --version`
3. **Import Errors**: Ensure the package is installed with `pip install -e .`

## Contributing

When contributing to the Python implementation:

1. **Follow PEP 8**: Code style is enforced by Ruff
2. **Write Tests**: All new features must have tests
3. **Update Documentation**: Keep docstrings and README current
4. **Type Hints**: Use type annotations for better code clarity
5. **Error Handling**: Include comprehensive error checking

## Future Enhancements

The Python implementation is designed to be extensible. Planned additions:

- Object storage (blobs, trees, commits)
- Index/staging area management
- Commit creation and history
- Branch operations
- File status tracking
- Repository introspection tools

Each new feature will follow the same patterns established in the `init` command:
- Dedicated module in `commands/`
- Comprehensive error handling
- Full test coverage
- Type annotations
- CLI integration through Typer