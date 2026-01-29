"""Calculator module with example functions and classes."""

from typing import List, Callable, Dict, Any, Union, Optional


def add(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    """Add two numbers together.

    Args:
        a: First number
        b: Second number

    Returns:
        The sum of a and b

    Examples:
        >>> add(1, 2)
        3
        >>> add(1.5, 2.5)
        4.0
    """
    return a + b


def subtract(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    """Subtract one number from another.

    Args:
        a: First number
        b: Second number to subtract from the first

    Returns:
        The result of a - b

    Examples:
        >>> subtract(5, 2)
        3
        >>> subtract(10.5, 2.5)
        8.0
    """
    return a - b


def calculate_sum(numbers: List[Union[int, float]]) -> Union[int, float]:
    """Calculate the sum of a list of numbers.

    Args:
        numbers: List of numbers to sum

    Returns:
        The sum of all numbers in the list

    Examples:
        >>> calculate_sum([1, 2, 3])
        6
        >>> calculate_sum([1.5, 2.5, 3.0])
        7.0
    """
    return sum(numbers)


def batch_operation(
    numbers: List[Union[int, float]],
    operation: Callable[[Union[int, float], Union[int, float]], Union[int, float]],
    base: Union[int, float] = 0,
) -> List[Union[int, float]]:
    """Apply an operation to each number in a list with a base value.

    Args:
        numbers: List of numbers to process
        operation: Function that takes two numbers and returns a result
        base: Base value to use for the operation (default: 0)

    Returns:
        List of results from applying the operation to each number with the base value

    Examples:
        >>> batch_operation([1, 2, 3], add, 10)
        [11, 12, 13]
        >>> batch_operation([1, 2, 3], subtract, 10)
        [9, 8, 7]
    """
    return [operation(base, num) for num in numbers]


class Calculator:
    """Calculator class with memory functionality.

    Attributes:
        memory: Current value stored in memory
        history: List of operations performed

    Examples:
        >>> calc = Calculator()
        >>> calc.add(5)
        5
        >>> calc.subtract(2)
        3
        >>> calc.memory
        3
        >>> calc.history
        [('add', 5, 5), ('subtract', 2, 3)]
    """

    def __init__(self, initial_value: Union[int, float] = 0):
        """Initialize the calculator with an optional initial value.

        Args:
            initial_value: Initial value to set in memory (default: 0)
        """
        self.memory: Union[int, float] = initial_value
        self.history: List[tuple] = []

    def add(self, value: Union[int, float]) -> Union[int, float]:
        """Add a value to memory.

        Args:
            value: Value to add

        Returns:
            New value in memory
        """
        self.memory = add(self.memory, value)
        self.history.append(("add", value, self.memory))
        return self.memory

    def subtract(self, value: Union[int, float]) -> Union[int, float]:
        """Subtract a value from memory.

        Args:
            value: Value to subtract

        Returns:
            New value in memory
        """
        self.memory = subtract(self.memory, value)
        self.history.append(("subtract", value, self.memory))
        return self.memory

    def reset(self) -> None:
        """Reset the calculator memory to zero."""
        self.memory = 0
        self.history.append(("reset", None, self.memory))

    def get_history(self) -> List[tuple]:
        """Get the history of operations.

        Returns:
            List of operations performed
        """
        return self.history

    def apply_batch(
        self, numbers: List[Union[int, float]], operation_name: str
    ) -> List[Union[int, float]]:
        """Apply a batch operation to a list of numbers.

        Args:
            numbers: List of numbers to process
            operation_name: Name of the operation to apply ('add' or 'subtract')

        Returns:
            List of results

        Raises:
            ValueError: If the operation name is not recognized
        """
        if operation_name == "add":
            op_func = add
        elif operation_name == "subtract":
            op_func = subtract
        else:
            raise ValueError(f"Unknown operation: {operation_name}")

        results = batch_operation(numbers, op_func, self.memory)
        self.history.append(("batch", operation_name, results))
        return results
