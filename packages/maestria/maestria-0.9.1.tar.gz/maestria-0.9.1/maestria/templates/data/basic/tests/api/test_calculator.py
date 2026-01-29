"""Tests for the Calculator module."""

import pytest
from typing import List, Union

from {{project_slug}}.api.calculator import (
    add, 
    subtract, 
    calculate_sum, 
    batch_operation,
    Calculator
)


class TestBasicFunctions:
    """Test the basic calculator functions."""

    def test_add(self):
        """Test the add function."""
        assert add(1, 2) == 3
        assert add(-1, 1) == 0
        assert add(0, 0) == 0
        assert add(1.5, 2.5) == 4.0

    def test_subtract(self):
        """Test the subtract function."""
        assert subtract(5, 3) == 2
        assert subtract(3, 5) == -2
        assert subtract(0, 0) == 0
        assert subtract(10.5, 2.5) == 8.0

    def test_calculate_sum(self):
        """Test the calculate_sum function."""
        assert calculate_sum([1, 2, 3]) == 6
        assert calculate_sum([]) == 0
        assert calculate_sum([-1, 1]) == 0
        assert calculate_sum([1.5, 2.5, 3.0]) == 7.0

    def test_batch_operation(self):
        """Test the batch_operation function."""
        # Test with add operation
        assert batch_operation([1, 2, 3], add, 10) == [11, 12, 13]
        
        # Test with subtract operation
        assert batch_operation([1, 2, 3], subtract, 10) == [9, 8, 7]
        
        # Test with empty list
        assert batch_operation([], add, 5) == []
        
        # Test with custom operation
        def multiply(a, b):
            return a * b
        
        assert batch_operation([1, 2, 3], multiply, 2) == [2, 4, 6]


class TestCalculatorClass:
    """Test the Calculator class."""

    def test_initialization(self):
        """Test Calculator initialization."""
        calc = Calculator()
        assert calc.memory == 0
        assert len(calc.history) == 0
        
        calc = Calculator(5)
        assert calc.memory == 5
        assert len(calc.history) == 0

    def test_add_method(self):
        """Test Calculator.add method."""
        calc = Calculator()
        result = calc.add(5)
        assert result == 5
        assert calc.memory == 5
        assert len(calc.history) == 1
        assert calc.history[0][0] == 'add'
        assert calc.history[0][1] == 5
        assert calc.history[0][2] == 5
        
        result = calc.add(3)
        assert result == 8
        assert calc.memory == 8
        assert len(calc.history) == 2

    def test_subtract_method(self):
        """Test Calculator.subtract method."""
        calc = Calculator(10)
        result = calc.subtract(3)
        assert result == 7
        assert calc.memory == 7
        assert len(calc.history) == 1
        assert calc.history[0][0] == 'subtract'
        assert calc.history[0][1] == 3
        assert calc.history[0][2] == 7
        
        result = calc.subtract(5)
        assert result == 2
        assert calc.memory == 2
        assert len(calc.history) == 2

    def test_reset_method(self):
        """Test Calculator.reset method."""
        calc = Calculator(10)
        calc.add(5)
        assert calc.memory == 15
        
        calc.reset()
        assert calc.memory == 0
        assert len(calc.history) == 2
        assert calc.history[1][0] == 'reset'

    def test_get_history_method(self):
        """Test Calculator.get_history method."""
        calc = Calculator()
        assert isinstance(calc.get_history(), list)
        assert len(calc.get_history()) == 0
        
        calc.add(5)
        calc.subtract(3)
        calc.reset()
        
        history = calc.get_history()
        assert len(history) == 3
        assert history[0][0] == 'add'
        assert history[1][0] == 'subtract'
        assert history[2][0] == 'reset'

    def test_apply_batch_method(self):
        """Test Calculator.apply_batch method."""
        calc = Calculator(10)
        
        # Test add batch
        results = calc.apply_batch([1, 2, 3], 'add')
        assert results == [11, 12, 13]
        assert len(calc.history) == 1
        assert calc.history[0][0] == 'batch'
        
        # Test subtract batch
        results = calc.apply_batch([1, 2, 3], 'subtract')
        assert results == [9, 8, 7]
        assert len(calc.history) == 2
        
        # Test invalid operation
        with pytest.raises(ValueError):
            calc.apply_batch([1, 2, 3], 'multiply')