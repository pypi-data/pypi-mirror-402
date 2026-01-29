"""Simple Python Utilities Package.

A minimalist Python library providing basic utility functions
for common operations like printing messages and arithmetic.

Author: fjmpereira20
Version: 1.7.0
"""

from .core import (
    add_numbers,
    divide_numbers,
    format_currency,
    is_even,
    max_numbers,
    min_numbers,
    multiply_numbers,
    multiply_three_numbers,
    print_message,
    square_numbers,
)

__version__ = "1.7.0"
__author__ = "fjmpereira20"
__email__ = "fjmpereira20@users.noreply.github.com"

__all__ = [
    "print_message",
    "add_numbers",
    "multiply_numbers",
    "multiply_three_numbers",
    "divide_numbers",
    "square_numbers",
    "max_numbers",
    "min_numbers",
    "is_even",
    "format_currency",
]
