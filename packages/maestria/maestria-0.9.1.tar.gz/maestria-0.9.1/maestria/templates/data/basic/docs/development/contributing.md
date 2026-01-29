# Contributing to {{project_name}}

Thank you for your interest in contributing to {{project_name}}! This document provides guidelines and instructions for contributing.

## Development Setup

1. Fork the repository on GitHub.
2. Clone your fork locally:
   ```bash
   git clone <your-fork-url>
   cd {{project_slug}}
   ```

3. Set up the development environment:
   ```bash
   maestria env setup
   ```

4. Create a branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### Running Tests

Run the tests to make sure everything is working correctly:

```bash
maestria test
```

For test coverage:

```bash
maestria test --all
```

### Code Style

We use [Black](https://github.com/psf/black) for code formatting, [mypy](https://github.com/python/mypy) for type checking, and [ruff](https://github.com/charliermarsh/ruff) for linting.

Format and lint your code before submitting:

```bash
maestria lint
```

Check code style without making changes:

```bash
maestria lint --check
```

### Building the Package

To build the package:

```bash
maestria build
```

## Pull Request Process

1. Update the documentation with details of changes to the interface, if applicable.
2. Update the README.md with details of changes, if applicable.
3. The version number will be updated by the maintainers during the release process.
4. Submit a pull request to the original repository.

## Coding Standards

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines.
- Write docstrings for all functions, classes, and methods.
- Add type hints to all function parameters and return values.
- Include unit tests for all new functionality.
- Document API changes in the appropriate documentation files.

## Commit Messages

Please use clear and descriptive commit messages with the following format:

```
<type>: <description>

[optional body]

[optional footer]
```

Types include:
- feat: A new feature
- fix: A bug fix
- docs: Documentation only changes
- style: Changes that do not affect the meaning of the code (formatting, etc)
- refactor: Code change that neither fixes a bug nor adds a feature
- test: Adding or modifying tests
- chore: Changes to the build process or auxiliary tools

## License

By contributing, you agree that your contributions will be licensed under the project's license.

## Questions?

If you have any questions, please feel free to open an issue or contact the maintainers directly.