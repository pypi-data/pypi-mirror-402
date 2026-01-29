# API Reference

{{project_name}} provides a simple and intuitive API for performing calculations and managing calculation state.

## Modules

- [Calculator Module](./calculator.md): Core calculation functionality

## Quick Reference

### Basic Operations

```python
from {{project_slug}}.api import add, subtract, calculate_sum

# Addition
result = add(5, 3)  # 8

# Subtraction
result = subtract(10, 4)  # 6

# Sum multiple numbers
result = calculate_sum([1, 2, 3, 4, 5])  # 15
```

### Batch Operations

```python
from {{project_slug}}.api import batch_operation, add, subtract

# Apply addition to each number
results = batch_operation([1, 2, 3], add, 10)  # [11, 12, 13]

# Apply subtraction to each number
results = batch_operation([1, 2, 3], subtract, 10)  # [9, 8, 7]
```

### Calculator with Memory

```python
from {{project_slug}}.api import Calculator

# Create a calculator
calc = Calculator()

# Add to memory
calc.add(5)      # 5
calc.add(3)      # 8

# Subtract from memory
calc.subtract(2) # 6

# Check memory value
print(calc.memory)  # 6

# Check operation history
print(calc.get_history())
# [('add', 5, 5), ('add', 3, 8), ('subtract', 2, 6)]

# Reset memory
calc.reset()     # 0
```

### Batch Processing with Calculator

```python
from {{project_slug}}.api import Calculator

calc = Calculator(10)  # Initialize with 10

# Apply batch addition
results = calc.apply_batch([1, 2, 3], 'add')  # [11, 12, 13]

# Apply batch subtraction
results = calc.apply_batch([1, 2, 3], 'subtract')  # [9, 8, 7]
```