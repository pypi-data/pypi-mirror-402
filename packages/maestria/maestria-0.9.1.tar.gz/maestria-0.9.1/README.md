# Maestria

**Maven for Python** - Team-oriented Python project management tool built on UV

[![PyPI version](https://badge.fury.io/py/maestria.svg)](https://pypi.org/project/maestria/)
[![Python Version](https://img.shields.io/pypi/pyversions/maestria.svg)](https://pypi.org/project/maestria/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/ebay/maestria.svg?style=social&label=Star)](https://github.com/ebay/maestria)
[![GitHub issues](https://img.shields.io/github/issues/ebay/maestria.svg)](https://github.com/ebay/maestria/issues)
[![GitHub forks](https://img.shields.io/github/forks/ebay/maestria.svg)](https://github.com/ebay/maestria/network)

> **What's in a name?** *Maestria* (Spanish/Italian for "mastery") brings Maven's proven build tool expertise from the Java world to Python. Just as Maven revolutionized Java project management, Maestria aims to bring that same level of sophistication and simplicity to Python development.

## Why Maestria?

Maestria brings Maven's proven build philosophy to Python, combining UV's blazing speed with enterprise-ready team features. See our [Why Maestria?](./docs/why-maestria.md) guide to understand how Maestria compares to other tools and what makes it unique.

**Key differentiators:**
- **Zero-setup enterprise integration** - Automatic pip.conf parsing for internal repositories
- **Multi-tier template system** - Share and enforce organizational standards
- **Plugin architecture** - Extend with custom workflows and lifecycle hooks
- **Team-first design** - Built for collaboration, not just individual developers
- **UV-powered performance** - 10-100x faster than traditional tools

Existing Python tools (Poetry, PDM, Hatch) target **individual developers**. Maestria is designed for **teams and enterprises** that need:

- **Multi-tier template registry** - Share organizational templates (local, git, organizational)
- **Team standardization** - Enforce security policies, testing standards, CI/CD patterns
- **Zero-setup workflows** - New developers productive in minutes, not days
- **Plugin architecture** - Extensible system with error isolation
- **Enterprise-ready** - Works with Artifactory, Nexus, and internal PyPI repositories
- **UV-powered** - Blazing-fast dependency resolution and environment management

Built on top of **UV** (Ultraviolet) for performance, Maestria combines Maven's time-tested philosophy with Python's modern tooling ecosystem.

> **Origin**: Maestria originated at eBay as the successor to the internal eBay Python Build Tool (PBT), refined through production use before being open-sourced to benefit the broader Python community.

## Quick Start

### Installation

```bash
pip install maestria
```

### Create Your First Project

```bash
# Initialize a new Python project
maestria init my-project --template=basic

# Set up development environment
cd my-project
maestria env setup

# Run tests
maestria test

# Build package
maestria build
```

## Documentation

- [Quickstart Guide](docs/quickstart-guide.md) - Get up and running quickly
- [Development Guide](docs/development-guide.md) - Contributing to Maestria
- [Publishing Guide](docs/publishing-guide.md) - Publishing your projects
- [Zero-Setup Workflow](docs/zero-setup-workflow.md) - Complete workflow guide
- [Feature Guide](docs/feature-guide.md) - All features explained

## Plugin Ecosystem

Maestria supports a plugin system for extending functionality. Official plugins include:

- **maestria-zensical-plugin** (coming soon) - Modern, fast documentation generation and GitHub Pages deployment

Community plugins and contributions are welcome! See our [Plugin Development Guide](docs/feature-guide.md#creating-plugins) to create your own.

## Design Philosophy

Maestria is designed as a lightweight layer on top of industry-standard tools to provide:

1. **Zero-setup experience** for common Python project tasks
2. **Team-oriented features** like shared templates and standards
3. **Unified interface** across different projects
4. **Plugin extensibility** for custom workflows
5. **Modern defaults** leveraging the best practices from the Python ecosystem

## Testing

Maestria maintains high test coverage standards to ensure reliability:

```bash
# Run all tests with coverage
python -m pytest --cov=maestria --cov-report=term tests/

# View detailed coverage with missing lines
python -m pytest --cov=maestria --cov-report=term-missing tests/

# Generate HTML coverage report
python -m pytest --cov=maestria --cov-report=html tests/
```

**Current Coverage**: >90%
- See [Development Guide](docs/development-guide.md) for more testing details

## Documentation

For comprehensive documentation, please visit our [documentation site](docs/index.md).

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:
- Setting up your development environment
- Code style and testing requirements
- Submitting pull requests

## License

Maestria is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

Copyright (c) 2024-2025 eBay Inc.