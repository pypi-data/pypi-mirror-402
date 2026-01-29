"""API module for {{project_name}}."""

from {{project_slug}}.api.calculator import (
    add, 
    subtract, 
    calculate_sum, 
    Calculator,
    batch_operation
)

__all__ = [
    "add", 
    "subtract", 
    "calculate_sum", 
    "Calculator",
    "batch_operation"
]