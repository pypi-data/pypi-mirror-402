# {{project_name}}

{{project_description}}

## Features

- **Comprehensive Calculation API**: Class-based and function-based interfaces for arithmetic operations
- **Rich Command Line Interface**: Multi-command CLI with subcommands and interactive mode
- **Memory Management**: State persistence between operations with history tracking
- **Batch Processing**: Process data from files with multiple operation types
- **Interactive Shell**: Interactive calculator environment for continuous operations
- **Well-tested**: Comprehensive test suite ensuring reliability

## Installation

```bash
pip install {{project_slug}}
```

## Quick Start

### Command Line

```bash
# Basic calculations
{{project_slug}} calculate add 5 3
{{project_slug}} calculate subtract 10 4
{{project_slug}} calculate sum 1 2 3 4 5

# Memory operations
{{project_slug}} memory add 5
{{project_slug}} memory show
{{project_slug}} memory subtract 2
{{project_slug}} memory reset

# Interactive shell
{{project_slug}} shell
```

### Python API

```python
from {{project_slug}}.api import add, subtract, calculate_sum, Calculator

# Basic operations
result1 = add(5, 3)        # 8
result2 = subtract(10, 4)  # 6
result3 = calculate_sum([1, 2, 3, 4, 5])  # 15

# Using the Calculator class
calc = Calculator()
calc.add(10)       # 10
calc.subtract(3)   # 7
print(calc.memory) # 7
calc.reset()       # 0
```

## Documentation

Complete documentation is available in the `docs/` directory:

- [API Reference](./docs/api/index.md)
- [CLI Guide](./docs/cli/index.md)
- [Tutorials](./docs/tutorials/index.md)

## Development

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd {{project_slug}}

# Install development dependencies
maestria env setup
```

### Testing

```bash
# Run tests
maestria test

# Run tests with coverage
maestria test --all

# Run specific tests
maestria test tests/specific_test.py
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

### Releasing

```bash
# Release a new version
maestria release
```

## Contributing

Contributions are welcome! Please see [Contributing Guidelines](./docs/development/contributing.md) for details.

## License

This project is licensed under the MIT License - see the LICENSE file for details.