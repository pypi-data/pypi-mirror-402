# Calculator Module

The Calculator module provides functions and classes for performing basic arithmetic operations and managing calculation state.

## Functions

### `add(a, b)`

Add two numbers together.

**Parameters:**
- `a` (int, float): First number
- `b` (int, float): Second number

**Returns:**
- (int, float): The sum of `a` and `b`

**Example:**
```python
from {{project_slug}}.api import add

result = add(5, 3)  # 8
result = add(1.5, 2.5)  # 4.0
```

### `subtract(a, b)`

Subtract one number from another.

**Parameters:**
- `a` (int, float): First number
- `b` (int, float): Second number to subtract from the first

**Returns:**
- (int, float): The result of `a - b`

**Example:**
```python
from {{project_slug}}.api import subtract

result = subtract(10, 4)  # 6
result = subtract(5.5, 2.5)  # 3.0
```

### `calculate_sum(numbers)`

Calculate the sum of a list of numbers.

**Parameters:**
- `numbers` (list[int, float]): List of numbers to sum

**Returns:**
- (int, float): The sum of all numbers in the list

**Example:**
```python
from {{project_slug}}.api import calculate_sum

result = calculate_sum([1, 2, 3, 4, 5])  # 15
result = calculate_sum([1.5, 2.5, 3.0])  # 7.0
```

### `batch_operation(numbers, operation, base=0)`

Apply an operation to each number in a list with a base value.

**Parameters:**
- `numbers` (list[int, float]): List of numbers to process
- `operation` (callable): Function that takes two numbers and returns a result
- `base` (int, float, optional): Base value to use for the operation. Default is 0

**Returns:**
- list[int, float]: List of results from applying the operation to each number with the base value

**Example:**
```python
from {{project_slug}}.api import batch_operation, add, subtract

# Add 10 to each number
results = batch_operation([1, 2, 3], add, 10)  # [11, 12, 13]

# Subtract each number from 10
results = batch_operation([1, 2, 3], subtract, 10)  # [9, 8, 7]

# Custom operation
def multiply(a, b):
    return a * b

results = batch_operation([1, 2, 3], multiply, 5)  # [5, 10, 15]
```

## Classes

### `Calculator`

Calculator class with memory functionality.

#### Methods

##### `__init__(initial_value=0)`

Initialize the calculator with an optional initial value.

**Parameters:**
- `initial_value` (int, float, optional): Initial value to set in memory. Default is 0

**Example:**
```python
from {{project_slug}}.api import Calculator

# Create a calculator with default initial memory (0)
calc1 = Calculator()

# Create a calculator with initial memory value of 10
calc2 = Calculator(10)
```

##### `add(value)`

Add a value to memory.

**Parameters:**
- `value` (int, float): Value to add

**Returns:**
- (int, float): New value in memory

**Example:**
```python
calc = Calculator(5)
result = calc.add(3)  # 8
```

##### `subtract(value)`

Subtract a value from memory.

**Parameters:**
- `value` (int, float): Value to subtract

**Returns:**
- (int, float): New value in memory

**Example:**
```python
calc = Calculator(10)
result = calc.subtract(4)  # 6
```

##### `reset()`

Reset the calculator memory to zero.

**Example:**
```python
calc = Calculator(5)
calc.reset()  # Memory is now 0
```

##### `get_history()`

Get the history of operations.

**Returns:**
- list[tuple]: List of operations performed, where each operation is a tuple of (operation_name, value, result)

**Example:**
```python
calc = Calculator()
calc.add(5)
calc.subtract(2)
calc.reset()

history = calc.get_history()
# [('add', 5, 5), ('subtract', 2, 3), ('reset', None, 0)]
```

##### `apply_batch(numbers, operation_name)`

Apply a batch operation to a list of numbers.

**Parameters:**
- `numbers` (list[int, float]): List of numbers to process
- `operation_name` (str): Name of the operation to apply ('add' or 'subtract')

**Returns:**
- list[int, float]: List of results

**Raises:**
- ValueError: If the operation name is not recognized

**Example:**
```python
calc = Calculator(10)

# Batch addition
results = calc.apply_batch([1, 2, 3], 'add')  # [11, 12, 13]

# Batch subtraction
results = calc.apply_batch([1, 2, 3], 'subtract')  # [9, 8, 7]
```