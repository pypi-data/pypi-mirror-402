# Quick Start Guide

This guide will help you get started with {{project_name}} by walking through the basic functionality.

## Basic Usage

### Command Line Interface

{{project_name}} provides a command-line interface for performing calculations:

```bash
# Perform an addition
{{project_slug}} calculate add 5 3

# Perform a subtraction
{{project_slug}} calculate subtract 10 4

# Calculate a sum of multiple numbers
{{project_slug}} calculate sum 1 2 3 4 5
```

### Interactive Shell

For continuous calculations, use the interactive shell:

```bash
{{project_slug}} shell
```

In the shell, you can run commands such as:

```
>>> add 5 3
5 + 3 = 8

>>> sub 10 4
10 - 4 = 6

>>> sum 1 2 3 4 5
1 + 2 + 3 + 4 + 5 = 15

>>> m+10    # Add 10 to memory
Added 10 to memory. New value: 10

>>> m-3     # Subtract 3 from memory
Subtracted 3 from memory. New value: 7

>>> memory  # Display current memory value
Memory: 7

>>> help    # Show available commands
Available commands:
  add X Y     - Add two numbers
  sub X Y     - Subtract Y from X
  sum X Y ... - Calculate sum of numbers
  ...
```

## Using the Python API

You can also use {{project_name}} as a Python library:

```python
from {{project_slug}}.api import add, subtract, calculate_sum, Calculator

# Basic operations
result1 = add(5, 3)        # 8
result2 = subtract(10, 4)  # 6
result3 = calculate_sum([1, 2, 3, 4, 5])  # 15

# Using the Calculator class for memory operations
calc = Calculator()
calc.add(10)       # 10
calc.subtract(3)   # 7
print(calc.memory) # 7
calc.reset()       # 0
```

## Batch Processing

Process multiple numbers from a file:

```bash
# Create a JSON file with numbers
echo "[1, 2, 3, 4, 5]" > numbers.json

# Process the file, adding 10 to each number
{{project_slug}} batch process numbers.json --operation add --base 10 --output results.json

# Check the results
cat results.json
# Output: [11, 12, 13, 14, 15]
```

## Next Steps

- Explore the [complete API documentation](./api/index.md)
- Learn about [advanced CLI features](./cli/index.md)
- Check out the [tutorials](./tutorials/index.md) for example use cases