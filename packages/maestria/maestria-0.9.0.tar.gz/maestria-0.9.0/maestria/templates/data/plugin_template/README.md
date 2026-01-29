# {{plugin_name}}

A Maestria plugin that provides additional functionality for Python projects.

## Features

- **Custom Commands**: Additional commands for Maestria
- **Project Analysis**: Analyze Python projects to gain insights about the codebase
- **Integration Hooks**: Integrate with Maestria's command lifecycle
- **Project Templates**: Example templates for projects that use this plugin

## Installation

```bash
pip install {{plugin_name}}
```

## Usage

Once installed, the plugin will be automatically available in Maestria:

```bash
# Say hello
maestria {{plugin_name_short}} hello World

# Say hello with formal greeting
maestria {{plugin_name_short}} hello World --formal

# Analyze a Python project
maestria {{plugin_name_short}} analyze /path/to/project

# Save analysis to a file
maestria {{plugin_name_short}} analyze /path/to/project --output analysis.json
```

## Development

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd {{plugin_name}}

# Install development dependencies
maestria env setup
```

### Testing

```bash
# Run tests
maestria test

# Run tests with coverage
maestria test --all
```

### Linting

```bash
# Run linting
maestria lint

# Check linting without making changes
maestria lint --check
```

### Building

```bash
# Build the package
maestria build
```

## Plugin Structure

```
{{package_name}}/
├── __init__.py            # Package initialization
├── plugin.py              # Main plugin implementation
├── commands/              # CLI commands
│   ├── __init__.py
│   ├── main.py            # Main command group
│   ├── hello.py           # Hello command
│   └── analyze.py         # Analyze command
├── hooks/                 # Command lifecycle hooks
│   └── __init__.py
├── templates/             # Project templates
│   └── data/              # Template data
│       └── example/       # Example template
└── utils/                 # Utility functions
    ├── __init__.py
    ├── formatting.py      # String formatting utilities
    └── analysis.py        # Project analysis utilities
```

## Creating a Project from the Plugin Template

```bash
maestria init my-plugin --template plugin_template
cd my-plugin
maestria env setup
```

## Contributing

Contributions are welcome! Please see the [Contributing Guidelines](./docs/development/contributing.md) for details.

## License

This project is licensed under the MIT License - see the LICENSE file for details.