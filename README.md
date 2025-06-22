# ToyGit

A simple Git implementation in Python for educational purposes.

## Overview

ToyGit is a minimal implementation of Git's core functionality, designed to help understand how Git works internally. This project aims to recreate essential Git commands and operations from scratch, providing insights into version control system internals.

## Features

### Currently Implemented
- `git init` - Initialize a new Git repository
  - Creates complete `.git` directory structure (objects, refs, heads, tags)
  - Supports `--force` flag to reinitialize existing repositories
  - Proper error handling for various edge cases
  - Creates initial HEAD file pointing to main branch

### Planned Features
- Object storage and manipulation (blobs, trees, commits)
- Staging area management (`git add`)
- Commit functionality (`git commit`)
- Branch management (`git branch`, `git checkout`)
- File status tracking (`git status`)
- History viewing (`git log`)
- Additional Git commands

## Project Structure

```
toygit/
├── python/              # Python implementation
│   ├── toygit/          # Main package
│   │   ├── cli.py       # Command-line interface
│   │   ├── commands/    # Git command implementations
│   │   │   └── init.py  # git init command
│   │   └── core/        # Core Git functionality
│   ├── tests/           # Comprehensive test suite
│   └── pyproject.toml   # Python project configuration
├── LICENSE              # License file
└── README.md           # This file
```

## Getting Started

See the [Python implementation README](python/README.md) for detailed setup, installation, and usage instructions.

## Architecture

ToyGit is designed with modularity and extensibility in mind:

- **CLI Layer**: Uses Typer for robust command-line interface
- **Commands Layer**: Individual command implementations with proper error handling
- **Core Layer**: Shared functionality and Git internals
- **Testing**: Comprehensive test coverage for all features

## Development Philosophy

This project follows these principles:

- **YAGNI (You Aren't Gonna Need It)**: Implement features incrementally
- **Robust Error Handling**: Comprehensive validation and meaningful error messages
- **Test-Driven Development**: Each feature is thoroughly tested before moving to the next
- **Educational Focus**: Code is written to be readable and instructive
- **Git Compatibility**: Strives to match Git's behavior and file formats

## Contributing

This is an educational project. When contributing:

1. Ensure all new features have comprehensive tests
2. Follow the existing code style and patterns
3. Add proper error handling and validation
4. Update documentation for new features

## Learning Resources

This implementation helps understand:

- Git's internal data structures
- Object storage mechanisms
- Reference management
- Repository initialization
- Command-line tool design patterns

## License

This project is licensed under the terms specified in the LICENSE file.