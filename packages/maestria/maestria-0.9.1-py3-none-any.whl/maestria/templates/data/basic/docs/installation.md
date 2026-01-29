# Installation

## Requirements

- Python {{python_version}} or higher
- pip package manager

## Basic Installation

To install {{project_name}}, run:

```bash
pip install {{project_slug}}
```

## Development Installation

If you want to develop or contribute to {{project_name}}, follow these steps:

```bash
# Clone the repository
git clone <repository-url>
cd {{project_slug}}

# Set up the development environment
maestria env setup

# Or, if you don't have maestria:
pip install --editable ".[dev]"
```

## Verification

To verify that the installation was successful, run:

```bash
{{project_slug}} --version
```

You should see the current version of {{project_name}} displayed.

## Next Steps

Once you have {{project_name}} installed, you can:

- Follow the [Quick Start](./quickstart.md) guide
- Explore the [API documentation](./api/index.md)
- Learn about the [command-line interface](./cli/index.md)